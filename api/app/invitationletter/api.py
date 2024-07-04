from datetime import datetime
import flask_restful as restful
from app.utils.auth import verify_token
from flask import g, request
from app.invitationletter.models import InvitationTemplate
from app.registration.models import Registration, RegistrationAnswer, RegistrationQuestion, Registration, RegistrationForm
from app.offer.models import Offer
from app.invitedGuest.models import InvitedGuest, GuestRegistrationAnswer, GuestRegistration
from app.invitationletter.mixins import InvitationMixin
from app.invitationletter.models import InvitationLetterRequest
from app.invitationletter.generator import generate
from app.users.models import AppUser
from app import db, LOGGER
from app.utils import errors
from app.utils.auth import auth_required
from app.events.repository import EventRepository


def invitation_info(invitation_request):
    return {
        'invitation_letter_request_id': invitation_request.id,
    }


def find_registration_answer(is_guest_registration: bool, registration_question_id: int, user_id: int, event_id: int): 
    if is_guest_registration:
        answer = (
                db.session.query(GuestRegistrationAnswer)
                    .filter_by(is_active=True)
                    .join(GuestRegistration, GuestRegistrationAnswer.guest_registration_id == GuestRegistration.id)
                    .filter_by(user_id=user_id)
                    .join(RegistrationForm, GuestRegistration.registration_form_id == RegistrationForm.id)
                    .filter_by(event_id=event_id)
                    .filter(GuestRegistrationAnswer.registration_question_id == registration_question_id)
                    .first())
    else:
        answer = (
            db.session.query(RegistrationAnswer)
                .join(Registration, RegistrationAnswer.registration_id == Registration.id)
                .join(Offer, Offer.id == Registration.offer_id)
                .filter_by(user_id=user_id, event_id=event_id)
                .filter(RegistrationAnswer.registration_question_id == registration_question_id)
                .first())
    return answer


def find_registration_question_by_headline(headline: str, registration_form_id: int):
    return (db.session.query(RegistrationQuestion)
            .filter_by(headline=headline, registration_form_id=registration_form_id)
            .first())

