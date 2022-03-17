import flask_restful as restful
from flask import g, request
from flask_restful import fields, marshal, marshal_with, reqparse

from app import LOGGER


class OrganisationApi(restful.Resource):
    organisation_fields = {
        "id": fields.Integer,
        "name": fields.String,
        "small_logo": fields.String,
        "large_logo": fields.String,
        "icon_logo": fields.String,
        "domain": fields.String,
        "system_name": fields.String,
        "url": fields.String,
        "email_from": fields.String,
        "system_url": fields.String,
        "privacy_policy": fields.String,
        "languages": fields.Raw,
    }

    @marshal_with(organisation_fields)
    def get(self):
        return g.organisation
