import flask_restful as restful

from app import LOGGER, app, db
from app.integration_tests.mixins import IntegratoonTestDelete
from app.users.models import AppUser
from app.utils.errors import (
    FAILED_CREATE_INTEGRATION_TEST_USER,
    FAILED_DELETE_INTEGRATION_TEST_USER,
    USER_NOT_FOUND,
)


def user_info(user):
    return {
        "id": user.id,
        "email": user.email,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "title": user.user_title,
        "is_admin": user.is_admin,
    }


class CreateIntegrationUser(restful.Resource):

    # Create test user for integation tests
    def get(self):
        try:
            user = AppUser.query.filter_by(email="john@thewall.com").first()

            if user is None:
                user = AppUser(
                    email="john@thewall.com",
                    firstname="John",
                    lastname="Snow",
                    user_title="Mr",
                    password="whitewalker360",
                    organisation_id=4,
                    is_admin=True,
                )
                user.verify()
                db.session.add(user)
                db.session.commit()
        except Exception as e:
            LOGGER.error("Failed to create test user {} due to: {}".format(user, e))
            return FAILED_CREATE_INTEGRATION_TEST_USER

        return user_info(user)


class DeleteIntegrationUser(IntegratoonTestDelete, restful.Resource):

    # Delete test user for integation tests
    def post(self):
        try:
            user = None
            args = self.req_parser.parse_args()
            user = AppUser.query.filter_by(email=args["email"]).first()
            # Already deleted
            if user is None:
                return USER_NOT_FOUND
            db.session.delete(user)
            db.session.commit()
        except Exception as e:
            LOGGER.error("Failed to delete test user {} due to: {}".format(user, e))
            return FAILED_DELETE_INTEGRATION_TEST_USER

        return 200
