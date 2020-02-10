from flask_restful import reqparse
import flask_restful as restful
from flask import request, g
from flask_restful import fields, marshal_with, marshal

from app import LOGGER

class OrganisationApi(restful.Resource):
    organisation_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'small_logo': fields.String,
        'large_logo': fields.String,
        'domain': fields.String,
        'system_name': fields.String,
        'url': fields.String,
        'email_from': fields.String,
        'system_url': fields.String,
        'privacy_policy': fields.String
    }

    @marshal_with(organisation_fields)
    def get(self):
        return g.organisation