class InvitationLetterAPI(InvitationMixin, restful.Resource):

    @auth_required
    def post(self):
        # Process arguments
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        work_address = args['work_address'] if args['work_address'] is not None else ' '
        addressed_to = args['addressed_to'] or 'Whom it May Concern'
        residential_address = args['residential_address']
        passport_name = args['passport_name']
        passport_no = args['passport_no']
        passport_issued_by = args['passport_issued_by']
        passport_expiry_date = datetime.strptime((args['passport_expiry_date']), '%Y-%m-%d')
        date_of_birth = datetime.strptime((args['date_of_birth']), '%Y-%m-%d')
        country_of_residence = args['country_of_residence']
        country_of_nationality = args['country_of_nationality']

        registration_event = EventRepository.get_by_id(event_id)
        if(registration_event is not None):
            to_date = registration_event.end_date
            from_date = registration_event.start_date
        else:
            return errors.EVENT_ID_NOT_FOUND

        # Finding registation_id for this user at this event
        user_id = verify_token(request.headers.get('Authorization'))['id']
        offer = db.session.query(Offer).filter(
            Offer.user_id == user_id).filter(Offer.event_id == event_id).first()
        registration_form = db.session.query(RegistrationForm).filter(
            RegistrationForm.event_id == event_id).first()

        if not registration_form:
            return errors.REGISTRATION_FORM_NOT_FOUND
            
        # Check if Guest Registration
        registration = None

        registration = db.session.query(GuestRegistration).filter(
            GuestRegistration.user_id == user_id).filter(GuestRegistration.registration_form_id == registration_form.id).first()
        if registration:
            is_guest_registration = True
            invited_guest = db.session.query(InvitedGuest).filter_by(event_id=event_id, user_id=user_id).first()
        else:
            is_guest_registration = False
            invited_guest = None

        # Normal Registration
        if (not registration) and offer:
            registration = db.session.query(Registration).filter(
                Registration.offer_id == offer.id).first()

        if not registration:
            return errors.REGISTRATION_NOT_FOUND

        try:
            if(is_guest_registration):
                invitation_letter_request = InvitationLetterRequest(
                    guest_registration_id=registration.id,
                    event_id=event_id,
                    work_address=work_address,
                    addressed_to=addressed_to,
                    residential_address=residential_address,
                    passport_name=passport_name,
                    passport_no=passport_no,
                    passport_issued_by=passport_issued_by,
                    passport_expiry_date=passport_expiry_date,
                    to_date=to_date,
                    from_date=from_date
                )
            else:
                invitation_letter_request = InvitationLetterRequest(
                    registration_id=registration.id,
                    event_id=event_id,
                    work_address=work_address,
                    addressed_to=addressed_to,
                    residential_address=residential_address,
                    passport_name=passport_name,
                    passport_no=passport_no,
                    passport_issued_by=passport_issued_by,
                    passport_expiry_date=passport_expiry_date,
                    to_date=to_date,
                    from_date=from_date
                )
            db.session.add(invitation_letter_request)
            db.session.commit()
        except Exception as e:
            LOGGER.error('Failed to add invitation letter request for user id {} due to: {}'.format(user_id, e))
            return errors.ADD_INVITATION_REQUEST_FAILED

        # Look for travel and accommodation tags
        if is_guest_registration and invited_guest is not None:
            tags = [t.tag.get_translation('en').name for t in invited_guest.invited_guest_tags]
        else:
            tags = [t.tag.get_translation('en').name for t in offer.offer_tags if t.accepted]

        accommodation = 'Accommodation' in tags
        travel = 'Travel' in tags

        LOGGER.info(f"Generating invitation letter for {passport_name} with accommodation: {accommodation}, Travel: {travel}")
        
        invitation_template = (
            db.session.query(InvitationTemplate)
            .filter_by(
                event_id=event_id,
                send_for_both_travel_accommodation=travel and accommodation,
                send_for_travel_award_only=travel and not accommodation,
                send_for_accommodation_award_only=accommodation and not travel)
            .first())
        
        template_url = invitation_template.template_path
        LOGGER.info(f"Using template_url: {template_url}")

        user = db.session.query(AppUser).filter(AppUser.id==user_id).first()

        def make_presenting_text(bringing_question_headline: str, title_question_headline: str, description: str) -> str:
            text = ""
            bringing_question = find_registration_question_by_headline(bringing_question_headline, registration_form.id)
            title_question = find_registration_question_by_headline(title_question_headline, registration_form.id)
            
            if bringing_question is not None:
                answer = find_registration_answer(is_guest_registration, bringing_question.id, user_id, event_id)
                if answer is not None and answer.value == 'yes':
                    text = description
                    if title_question is not None:
                        title_answer = find_registration_answer(is_guest_registration, title_question.id, user_id, event_id)
                        if title_answer is not None and len(title_answer.value) > 0:
                            text += f' titled "{title_answer.value}"'
                    
                    text += "."

            return text

        # Poster registration
        bringing_poster = make_presenting_text(
            "Would you like to present a poster during the Africa Research Days?",
            "What is the provisional title of your poster?",
            f"{user.firstname} will be presenting a poster of their research")
        
        bringing_poster_fr = make_presenting_text(
           "Would you like to present a poster during the Africa Research Days?",
            "What is the provisional title of your poster?",
            f"{user.firstname} présentera un poster de leur recherche")

        if not bringing_poster:
            bringing_poster = make_presenting_text(
                "Do you have an African Dataset that you would like to showcase during the African Datasets Session?",
                "What is the provisional title of your dataset?",
                f"{user.firstname} will be presenting an African dataset")
            
            bringing_poster_fr = make_presenting_text(
                "Do you have an African Dataset that you would like to showcase during the African Datasets Session?",
                "What is the provisional title of your dataset?",
                f"{user.firstname} présentera un jeu de données africain")
        
        if not bringing_poster:
            bringing_poster = make_presenting_text(
                "Would you like to show a demo of something you are working on?",
                "What is the provisional title of your demo?",
                f"{user.firstname} will be showcasing a demo of their work")
            
            bringing_poster_fr = make_presenting_text(
                "Would you like to show a demo of something you are working on?",
                "What is the provisional title of your demo?",
                f"{user.firstname} présentera une démo de leur travail")
        
        # Handling fields
        invitation_letter_request.invitation_letter_sent_at=datetime.now()
        is_sent = generate(template_path=template_url,
                            event_id=event_id,
                            work_address=work_address,
                            addressed_to=addressed_to,
                            residential_address=residential_address,
                            passport_name=passport_name,
                            passport_no=passport_no,
                            passport_issued_by=passport_issued_by,
                            invitation_letter_sent_at=invitation_letter_request.invitation_letter_sent_at.strftime("%Y-%m-%d"),
                            expiry_date=passport_expiry_date.strftime("%Y-%m-%d"),
                            to_date=to_date.strftime("%Y-%m-%d"),
                            from_date=from_date.strftime("%Y-%m-%d"),
                            country_of_residence=country_of_residence,
                            nationality=country_of_nationality,
                            date_of_birth=date_of_birth.strftime("%Y-%m-%d"),
                            email=user.email,
                            user_title=user.user_title,
                            firstname=user.firstname,
                            lastname=user.lastname,
                            bringing_poster=bringing_poster,
                            bringing_poster_fr=bringing_poster_fr,
                            user=user
                            )
        if not is_sent:
            return errors.SENDING_INVITATION_FAILED

        try:
            db.session.commit()
            return invitation_info(invitation_letter_request), 201

        except Exception as e:
            LOGGER.error(
                "Failed to add invitation request for user with email: {} due to {}".format(user.email, e))
            return errors.ADD_INVITATION_REQUEST_FAILED
