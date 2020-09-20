from datetime import datetime

import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with

from app.users.models import Country, UserCategory
from app import db


country_fields = {
    'value': fields.Integer(attribute='id'),
    'label': fields.String(attribute='name')
}

category_fields = {
    'value': fields.Integer(attribute='id'),
    'label': fields.String(attribute='name')
}


class CountryContentAPI(restful.Resource):
    # DEPRECATED - TODO: REMOVE
    @marshal_with(country_fields)
    def get(self):
        countries = db.session.query(Country).order_by(Country.id).all()
        return countries


class CategoryContentAPI(restful.Resource):
    # DEPRECATED - TODO: REMOVE
    @marshal_with(category_fields)
    def get(self):
        countries = db.session.query(
            UserCategory).order_by(UserCategory.id).all()
        return countries


class EthnicityContentAPI(restful.Resource):
    # DEPRECATED - TODO: REMOVE
    def get(self):
        return [
            {"label": "Black", "value": 'black'},
            {"label": "Coloured / Mixed Descent", "value": 'coloured/mixed'},
            {"label": "White", "value": 'white'},
            {"label": "Indian Descent", "value": 'indian'},
            {"label": "Other", "value": "other"}
        ]


class TitleContentAPI(restful.Resource):
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('language', type=str, required=True)
        args = req_parser.parse_args()
        language = args['language']

        if language == 'fr':
            return [
                {"value": "M.", "label": "M."},
                {"value": "Mme", "label": "Mme"},
                {"value": "Mlle", "label": "Mlle"},
                {"value": "Dr", "label": "Dr"},
                {"value": "Pr", "label": "Pr"}
            ]

        # Default to English if not another known language
        return [
            {"value": "Mr", "label": "Mr"},
            {"value": "Mrs", "label": "Mrs"},
            {"value": "Ms", "label": "Ms"},
            {"value": "Hon", "label": "Hon"},
            {"value": "Prof", "label": "Prof"},
            {"value": "Dr", "label": "Dr"},
            {"value": "Mx", "label": "Mx"}
        ]


class GenderContentAPI(restful.Resource):
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('language', type=str, required=True)
        args = req_parser.parse_args()
        language = args['language']

        if language == 'fr':
            {"value": "male", "label": "Homme"},
            {"value": "female", "label": "Femme"},
            {"value": "other", "label": "Autre"},
            {"value": "prefer_not_to_say", "label": "Je préfère ne pas le dire"}

        # Default to English if not another known language
        return [
            {"value": "male", "label": "Male"},
            {"value": "female", "label": "Female"},
            {"value": "other", "label": "Other"},
            {"value": "prefer_not_to_say", "label": "Prefer not to say"}
        ]


class DisabilityContentAPI(restful.Resource):
    # DEPRECATED - TODO: REMOVE
    def get(self):
        return[
            {"label": "No disabilities", "value": "none"},
            {"label": "Sight disability", "value": "sight"},
            {"label": "Hearing disability", "value": "hearing"},
            {"label": "Communication disability", "value": "communication"},
            {"label": "Physical disability(e.g. difficulty in walking)",
             "value": "physical"},
            {"label": "Mental disability(e.g. difficulty in remembering or concentrating)",
             "value": "mental"},
            {"label": "Difficulty in self-care", "value": "self-care"},
            {"label": "Other", "value": "other"},
        ]
