from datetime import datetime
import flask_restful as restful
from sqlalchemy.exc import IntegrityError
from app.applicationModel.models import Question
from app.responses.models import Answer, Response
from app.registration.models import RegistrationSection
from app.registration.models import RegistrationQuestion
from app.registration.models import RegistrationForm
from app.registration.mixins import RegistrationFormMixin, RegistrationSectionMixin, RegistrationQuestionMixin
from app.utils.auth import verify_token
import traceback
from flask import g, request
from flask_restful import fields, marshal_with
from sqlalchemy.exc import SQLAlchemyError
from app.events.models import Event
from app.invitationletter.models import InvitationTemplate
from app.registration.models import Offer
from app.invitationletter.mixins import InvitationMixin
from app.users.models import AppUser
from app import db, LOGGER
from app.utils import errors
from app.utils.auth import auth_required, admin_required
from app.utils.emailer import send_mail


class InvitationLetterAPI(InvitationMixin, restful.Resource):

    @admin_required
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
        to_date = datetime.strptime((args['offer_date']), '%Y-%m-%dT%H:%M:%S.%fZ')
        from_date = datetime.strptime((args['expiry_date']), '%Y-%m-%dT%H:%M:%S.%fZ')

        user_id = verify_token(request.headers.get('Authorization'))['id']

        offer = db.session.query(Offer).filter(
            Offer.user_id == user_id).first()

        if not offer:
            return errors.OFFER_NOT_FOUND

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


        # registration_form = RegistrationForm(
        #
        #     event_id=event_id
        # )
        #
        # db.session.add(registration_form)

        try:
            db.session.commit()
        except IntegrityError:
            LOGGER.error(
                "Failed to add registration form for event : {}".format(event_id))
            return errors.ADD_REGISTRATION_FORM_FAILED

        return
