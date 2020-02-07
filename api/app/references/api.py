from datetime import datetime

from flask import g, request
import flask_restful as restful
from flask_restful import fields, marshal_with

from app.events.models import Event
from app.events.repository import EventRepository as event_repository
from app import LOGGER
from app.utils.errors import EVENT_NOT_FOUND, USER_NOT_FOUND, RESPONSE_NOT_FOUND, FORBIDDEN,\
                        REFRERENCE_REQUEST_WITH_TOKEN_NOT_FOUND, DUPLICATE_REFERENCE_SUBMISSION

from app.utils.auth import auth_optional, auth_required
from app.utils.emailer import send_mail
from app.references.repository import ReferenceRequestRepository as reference_request_repository
from app.references.models import ReferenceRequest, Reference
from app.references.mixins import ReferenceRequestsMixin, ReferenceRequestsListMixin, ReferenceMixin
from app.utils import misc
from app.users.repository import UserRepository as user_repository
from app.responses.repository import ResponseRepository as response_repository

reference_request_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'firstname': fields.String,
    'lastname': fields.String,
    'relation': fields.String,
    'email_sent': fields.DateTime,
    'response_id': fields.Integer,
    'email': fields.String,
    'reference_submitted' : fields.Boolean
}

reference_fields = {
    'id': fields.Integer,
    'reference_request_id': fields.String,
    'uploaded_document': fields.String,
    'timestamp': fields.DateTime
}

class ReferenceRequestAPI(ReferenceRequestsMixin, restful.Resource):

    @marshal_with(reference_request_fields)
    @auth_required
    def get(self):
        LOGGER.debug('Received get request for reference-request')
        args = self.get_req_parser.parse_args()
        return reference_request_repository.get_by_id(args['id']), 200

    @auth_required
    def post(self):
        LOGGER.debug('Received post request for reference-request')
        args = self.post_req_parser.parse_args()
        response_id = args['response_id']
        title = args['title']
        firstname = args['firstname']
        lastname = args['lastname']
        relation = args['relation']
        email = args['email']
        user = user_repository.get_by_id(g.current_user['id'])

        if not user:
            return USER_NOT_FOUND

        response_event = event_repository.get_event_by_response_id(response_id)
        if not response_event or not response_event.Event:
            return EVENT_NOT_FOUND
        event = response_event.Event
        reference_request = ReferenceRequest(response_id=response_id,title=title, 
                                        firstname=firstname, lastname=lastname, relation=relation, email=email)
        reference_request_repository.create(reference_request)

        link = "{host}/{key}/reference?token={token}".format(host=misc.get_baobab_host(), 
                                                            key=event.key, token=reference_request.token)
        
        subject = 'REFERENCE REQUEST - {}'.format(event.name)
        body = REFERENCE_REQUEST_EMAIL_BODY.format(title=title, firstname=firstname, 
                                        lastname=lastname, event_description=event.description, 
                                        link=link, candidate_firstname=user.firstname, 
                                        candidate_lastname=user.lastname,
                                        application_close_date=event.application_close)
        send_mail(recipient=email, subject=subject, body_text=body)

        reference_request.set_email_sent(datetime.now())
        reference_request_repository.add(reference_request)
        return {}, 201

    
class ReferenceRequestListAPI(ReferenceRequestsListMixin, restful.Resource):

    @marshal_with(reference_request_fields)
    @auth_required
    def get(self):
        LOGGER.debug('Received get request for reference-request')
        user = user_repository.get_by_id(g.current_user['id'])
        if not user:
            return USER_NOT_FOUND

        args = self.req_parser.parse_args()
        response = response_repository.get_by_id_and_user_id(args['response_id'], user.id)
        if not response:
            return RESPONSE_NOT_FOUND

        return reference_request_repository.get_all_by_response_id(response.id), 200


REFERENCE_REQUEST_EMAIL_BODY="""
Dear {title} {firstname} {lastname},

{candidate_firstname} {candidate_lastname} has requested your reference for their application for the {event_description}.

Please visit {link} to upload your reference by {application_close_date}

Kind regards,
The {event_description} team.
"""


class ReferenceAPI(ReferenceMixin, restful.Resource):

    @marshal_with(reference_fields)
    @auth_required
    def get(self):
        LOGGER.debug('Received get request for reference')
        user = user_repository.get_by_id(g.current_user['id'])
        if not (user or user.is_admin):
            return FORBIDDEN

        args = self.get_req_parser.parse_args()
        response = response_repository.get_by_id_and_user_id(args['response_id'], user.id)
        if not response:
            return RESPONSE_NOT_FOUND

        reference_responses = reference_request_repository.get_reference_by_response_id(response.id)
        return [reference_response.Reference for reference_response in reference_responses], 200

    def post(self):
        LOGGER.debug('Received post request for reference')
        args = self.post_req_parser.parse_args()
        token = args['token']
        uploaded_document = args['uploaded_document']
        reference_request = reference_request_repository.get_by_token(token)
        if not reference_request:
            return REFRERENCE_REQUEST_WITH_TOKEN_NOT_FOUND

        reference = reference_request_repository.get_reference_by_reference_request_id(reference_request.id)
        if reference:
            return DUPLICATE_REFERENCE_SUBMISSION
        
        reference_request.set_reference_submitted()
        reference = Reference(reference_request_id=reference_request.id, uploaded_document=uploaded_document)
        reference_request_repository.add(reference)
        reference_request_repository.add(reference_request)
        return {}, 201
