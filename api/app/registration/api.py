from datetime import datetime
import traceback

from flask import g, request
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with
from sqlalchemy.exc import SQLAlchemyError

from app.events.models import Event, EventRole
from app.offer.models import Offer, OfferRole
from app.events.mixins import EventsMixin
from app.users.models import AppUser
from app.users.repository import UserRepository as user_repository
from app.applicationModel.models import ApplicationForm
from app.responses.models import Response

from app import db, bcrypt, LOGGER
from app.utils.errors import EVENT_NOT_FOUND, FORBIDDEN

from app.utils.auth import auth_optional, auth_required
from app.utils.emailer import send_mail



OFFER_EMAIL_BODY = """
Dear {title} {firstname} {lastname},

//Offer Template

Kind Regards,
The Deep Learning Indaba team
"""
class NewOfferAPI(restful.Resources):

    @auth_requied
    def post(self):
        args = self.req_parse.pase_args()
        event_id = args['event_id']
        offer_date = args['offer_date']
        user_id = g.current_user['id']
