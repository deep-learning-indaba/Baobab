from datetime import datetime
from unittest import mock

from sqlalchemy import inspect as sa_inspect

from app import db
from app.utils.testing import ApiTestCase
from app.forms.models import (
    Form, FormTranslation, FormSection, FormQuestion, FormQuestionTranslation,
    FormResponse, FormAnswer,
)
from app.documents.models import (
    DocumentTemplate, DocumentTemplateTranslation, DocumentTemplateVariant,
    DocumentTemplateForm, DocumentTemplateFormTranslation, UserEventData,
)
from app.tags.models import Tag, TagTranslation, TagType
from app.offer.models import Offer, OfferTag
from app.invitedGuest.models import InvitedGuest, InvitedGuestTag
from app.attendance.models import Attendance


def _pk(obj):
    """The primary key of `obj`, safe to call even once it has become a
    detached SQLAlchemy instance.

    A request made through the Flask test client (self.app.post/.get/...)
    tears down db.session at the end of the request, which detaches every
    object that was loaded through it - including self.user/self.event
    created back in setUp. SQLAlchemy's default expire_on_commit then means
    even `.id` needs a fresh SELECT to re-read, which a detached instance has
    no session left to run, raising DetachedInstanceError.

    The object's identity key, in contrast, is cached on its instance state
    independently of session attachment, so reading it needs no session and
    never raises. This is the same hazard the forms test suite works around
    by capturing plain ids immediately after creation; the identity-key
    lookup does the equivalent without every factory method having to be
    called before the test's first HTTP request.
    """
    try:
        return obj.id
    except Exception:
        identity = sa_inspect(obj).identity
        return identity[0] if identity else None


