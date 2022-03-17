from datetime import datetime

import flask_restful as restful
from flask import g, request
from sqlalchemy.exc import IntegrityError

from app import LOGGER, db
from app.events.repository import EventRepository
from app.invitationletter.generator import generate
from app.invitationletter.mixins import InvitationMixin
from app.invitationletter.models import InvitationLetterRequest, InvitationTemplate
from app.invitedGuest.models import GuestRegistration
from app.registration.models import (
    Offer,
    Registration,
    RegistrationAnswer,
    RegistrationForm,
    RegistrationQuestion,
)
from app.users.models import AppUser, Country
from app.utils import errors
from app.utils.auth import auth_required, verify_token


def invitation_info(invitation_request):
    return {
        "invitation_letter_request_id": invitation_request.id,
    }


class InvitationLetterAPI(InvitationMixin, restful.Resource):
    @auth_required
    def post(self):
        # Process arguments
        args = self.req_parser.parse_args()
        event_id = args["event_id"]
        work_address = args["work_address"] if args["work_address"] is not None else " "
        addressed_to = args["addressed_to"] or "Whom it May Concern"
        residential_address = args["residential_address"]
        passport_name = args["passport_name"]
        passport_no = args["passport_no"]
        passport_issued_by = args["passport_issued_by"]
        passport_expiry_date = datetime.strptime(
            (args["passport_expiry_date"]), "%Y-%m-%d"
        )

        registration_event = EventRepository.get_by_id(event_id)
        if registration_event is not None:
            to_date = registration_event.end_date
            from_date = registration_event.start_date
        else:
            return errors.EVENT_ID_NOT_FOUND

        # Finding registation_id for this user at this event
        user_id = verify_token(request.headers.get("Authorization"))["id"]
        offer = (
            db.session.query(Offer)
            .filter(Offer.user_id == user_id)
            .filter(Offer.event_id == event_id)
            .first()
        )
        registration_form = (
            db.session.query(RegistrationForm)
            .filter(RegistrationForm.event_id == event_id)
            .first()
        )

        if not registration_form:
            return errors.REGISTRATION_FORM_NOT_FOUND

        # Check if Guest Registration
        registration = None

        registration = (
            db.session.query(GuestRegistration)
            .filter(GuestRegistration.user_id == user_id)
            .filter(GuestRegistration.registration_form_id == registration_form.id)
            .first()
        )
        if registration:
            is_guest_registration = True
        else:
            is_guest_registration = False

        # Normal Registration
        if (not registration) and offer:
            registration = (
                db.session.query(Registration)
                .filter(Registration.offer_id == offer.id)
                .first()
            )

        if not registration:
            return errors.REGISTRATION_NOT_FOUND

        try:
            if is_guest_registration:
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
                    from_date=from_date,
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
                    from_date=from_date,
                )
            db.session.add(invitation_letter_request)
            db.session.commit()
        except Exception as e:
            LOGGER.error(
                "Failed to add invitation letter request for user id {} due to: {}".format(
                    user_id, e
                )
            )
            return errors.ADD_INVITATION_REQUEST_FAILED

        invitation_template = None
        if is_guest_registration:
            invitation_template = (
                db.session.query(InvitationTemplate)
                .filter(InvitationTemplate.send_for_both_travel_accommodation == False)
                .filter(InvitationTemplate.send_for_travel_award_only == False)
                .filter(InvitationTemplate.send_for_accommodation_award_only == False)
                .first()
            )
        elif (
            offer.accommodation_award
            and offer.accepted_accommodation_award
            and offer.travel_award
            and offer.accepted_travel_award
        ):
            invitation_template = (
                db.session.query(InvitationTemplate)
                .filter(InvitationTemplate.event_id == offer.event_id)
                .filter(InvitationTemplate.send_for_both_travel_accommodation == True)
                .first()
            )

        elif offer.travel_award and offer.accepted_travel_award:
            invitation_template = (
                db.session.query(InvitationTemplate)
                .filter(InvitationTemplate.event_id == offer.event_id)
                .filter(InvitationTemplate.send_for_travel_award_only == True)
                .first()
            )

        elif offer.accommodation_award and offer.accepted_accommodation_award:
            invitation_template = (
                db.session.query(InvitationTemplate)
                .filter(InvitationTemplate.event_id == offer.event_id)
                .filter(InvitationTemplate.send_for_accommodation_award_only == True)
                .first()
            )

        else:
            invitation_template = (
                db.session.query(InvitationTemplate)
                .filter(InvitationTemplate.send_for_both_travel_accommodation == False)
                .filter(InvitationTemplate.send_for_travel_award_only == False)
                .filter(InvitationTemplate.send_for_accommodation_award_only == False)
                .first()
            )

        template_url = invitation_template.template_path

        user = db.session.query(AppUser).filter(AppUser.id == user_id).first()
        country_of_residence = (
            db.session.query(Country)
            .filter(Country.id == user.residence_country_id)
            .first()
        )
        nationality = (
            db.session.query(Country)
            .filter(Country.id == user.nationality_country_id)
            .first()
        )

        if user.user_dateOfBirth is not None:
            date_of_birth = user.user_dateOfBirth.strftime("%Y-%m-%d")
        else:
            return errors.MISSING_DATE_OF_BIRTH

        # Poster registration
        bringing_poster = ""
        poster_registration_question = (
            db.session.query(RegistrationQuestion)
            .filter(RegistrationQuestion.headline == "Will you be bringing a poster?")
            .first()
        )
        if poster_registration_question is not None:
            poster_answer = (
                db.session.query(RegistrationAnswer)
                .join(
                    Registration, RegistrationAnswer.registration_id == Registration.id
                )
                .join(Offer, Offer.id == Registration.offer_id)
                .filter(Offer.user_id == user_id)
                .filter(
                    RegistrationAnswer.registration_question_id
                    == poster_registration_question.id
                )
                .first()
            )
            if poster_answer is not None and poster_answer.value == "yes":
                bringing_poster = (
                    "The participant will be presenting a poster of their research."
                )

        # Handling fields
        invitation_letter_request.invitation_letter_sent_at = datetime.now()
        is_sent = generate(
            template_path=template_url,
            event_id=event_id,
            work_address=work_address,
            addressed_to=addressed_to,
            residential_address=residential_address,
            passport_name=passport_name,
            passport_no=passport_no,
            passport_issued_by=passport_issued_by,
            invitation_letter_sent_at=invitation_letter_request.invitation_letter_sent_at.strftime(
                "%Y-%m-%d"
            ),
            expiry_date=passport_expiry_date.strftime("%Y-%m-%d"),
            to_date=to_date.strftime("%Y-%m-%d"),
            from_date=from_date.strftime("%Y-%m-%d"),
            country_of_residence=country_of_residence.name,
            nationality=nationality.name,
            date_of_birth=date_of_birth,
            email=user.email,
            user_title=user.user_title,
            firstname=user.firstname,
            lastname=user.lastname,
            bringing_poster=bringing_poster,
            user=user,
        )
        if not is_sent:
            return errors.SENDING_INVITATION_FAILED

        try:
            db.session.commit()
            return invitation_info(invitation_letter_request), 201

        except Exception as e:
            LOGGER.error(
                "Failed to add invitation request for user with email: {} due to {}".format(
                    user.email, e
                )
            )
            return errors.ADD_INVITATION_REQUEST_FAILED
