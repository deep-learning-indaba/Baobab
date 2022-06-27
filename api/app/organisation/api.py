import flask_restful as restful
from flask import g
from flask_restful import fields, marshal_with

from app.organisation.mixins import StripeSettingsMixin
from app.organisation.resolver import OrganisationResolver
from app.organisation.repository import OrganisationRepository as organisation_repository
from app.users.repository import UserRepository as user_repository
from app.utils.auth import auth_required
from app.utils.errors import FORBIDDEN

class OrganisationApi(restful.Resource):
    organisation_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'small_logo': fields.String,
        'large_logo': fields.String,
        'icon_logo': fields.String,
        'domain': fields.String,
        'system_name': fields.String,
        'url': fields.String,
        'email_from': fields.String,
        'system_url': fields.String,
        'privacy_policy': fields.String,
        'languages': fields.Raw
    }

    @marshal_with(organisation_fields)
    def get(self):
        return g.organisation

class StripeSettingsApi(restful.Resource, StripeSettingsMixin):
    settings_fields = {
        'iso_currency_code': fields.String,
        'stripe_api_publishable_key': fields.String,
        'stripe_api_secret_key': fields.String,
        'stripe_webhook_secret_key': fields.String
    }

    @auth_required
    @marshal_with(settings_fields)
    def get(self):
        current_user = user_repository.get_by_id(g.current_user['id'])
        if not current_user.is_admin:
            return FORBIDDEN

        return g.organisation

    @auth_required
    @marshal_with(settings_fields)
    def post(self):
        current_user = user_repository.get_by_id(g.current_user['id'])
        if not current_user.is_admin:
            return FORBIDDEN
        
        organisation = organisation_repository.get_by_id(g.organisation.id)
        
        args = self.req_parser.parse_args()
        organisation.set_currency(args['iso_currency_code'])
        organisation.set_stripe_keys(
            args['publishable_key'],
            args['secret_key'],
            args['webhook_secret_key']
        )
        organisation_repository.save()

        OrganisationResolver.bust_cache()
        return organisation, 200