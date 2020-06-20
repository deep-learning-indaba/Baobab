from app.events.models import Event
from app.users.models import AppUser
from app.invitedGuest.repository import InvitedGuestRepository as invited_guest_repository
from app.responses.repository import ResponseRepository as response_repository
from app.registrationResponse.repository import RegistrationRepository as registration_repository
from app.registration.repository import OfferRepository as offer_repository
from app.outcome.repository import OutcomeRepository as outcome_repository


class EventStatus():
    """Represents the status of a user at an event."""
    def __init__(self, 
                 invited_guest=None, 
                 application_status=None,
                 outcome_status=None,
                 offer_status=None, 
                 registration_status=None):
        if invited_guest is None and registration_status is not None and offer_status is None:
            raise ValueError('Non-invited guest must have an offer to have a registration status')
        
        if invited_guest is None and outcome_status is not None and application_status is None:
            raise ValueError('User must have applied to have an outcome')

        self.invited_guest=invited_guest 
        self.application_status = application_status
        self.registration_status=registration_status
        self.offer_status=offer_status
        self.outcome_status=outcome_status

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


def get_event_status(event_id, user_id):
    invited_guest = invited_guest_repository.get_for_event_and_user(event_id, user_id)
    if invited_guest:
        registration = invited_guest_repository.get_registration_for_event_and_user(event_id, user_id)
        # If they're an invited guest, we don't bother with whether they applied or not
        return EventStatus(invited_guest=invited_guest.role, 
                           registration_status=_get_registration_status(registration))
    
    response = response_repository.get_by_user_id_for_event(user_id, event_id)
    if response is None:
        application_status = None
    elif response.is_submitted:
        application_status = 'Submitted'
    elif response.is_withdrawn:
        application_status = 'Withdrawn'
    else:
        application_status = 'Not Submitted'

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

    registration = registration_repository.get_by_user_id(user_id, event_id)
    registration_status = _get_registration_status(registration)

    return EventStatus(application_status=application_status,
                       outcome_status=outcome_status,
                       offer_status=offer_status,
                       registration_status=registration_status)
