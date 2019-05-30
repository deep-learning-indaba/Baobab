from datetime import datetime
import traceback

from flask import g, request
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with
from sqlalchemy.exc import SQLAlchemyError

from app.events.models import Event, EventRole
from app.offer.models import OfferEntity
from app.offer.mixins import OfferMixin
from app.users.models import AppUser
from app.users.repository import UserRepository as user_repository
from app.applicationModel.models import ApplicationForm
from app.responses.models import Response

from app import db, bcrypt, LOGGER
from app.utils.errors import EVENT_NOT_FOUND, FORBIDDEN
from app.users import api as UserAPI
from app.users.mixins import SignupMixin

from app.utils.auth import auth_optional, auth_required
from app.utils.emailer import send_mail



OFFER_EMAIL_BODY = """
Dear {title} {firstname} {lastname},

//Offer Template

Kind Regards,
The Deep Learning Indaba team
"""

def offer_info(offerEntity):
    return {
        'user_id': offerEntity.user_id,
        'event_id':offerEntity.event_d,
        'offer_date':offerEntity.offer_date,
        'expiry_date':offerEntity.expiry_date,
        'payment_required':offerEntity.payment_required,
        'travel_award':offerEntity.travel_award,
        'accommodation_award':offerEntity.accomodation_award
    }


class NewOfferAPI(restful.Resources):

    @auth_requied
    def post(self):
        args = self.req_parse.pase_args()
        user_id = g.current_user['id']
        event_id = args['event_id']
        offer_date = args['offer_date']

    user = db.session.query(AppUser).filter(
            AppUser.email == email).first()

    offerEntity = OfferEntity(
        user_id = user_id,
        event_id = event_d,
        offer_date = offer_date,
        expiry_date = expiry_date,
        payment_required = payment_required,
        travel_award = travel_award,
        accommodation_award = accomodation_award
    )

    db.session.add(offerEntity)

    try:
        db.session.commit()
    except IntegrityError:
        LOGGER.error(
            "Failed to add offer: {}",format(email))
        return ADD_INITED_IFO_FAILED

    return offer_info(offerEntity),201


class CreateOffer(SignupMixin, restful.Resource):

    @auth_required
    def post(self):
        user_api = UserAPI.UserAPI()
        return user_api.post(True)
