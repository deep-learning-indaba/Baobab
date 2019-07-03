from datetime import datetime
import flask_restful as restful
from sqlalchemy.exc import IntegrityError
from app.utils.auth import verify_token
from flask import g, request
from app.invitationletter.models import InvitationTemplate
from app.registration.models import Offer, Registration, RegistrationAnswer, RegistrationQuestion
from app.invitationletter.mixins import InvitationMixin
from app.invitationletter.models import InvitationLetterRequest
from app.invitationletter.generator import generate
from app.users.models import AppUser, Country
from app import db, LOGGER
from app.utils import errors
from app.utils.auth import auth_required


def invitation_info(invitation_request):
    return {
        'invitation_letter_request_id': invitation_request.id,
    }


class InvitationLetterAPI(InvitationMixin, restful.Resource):

    @auth_required
    def post(self):
        args = self.req_parser.parse_args()
        registration_id = args['registration_id']
        event_id = args['event_id']
        work_address = args['work_address']
        addressed_to = args['addressed_to']
        residential_address = args['residential_address']
        passport_name = args['passport_name']
        passport_no = args['passport_no']
        passport_issued_by = args['passport_issued_by']
        passport_expiry_date = datetime.strptime((args['passport_expiry_date']),
                                                 '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%Y-%m-%d")
        to_date = datetime.strptime((args['to_date']),
                                    '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%Y-%m-%d")
        from_date = datetime.strptime((args['from_date']),
                                      '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%Y-%m-%d")
        user_id = verify_token(request.headers.get('Authorization'))['id']

        invitation_letter_request = InvitationLetterRequest(
            registration_id=registration_id,
            event_id=event_id,
            work_address=work_address,
            addressed_to=addressed_to,
            residential_address=residential_address,
            passport_name=passport_name,
            passport_no=passport_no,
            passport_issued_by=passport_issued_by,
            passport_expiry_date=passport_expiry_date,
            invitation_letter_sent_at=datetime.now().strftime("%Y-%m-%d"),
            to_date=to_date,
            from_date=from_date,
        )

        offer = db.session.query(Offer).filter(
            Offer.user_id == user_id).first()

        if not offer:
            return errors.OFFER_NOT_FOUND

        invitation_template = None

        if offer.accommodation_award and offer.accepted_accommodation_award \
                and offer.travel_award and offer.accepted_travel_award:
            invitation_template = db.session.query(InvitationTemplate).filter(
                InvitationTemplate.event_id == offer.event_id).filter(
                InvitationTemplate.send_for_both_travel_accommodation).first()

        elif offer.travel_award and offer.accepted_travel_award:
            invitation_template = db.session.query(InvitationTemplate).filter(
                InvitationTemplate.event_id == offer.event_id).filter(
                InvitationTemplate.send_for_travel_award_only).first()

        elif offer.accommodation_award and offer.accepted_accommodation_award:
            invitation_template = db.session.query(InvitationTemplate).filter(
                InvitationTemplate.event_id == offer.event_id).filter(
                InvitationTemplate.send_for_accommodation_award_only).first()

        elif (not offer.accommodation_award) and (not offer.travel_award):
            invitation_template = db.session.query(InvitationTemplate)\
                .filter(not InvitationTemplate.send_for_both_travel_accommodation)\
                .filter(not InvitationTemplate.send_for_travel_award_only)\
                .filter(not InvitationTemplate.send_for_accommodation_award_only).first()


        if invitation_template:
            template_url = invitation_template.template_path

            user = db.session.query(AppUser).filter(
                AppUser.id == user_id).first()

            if not user:
                return errors.USER_NOT_FOUND

            country_of_residence = db.session.query(Country).filter(Country.id == user.residence_country_id).first()
            nationality = db.session.query(Country).filter(Country.id == user.nationality_country_id).first()
            date_of_birth = user.user_dateOfBirth

            bringing_poster = ""

            poster_registration_question = db.session.query(RegistrationQuestion).filter(RegistrationQuestion.headline == "Will you be bringing a poster?").first()
            if poster_registration_question is not None:
                poster_answer = (
                    db.session.query(RegistrationAnswer)
                    .join(Registration, RegistrationAnswer.registration_id == Registration.id)
                    .join(Offer, Offer.id == Registration.offer_id)
                    .filter(Offer.user_id == user_id)
                    .filter(RegistrationAnswer.registration_question_id == poster_registration_question.id)
                    .first()
                )

                if poster_answer is not None and poster_answer.value == "yes":
                    # Get whether they submitted a poster in registration
                    bringing_poster = "The candidate will be presenting an academic poster on their research."

                


            is_sent = generate(template_path=template_url,
                               event_id=event_id,
                               work_address=work_address,
                               addressed_to=addressed_to,
                               residential_address=residential_address,
                               passport_name=passport_name,
                               passport_no=passport_no,
                               passport_issued_by=passport_issued_by,
                               invitation_letter_sent_at=invitation_letter_request.invitation_letter_sent_at,
                               expiry_date=passport_expiry_date,
                               to_date=to_date,
                               from_date=from_date,
                               country_of_residence=country_of_residence,
                               nationality=nationality,
                               date_of_birth=date_of_birth,
                               email=user.email,
                               user_title=user.user_title,
                               firstname=user.firstname,
                               lastname=user.lastname,
                               bringing_poster=bringing_poster
                               )

            if is_sent:
                try:
                    db.session.add(invitation_letter_request)
                    db.session.commit()
                    return invitation_info(invitation_letter_request), 201

                except Exception as e:
                    LOGGER.error(
                        "Failed to add invitation request for user with email: {} due to {}".format(user.email, e))
                    return errors.ADD_INVITATION_REQUEST_FAILED

            else:
                return errors.SENDING_INVITATION_FAILED

        return errors.TEMPLATE_NOT_FOUND