class DocumentsTestCase(ApiTestCase):
    """Shared factory helpers for the document generation test suite."""

    def setUp(self):
        super().setUp()
        self.user = self.add_user('user@example.com', 'Amina', 'Diallo')
        self.admin = self.add_user('admin@example.com', 'Admin', 'User', is_admin=True)
        self.event = self.add_event()
        self.user_id = self.user.id
        self.admin_id = self.admin.id
        self.event_id = self.event.id
        self.user_email = self.user.email
        self.admin_email = self.admin.email
        self.user_firstname = self.user.firstname
        self.user_lastname = self.user.lastname
        self.mock_bucket = self._mock_storage()

    def _mock_storage(self):
        """Replaces app.utils.storage.get_storage_bucket with a mock bucket,
        following the same pattern app/files/tests.py already uses.

        Both generator.py and api.py reach it via `from app.utils import
        storage; storage.get_storage_bucket()` - patching the attribute on the
        shared app.utils.storage module object (rather than a per-importer
        qualified path) covers every caller in one patch, since each of them
        holds a reference to that same module object, not a copy of the
        function.

        Without this, a generation test's upload (or a download test's read)
        falls through to a real `google.cloud.storage.Client()` call, which
        needs Application Default Credentials neither this sandboxed test
        environment nor CI (no docker-compose, no fake-gcs-server, no gcloud
        login) has - raising DefaultCredentialsError. Locally, docker-compose
        happens to mask this by pointing USE_LOCAL_STORAGE_EMULATOR at a real
        fake-gcs-server container; CI has no equivalent, so it always surfaces
        there even when a local `docker-compose run pytest` looks clean.
        """
        patcher = mock.patch('app.utils.storage.get_storage_bucket')
        mock_get_bucket = patcher.start()
        self.addCleanup(patcher.stop)
        mock_blob = mock_get_bucket.return_value.blob.return_value
        mock_blob.upload_from_string.return_value = None
        mock_blob.download_to_filename.return_value = None
        return mock_get_bucket

    def make_form(self, event_id=None, form_type=None, name=None):
        event_id = event_id or self.event_id
        form = Form(event_id=event_id, created_by_user_id=self.user_id, form_type=form_type)
        db.session.add(form)
        db.session.flush()
        db.session.add(FormTranslation(
            form_id=form.id, language='en',
            name=name or (form_type or 'form').title() + ' Form',
        ))
        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        form._section = section
        db.session.commit()
        return form

    def make_question(self, form, key, question_type='short-text', headline=None,
                       dependency_expression=None, options=None):
        question = FormQuestion(
            form_id=_pk(form), section_id=form._section.id, order=1,
            question_type=question_type, key=key,
            dependency_expression=dependency_expression,
        )
        db.session.add(question)
        db.session.flush()
        db.session.add(FormQuestionTranslation(
            form_question_id=question.id, language='en',
            headline=headline or key, options=options,
        ))
        db.session.commit()
        return question

    def submit_response(self, form, user, answers, submitted=True):
        """answers: {question: value}"""
        response = FormResponse(form_id=_pk(form), user_id=_pk(user))
        response.is_submitted = submitted
        if submitted:
            response.submitted_timestamp = datetime.now()
        db.session.add(response)
        db.session.flush()
        for question, value in answers.items():
            db.session.add(FormAnswer(response_id=response.id, question_id=_pk(question), value=value))
        db.session.commit()
        return response

    def make_document_template(self, event_id=None, key='invitation-letter', name='Invitation Letter',
                                self_service=True, eligibility_expression=None,
                                allow_blank_values=False, filename_pattern=None,
                                delivery_mode='none'):
        event_id = event_id or self.event_id
        document_template = DocumentTemplate(
            event_id=event_id, created_by_user_id=self.user_id, key=key,
            self_service=self_service, eligibility_expression=eligibility_expression,
            allow_blank_values=allow_blank_values, filename_pattern=filename_pattern,
            delivery_mode=delivery_mode,
        )
        db.session.add(document_template)
        db.session.flush()
        db.session.add(DocumentTemplateTranslation(
            document_template_id=document_template.id, language='en', name=name))
        db.session.commit()
        return document_template

    def make_variant(self, document_template, placeholders, name='Default',
                      language=None, selection_expression=None, priority=0,
                      google_file_id=None, google_file_type='document'):
        variant = DocumentTemplateVariant(
            document_template_id=_pk(document_template), name=name,
            google_file_id=google_file_id or f'file-{name}',
            google_file_type=google_file_type,
            language=language, selection_expression=selection_expression, priority=priority,
        )
        variant.detected_placeholders = list(placeholders)
        variant.access_status = 'ok'
        db.session.add(variant)
        db.session.commit()
        return variant

    def link_form(self, document_template, form, order, requirement='none', prompt_message=None):
        link = DocumentTemplateForm(
            document_template_id=_pk(document_template), form_id=_pk(form),
            order=order, requirement=requirement,
        )
        db.session.add(link)
        db.session.flush()
        if prompt_message:
            db.session.add(DocumentTemplateFormTranslation(
                document_template_form_id=link.id, language='en', prompt_message=prompt_message))
        db.session.commit()
        return link

    def set_user_data(self, event, user, key, value):
        row = UserEventData(
            event_id=_pk(event), user_id=_pk(user), key=key, value=value,
            updated_by_user_id=self.user_id,
        )
        db.session.add(row)
        db.session.commit()
        return row

    def make_tag(self, event, name='Accommodation'):
        tag = Tag(event_id=_pk(event), tag_type=TagType.OFFER_NOTE)
        db.session.add(tag)
        db.session.flush()
        db.session.add(TagTranslation(tag_id=tag.id, language='en', name=name))
        db.session.commit()
        return tag

    def give_offer_tag(self, event, user, tag):
        event_id, user_id = _pk(event), _pk(user)
        offer = db.session.query(Offer).filter_by(user_id=user_id, event_id=event_id).first()
        if not offer:
            offer = Offer(
                user_id=user_id, event_id=event_id, offer_date=datetime.now(),
                expiry_date=datetime.now(), payment_required=False, candidate_response=True,
            )
            db.session.add(offer)
            db.session.flush()
        db.session.add(OfferTag(offer_id=offer.id, tag_id=_pk(tag), accepted=True))
        db.session.commit()
        return offer

    def give_guest_tag(self, event, user, tag):
        event_id, user_id = _pk(event), _pk(user)
        invited_guest = db.session.query(InvitedGuest).filter_by(
            user_id=user_id, event_id=event_id).first()
        if not invited_guest:
            invited_guest = InvitedGuest(event_id=event_id, user_id=user_id, role='guest')
            db.session.add(invited_guest)
            db.session.flush()
        db.session.add(InvitedGuestTag(invited_guest_id=invited_guest.id, tag_id=_pk(tag)))
        db.session.commit()
        return invited_guest

    def mark_attended(self, event, user):
        attendance = Attendance(event_id=_pk(event), user_id=_pk(user), updated_by_user_id=self.user_id)
        attendance.confirm()
        db.session.add(attendance)
        db.session.commit()
        return attendance
