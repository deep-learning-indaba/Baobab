from app.events.models import Event
from app.users.models import AppUser
from app.invitedGuest.repository import InvitedGuestRepository as invited_guest_repository
from app.responses.repository import ResponseRepository as response_repository
from app.registrationResponse.repository import RegistrationRepository as registration_repository
from app.offer.repository import OfferRepository as offer_repository
from app.outcome.repository import OutcomeRepository as outcome_repository
from app.forms.models import FormResponse
from app.forms import system as form_system
from app import db


class EventStatus():
    """Represents the status of a user at an event."""
    def __init__(self,
                 invited_guest=None,
                 application_status=None,
                 outcome_status=None,
                 offer_status=None,
                 registration_status=None,
                 survey_status=None):
        if invited_guest is None and registration_status is not None and offer_status is None:
            raise ValueError('Non-invited guest must have an offer to have a registration status')

        if invited_guest is None and outcome_status is not None and application_status is None:
            raise ValueError('User must have applied to have an outcome')

        self.invited_guest=invited_guest
        self.application_status = application_status
        self.registration_status=registration_status
        self.offer_status=offer_status
        self.outcome_status=outcome_status
        self.survey_status=survey_status

    @property
    def is_event_attendee(self):
        return self.invited_guest or self.offer_status == "Accepted"


def _get_registration_status(registration):
    if registration is None:
        return None
    if registration.confirmed:
        return 'Confirmed'
    else:
        return 'Not Confirmed'


def _get_survey_status(event_id, user_id):
    event = db.session.query(Event).get(event_id)
    if event is None or event.survey_form_id is None:
        return None

    form_response = db.session.query(FormResponse).filter_by(
        form_id=event.survey_form_id, user_id=user_id
    ).order_by(FormResponse.id.desc()).first()

    if form_response is None:
        return 'Not Submitted'
    elif form_response.is_submitted:
        return 'Submitted'
    else:
        return 'Not Submitted'


def _latest_form_response(form, user_id):
    return db.session.query(FormResponse).filter_by(
        form_id=form.id, user_id=user_id
    ).order_by(FormResponse.id.desc()).first()


def _application_status(response):
    """Status string for a legacy Response or a FormResponse."""
    if response is None:
        return None
    if response.is_withdrawn:
        return 'Withdrawn'
    if response.is_submitted:
        return 'Submitted'
    return 'Not Submitted'


def _new_registration_status(event_id, user_id, invited_guest=None, offer=None):
    """Registration status from the event's new-system registration form.

    A submitted registration is only 'Confirmed' once the attendee's place is
    secured: always for an invited guest, otherwise when the offer is accepted
    and, if payment is required, paid.
    """
    form = form_system.get_registration_form(event_id)
    if form is None:
        return None
    response = _latest_form_response(form, user_id)
    if response is None or not response.is_submitted or response.is_withdrawn:
        return None
    if invited_guest is not None or (offer is not None and offer.is_confirmed):
        return 'Confirmed'
    return 'Not Confirmed'


def get_event_status(event_id, user_id):
    survey_status = _get_survey_status(event_id, user_id)
    uses_new_forms = form_system.event_uses_new_forms(event_id)

    invited_guest = invited_guest_repository.get_for_event_and_user(event_id, user_id)
    if invited_guest:
        if uses_new_forms:
            registration_status = _new_registration_status(event_id, user_id, invited_guest=invited_guest)
        else:
            registration = invited_guest_repository.get_registration_for_event_and_user(event_id, user_id)
            registration_status = _get_registration_status(registration)
        # If they're an invited guest, we don't bother with whether they applied or not
        return EventStatus(invited_guest=invited_guest.role,
                           registration_status=registration_status,
                           survey_status=survey_status)

    if uses_new_forms:
        app_form = form_system.get_application_form(event_id)
        response = _latest_form_response(app_form, user_id) if app_form else None
    else:
        response = response_repository.get_by_user_id_for_event(user_id, event_id)
    application_status = _application_status(response)

    outcome = outcome_repository.get_latest_by_user_for_event(user_id, event_id)
    if outcome is None:
        outcome_status = None
    else:
        outcome_status = outcome.status.name

    offer = offer_repository.get_by_user_id_for_event(user_id, event_id)
    if offer is None:
        offer_status = None
    elif offer.candidate_response:
        offer_status = 'Accepted'
    elif offer.candidate_response == False:
        offer_status = 'Rejected'
    elif offer.is_expired():
        offer_status = 'Expired'
    else:
        offer_status = 'Pending'

    if offer is None:
        registration_status = None
    elif uses_new_forms:
        registration_status = _new_registration_status(event_id, user_id, offer=offer)
    else:
        registration = registration_repository.get_by_user_id(user_id, event_id)
        registration_status = _get_registration_status(registration)

    return EventStatus(application_status=application_status,
                       outcome_status=outcome_status,
                       offer_status=offer_status,
                       registration_status=registration_status,
                       survey_status=survey_status)
