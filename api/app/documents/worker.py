"""Bulk document generation worker (design section 8.2).

Certificates for 800 attendees is 3,200 Google API calls - it cannot run
inside a request. Following the outbox pattern already in the codebase
(app/outbox/sender.py): a bulk request pre-creates one `pending`
GeneratedDocument row per recipient (app/documents/api.py's
DocumentTemplateGenerateAPI), and the worker behind
/api/v1/tasks/document-generation, driven every minute by App Engine cron
(api/cron.yaml), claims a batch with an exclusive UPDATE and processes it
within a time budget. A backlog drains over several runs.
"""
import time
import uuid
from datetime import datetime, timedelta

from app import db, LOGGER
from app.documents.models import (
    GeneratedDocument, GeneratedDocumentStatus, DocumentGenerationJob,
)
from app.documents.generator import _process_row, GenerationError
from app.documents.google_client import build_default_client
from app.events.models import Event
from app.documents.models import DocumentTemplate
from app.users.models import AppUser
from config import GCP_DOCS_WORKING_FOLDER_ID, DOCUMENT_WORKER_BATCH_SIZE, DOCUMENT_WORKER_TIME_BUDGET_SECONDS

#: How long a claimed row may sit in `generating` before it's assumed the
#: worker holding it died. Comfortably longer than one worker run.
STALE_CLAIM_SECONDS = 600


def claim_batch(limit, now=None):
    """Take exclusive ownership of up to `limit` due bulk-generation rows.

    Only rows with a job_id are claimable here - a synchronous single
    generation (generator.generate_document) never leaves a row `pending`,
    so this can't collide with it. The `status == 'pending'` predicate on the
    UPDATE is what makes the claim exclusive, same reasoning as
    OutboxRepository.claim_batch: portable to SQLite (no SELECT ... FOR
    UPDATE SKIP LOCKED), safe under concurrent workers because only one
    UPDATE can move a given row out of `pending`.
    """
    now = now or datetime.utcnow()
    token = str(uuid.uuid4())

    candidate_ids = [row[0] for row in (
        db.session.query(GeneratedDocument.id)
        .filter(GeneratedDocument.status == GeneratedDocumentStatus.PENDING,
                GeneratedDocument.job_id.isnot(None))
        .order_by(GeneratedDocument.id)
        .limit(limit)
        .all())]
    if not candidate_ids:
        return []

    (db.session.query(GeneratedDocument)
     .filter(GeneratedDocument.id.in_(candidate_ids),
             GeneratedDocument.status == GeneratedDocumentStatus.PENDING)
     .update({'status': GeneratedDocumentStatus.GENERATING, 'claimed_at': now, 'claim_token': token},
             synchronize_session=False))
    db.session.commit()

    return (db.session.query(GeneratedDocument)
            .filter(GeneratedDocument.claim_token == token)
            .order_by(GeneratedDocument.id)
            .all())


def release(rows):
    """Return claimed-but-unattempted rows to the pending pool - the worker
    ran out of its time budget, not a generation failure, so no attempt is
    charged."""
    for row in rows:
        row.status = GeneratedDocumentStatus.PENDING
        row.claim_token = None
        row.claimed_at = None
    db.session.commit()
    return len(rows)


def requeue_stale(stale_before=None):
    """Recover rows whose worker died mid-attempt, charging an attempt even
    though the outcome is unknown - same reasoning as
    OutboxRepository.requeue_stale, so a row that reliably kills its worker
    lands in `failed` instead of cycling forever."""
    stale_before = stale_before or (datetime.utcnow() - timedelta(seconds=STALE_CLAIM_SECONDS))
    stale = (db.session.query(GeneratedDocument)
             .filter(GeneratedDocument.status == GeneratedDocumentStatus.GENERATING,
                     GeneratedDocument.job_id.isnot(None),
                     GeneratedDocument.claimed_at < stale_before)
             .all())
    for row in stale:
        row.mark_failed(
            'ABANDONED', 'The worker holding this document reported no outcome.', retryable=True)
        _record_if_terminal(row)
    if stale:
        db.session.commit()
    return len(stale)


def _record_if_terminal(row):
    """Updates the owning job's counters once (and only once) a row reaches
    a terminal state. A row bounced back to `pending` for a retry hasn't
    resolved yet, so the job must not count it - see
    DocumentGenerationJob.record_outcome."""
    if row.job_id and row.status in (GeneratedDocumentStatus.GENERATED, GeneratedDocumentStatus.FAILED):
        job = db.session.query(DocumentGenerationJob).filter_by(id=row.job_id).first()
        if job:
            job.record_outcome(succeeded=row.status == GeneratedDocumentStatus.GENERATED)


def _process_one(row, client):
    document_template = db.session.query(DocumentTemplate).filter_by(id=row.document_template_id).first()
    user = db.session.query(AppUser).filter_by(id=row.user_id).first()
    event = db.session.query(Event).filter_by(id=row.event_id).first()

    if not document_template or not user or not event:
        # The recipient, template or event was deleted after the job was
        # created - not retryable, nothing will change that.
        row.mark_failed(
            'RECIPIENT_OR_TEMPLATE_DELETED',
            'The template, recipient or event no longer exists.', retryable=False)
        db.session.commit()
        _record_if_terminal(row)
        db.session.commit()
        return 'failed'

    job = db.session.query(DocumentGenerationJob).filter_by(id=row.job_id).first() if row.job_id else None
    override_eligibility = bool(job and job.override_eligibility)

    try:
        _process_row(row, document_template, user, event, row.language,
                     client=client, override_eligibility=override_eligibility, retryable=True)
    except GenerationError as e:
        LOGGER.info('Bulk generation failed for document %s: %s (%s)', row.id, e.code, e.message)
        _record_if_terminal(row)
        db.session.commit()
        return 'failed'

    _record_if_terminal(row)
    db.session.commit()
    return 'generated'


def run_bulk_generation(batch_size=None, time_budget_seconds=None):
    """Claim and process a batch of pending bulk-generation rows.

    Returns a summary dict of what happened. Processing stops when the batch
    is exhausted or the time budget expires, whichever comes first; anything
    released is retried on the next run.
    """
    batch_size = batch_size or DOCUMENT_WORKER_BATCH_SIZE
    time_budget_seconds = (DOCUMENT_WORKER_TIME_BUDGET_SECONDS if time_budget_seconds is None
                           else time_budget_seconds)

    started_at = time.monotonic()
    summary = {'recovered': requeue_stale(),
               'claimed': 0, 'generated': 0, 'failed': 0, 'released': 0}

    rows = claim_batch(batch_size)
    summary['claimed'] = len(rows)
    if not rows:
        return summary

    client = build_default_client(working_folder_id=GCP_DOCS_WORKING_FOLDER_ID)

    for index, row in enumerate(rows):
        if time.monotonic() - started_at > time_budget_seconds:
            remaining = rows[index:]
            summary['released'] = release(remaining)
            LOGGER.info('Document worker time budget reached, released %s rows', len(remaining))
            break

        summary[_process_one(row, client)] += 1

    return summary
