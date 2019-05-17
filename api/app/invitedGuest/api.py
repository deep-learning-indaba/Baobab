
from flask_restful import reqparse, fields, marshal_with
import flask_restful as restful
from sqlalchemy.exc import IntegrityError

from app.applicationModel.mixins import ApplicationFormMixin
from app.utils.auth import auth_required
from app import LOGGER
from app import db, bcrypt

from app.users.models import AppUser
from app.invitedGuest.models import InvitedGuest
from app.utils.errors import USER_NOT_FOUND, ADD_INVITED_GUEST_FAILED, INVITED_GUEST_FOR_EVENT_EXISTS
from app.invitedGuest.mixins import InvitedGuestMixin
from users import api as UserAPI


def invitedGuest_info(invitedGuest):
    return {
        'invitedGuest_id': invitedGuest.id,
        'event_id': invitedGuest.event_id,
        'user_id': invitedGuest.user_id,
        'role': invitedGuest.role
    }


class InvitedGuestAPI(InvitedGuestMixin, restful.Resource):

    @auth_required
    def post(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        email = args['email_address']
        role = args['role']

        user = db.session.query(AppUser).filter(
            AppUser.email == email).first()

        if not user:
            return USER_NOT_FOUND

        existingInvitedGuest = db.session.query(InvitedGuest).filter(
            InvitedGuest.event_id == event_id and InvitedGuest.user_id == user.id).first()

        if existingInvitedGuest:
            return INVITED_GUEST_FOR_EVENT_EXISTS

        invitedGuest = InvitedGuest(
            event_id=event_id,
            user_id=user.id,
            role=role
        )

        db.session.add(invitedGuest)

        try:
            db.session.commit()
        except IntegrityError:
            LOGGER.error(
                "Failed to add invited guest: {}".format(email))
            return ADD_INVITED_GUEST_FAILED

        return invitedGuest_info(invitedGuest), 201


class CreateUser(ApplicationFormMixin, restful.Resource):

    @auth_required
    def post(self):
        return UserAPI.post(args)
