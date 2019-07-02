from datetime import datetime
import flask_restful as restful
from sqlalchemy.exc import IntegrityError
from app.utils.auth import verify_token
from flask import g, request
from app.invitationletter.models import InvitationTemplate
from app.registration.models import Offer
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
        to_date = datetime.strptime((args['to_date']), '%Y-%m-%dT%H:%M:%S.%fZ')
        from_date = datetime.strptime((args['from_date']), '%Y-%m-%dT%H:%M:%S.%fZ')
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
            invitation_letter_sent_at=datetime.now().strftime("%Y-%m-%d"),
            to_date=to_date,
            from_date=from_date,
        )

        offer = db.session.query(Offer).filter(
            Offer.user_id == user_id).first()

        if not offer:
            return errors.OFFER_NOT_FOUND

        global invitation_template

        if offer.accommodation_award and offer.travel_award:
            invitation_template = db.session.query(InvitationTemplate).filter(
                InvitationTemplate.event_id == offer.event_id).filter(
                InvitationTemplate.send_for_both_travel_accommodation).first()
        elif offer.travel_award:
            invitation_template = db.session.query(InvitationTemplate).filter(
                InvitationTemplate.event_id == offer.event_id).filter(
                InvitationTemplate.send_for_both_travel_accommodation).first()
        elif offer.accommodation_award:
            invitation_template = db.session.query(InvitationTemplate).filter(
                InvitationTemplate.event_id == offer.event_id).filter(
                InvitationTemplate.send_for_both_travel_accommodation).first()

        if invitation_template:
            template_url = invitation_template.template_path

            user = db.session.query(AppUser).filter(
                AppUser.id == user_id).first()

            if not user:
                return errors.USER_NOT_FOUND

            country_of_residence = db.session.query(Country).filter(Country.id == user.residence_country_id).first()
            nationality = db.session.query(Country).filter(Country.id == user.nationality_country_id).first()
            date_of_birth = user.user_dateOfBirth

            is_sent = generate(template_path=template_url,
                               event_id=event_id,
                               work_address=work_address,
                               addressed_to=addressed_to,
                               residential_address=residential_address,
                               passport_name=passport_name,
                               passport_no=passport_no,
                               passport_issued_by=passport_issued_by,
                               invitation_letter_sent_at=invitation_letter_request.invitation_letter_sent_at,
                               to_date=to_date,
                               from_date=from_date,
                               country_of_residence=country_of_residence,
                               nationality=nationality,
                               date_of_birth=date_of_birth,
                               email=user.email,
                               user_title=user.user_title,
                               firstname=user.firstname,
                               lastname=user.lastname)

            if is_sent:
                try:
                    db.session.add(invitation_letter_request)
                    db.session.commit()
                except Exception as e:
                    LOGGER.error(
                        "Failed to add invitation request for user with email: {} due to {}".format(user.email, e))
                    return errors.ADD_INVITATION_REQUEST_FAILED

            return invitation_info(invitation_letter_request), 201

        return errors.TEMPLATE_NOT_FOUND
