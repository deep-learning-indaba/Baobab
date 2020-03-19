from app.users.models import AppUser
from app import db, app, LOGGER
import flask_restful as restful
from app.utils.errors import FAILED_CREATE_INTEGRATION_TEST_USER,FAILED_DELETE_INTEGRATION_TEST_USER

class CreateIntegrationUser(restful.Resource):

    # Create test user for integation tests
    def get(self):
        try:
            user = AppUser(email="john@thewall.com",
                        firstname="John",
                        lastname="Snow",
                        user_title="Mr",
                        password="whitewalker360",
                        organisation_id=4,
                        is_admin=True)
            user.verify()


            db.session.add(user)
            db.session.commit()
        except Exception as e:
            LOGGER.error('Failed to create test user {} due to: {}'.format(user, e))
            return FAILED_CREATE_INTEGRATION_TEST_USER

        return 200

class DeleteIntegrationUser(restful.Resource):

    # Delete test user for integation tests
    def get(self):
        try:
            user = AppUser.query.filter_by(email='john@thewall.com').first()

            db.session.delete(user)
            db.session.commit()
        except Exception as e:
            LOGGER.error('Failed to delete test user {} due to: {}'.format(user, e))
            return FAILED_DELETE_INTEGRATION_TEST_USER

        return 200