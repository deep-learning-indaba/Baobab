"""Resolves a bulk-generation recipient selection (design section 9.7) to a
set of user ids. Deliberately independent of eligibility: `document_template.
eligibility_expression` is a separate, later filter (app/documents/generator.py),
applied to whatever population a selection like "everyone" or "by tag" turns up.
"""
from sqlalchemy import func

from app import db
from app.offer.models import Offer, OfferTag
from app.invitedGuest.models import InvitedGuest, InvitedGuestTag
from app.forms.models import FormResponse
from app.users.models import AppUser


def _event_population_user_ids(event_id):
    """Everyone this event knows about at all: an applicant with an Offer row,
    or an InvitedGuest row - the same population tag expressions already
    evaluate against (app/forms/visibility.py)."""
    offer_users = {row[0] for row in db.session.query(Offer.user_id).filter_by(event_id=event_id).all()}
    guest_users = {row[0] for row in
                   db.session.query(InvitedGuest.user_id).filter_by(event_id=event_id).all()}
    return offer_users | guest_users


def _user_ids_with_tag(event_id, tag_id):
    offer_users = {row[0] for row in (
        db.session.query(Offer.user_id)
        .join(OfferTag, OfferTag.offer_id == Offer.id)
        .filter(Offer.event_id == event_id, OfferTag.tag_id == tag_id)
        .all())}
    guest_users = {row[0] for row in (
        db.session.query(InvitedGuest.user_id)
        .join(InvitedGuestTag, InvitedGuestTag.invited_guest_id == InvitedGuest.id)
        .filter(InvitedGuest.event_id == event_id, InvitedGuestTag.tag_id == tag_id)
        .all())}
    return offer_users | guest_users


def _user_ids_with_form_submitted(form_id):
    return {row[0] for row in db.session.query(FormResponse.user_id).filter(
        FormResponse.form_id == form_id,
        FormResponse.is_submitted == True,   # noqa: E712
        FormResponse.is_withdrawn == False,  # noqa: E712
    ).all()}


def _user_ids_from_emails(emails):
    normalised = {e.strip().lower() for e in (emails or []) if e and e.strip()}
    if not normalised:
        return set()
    return {row[0] for row in db.session.query(AppUser.id)
            .filter(func.lower(AppUser.email).in_(normalised)).all()}


def resolve_recipient_user_ids(event, selection):
    """`selection` (design section 9.7's recipient picker, stored verbatim on
    DocumentGenerationJob.recipient_selection for the audit trail):

      {"type": "everyone"}
      {"type": "tag", "tag_id": 12}
      {"type": "form_submitted", "form_id": 34}
      {"type": "user_ids", "user_ids": [1, 2, 3]}
      {"type": "emails", "emails": ["a@example.com", ...]}

    Returns a sorted list of distinct user ids. Any of these may include
    people who turn out ineligible or already-generated-for - that filtering
    happens one level up, in the preflight/job-creation API, since it needs
    per-person eligibility and blocker checks this module has no reason to
    duplicate.
    """
    selection = selection or {'type': 'everyone'}
    selection_type = selection.get('type', 'everyone')

    if selection_type == 'everyone':
        user_ids = _event_population_user_ids(event.id)
    elif selection_type == 'tag':
        user_ids = _user_ids_with_tag(event.id, selection.get('tag_id'))
    elif selection_type == 'form_submitted':
        user_ids = _user_ids_with_form_submitted(selection.get('form_id'))
    elif selection_type == 'user_ids':
        user_ids = set(selection.get('user_ids') or [])
    elif selection_type == 'emails':
        user_ids = _user_ids_from_emails(selection.get('emails'))
    else:
        user_ids = set()

    return sorted(user_ids)
