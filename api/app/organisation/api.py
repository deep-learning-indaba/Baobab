import re
from functools import wraps

import flask_restful as restful
from flask import g, request
from flask_restful import fields, marshal_with

from app.email_template.repository import BRAND_COLOUR_RE
from app.organisation.models import SUPPORTED_LANGUAGES
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
        'languages': fields.Raw,
        'iso_currency_code': fields.String,
        'pwa_icon_192': fields.String,
        'pwa_icon_512': fields.String,
        'primary_colour': fields.String,
        'secondary_colour': fields.String,
        'favicon': fields.String,
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


def org_admin_required(func):
    """Requires a valid token whose DB user is an admin of the requesting organisation."""
    @wraps(func)
    @auth_required
    def wrapper(*args, **kwargs):
        user = user_repository.get_by_id(g.current_user['id'])
        if user is None or not user.is_admin or user.organisation_id != g.organisation.id:
            return FORBIDDEN
        return func(*args, **kwargs)
    return wrapper


def _error(message, field):
    return {'message': message, 'field': field}, 400


class _InvalidField(Exception):
    def __init__(self, message, field):
        super().__init__(message)
        self.message = message
        self.field = field


# field: (max length, required)
_TEXT_FIELDS = {
    'name': (50, True),
    'system_name': (50, True),
    'url': (100, True),
    'system_url': (100, True),
    'email_from': (100, False),
    'privacy_policy': (100, True),
    'small_logo': (255, True),
    'large_logo': (255, True),
    'icon_logo': (255, True),
    'favicon': (255, False),
    'pwa_icon_192': (255, False),
    'pwa_icon_512': (255, False),
    'primary_colour': (7, False),
    'secondary_colour': (7, False),
    'iso_currency_code': (3, False),
    'stripe_api_publishable_key': (200, False),
    'stripe_api_secret_key': (200, False),
    'stripe_webhook_secret_key': (200, False),
}
_URL_FIELDS = ('url', 'system_url')
_COLOUR_FIELDS = ('primary_colour', 'secondary_colour')
_CURRENCY_RE = re.compile(r'^[A-Z]{3}$')
_URL_RE = re.compile(r'^https?://\S+', re.IGNORECASE)


def _validate_text(field, value):
    max_length, required = _TEXT_FIELDS[field]
    if value is not None and not isinstance(value, str):
        raise _InvalidField('{} must be text'.format(field), field)
    value = value.strip() if value is not None else None
    if not value:
        if required:
            raise _InvalidField('{} is required'.format(field), field)
        return None
    if len(value) > max_length:
        raise _InvalidField('{} must be at most {} characters'.format(field, max_length), field)
    if field in _URL_FIELDS and not _URL_RE.match(value):
        raise _InvalidField('{} must start with http:// or https://'.format(field), field)
    if field == 'email_from' and '@' not in value:
        raise _InvalidField('email_from must be an email address', field)
    if field in _COLOUR_FIELDS and not BRAND_COLOUR_RE.match(value):
        raise _InvalidField('{} must look like #1a2b3c'.format(field), field)
    if field == 'iso_currency_code' and not _CURRENCY_RE.match(value):
        raise _InvalidField('iso_currency_code must be three uppercase letters', field)
    return value


def _validate_languages(value):
    if not isinstance(value, list) or not value:
        raise _InvalidField('languages must be a non-empty list', 'languages')
    cleaned = []
    seen = set()
    for item in value:
        if not isinstance(item, dict):
            raise _InvalidField('Each language must have a code and description', 'languages')
        code = item.get('code')
        description = item.get('description')
        if not isinstance(code, str) or not code.strip() or \
                not isinstance(description, str) or not description.strip():
            raise _InvalidField('Each language must have a code and description', 'languages')
        code = code.strip()
        if code not in SUPPORTED_LANGUAGES:
            raise _InvalidField('Unsupported language code: {}'.format(code), 'languages')
        if code in seen:
            raise _InvalidField('Duplicate language code: {}'.format(code), 'languages')
        seen.add(code)
        cleaned.append({'code': code, 'description': description.strip()})
    return cleaned


def _validate_settings(body):
    """Returns the cleaned values for every key in body, or raises _InvalidField."""
    if not isinstance(body, dict):
        raise _InvalidField('Request body must be a JSON object', None)
    values = {}
    for field, value in body.items():
        if field == 'languages':
            values[field] = _validate_languages(value)
        elif field in _TEXT_FIELDS:
            values[field] = _validate_text(field, value)
        else:
            raise _InvalidField('{} cannot be set'.format(field), field)
    return values


class OrganisationSettingsApi(restful.Resource):
    @staticmethod
    def _settings(org):
        return {
            'id': org.id,
            'domain': org.domain,
            'name': org.name,
            'system_name': org.system_name,
            'url': org.url,
            'email_from': org.email_from,
            'system_url': org.system_url,
            'privacy_policy': org.privacy_policy,
            'languages': org.languages,
            'small_logo': org.small_logo,
            'large_logo': org.large_logo,
            'icon_logo': org.icon_logo,
            'favicon': org.favicon,
            'pwa_icon_192': org.pwa_icon_192,
            'pwa_icon_512': org.pwa_icon_512,
            'primary_colour': org.primary_colour,
            'secondary_colour': org.secondary_colour,
            'iso_currency_code': org.iso_currency_code,
            'stripe_api_publishable_key': org.stripe_api_publishable_key,
            'stripe_secret_key_set': bool(org.stripe_api_secret_key),
            'stripe_webhook_secret_key_set': bool(org.stripe_webhook_secret_key),
        }

    @org_admin_required
    def get(self):
        return self._settings(organisation_repository.get_by_id(g.organisation.id)), 200

    @org_admin_required
    def put(self):
        try:
            values = _validate_settings(request.get_json(silent=True))
        except _InvalidField as e:
            return _error(e.message, e.field)

        organisation = organisation_repository.get_by_id(g.organisation.id)
        for field, value in values.items():
            setattr(organisation, field, value)
        organisation_repository.save()

        OrganisationResolver.bust_cache()
        return self._settings(organisation), 200
