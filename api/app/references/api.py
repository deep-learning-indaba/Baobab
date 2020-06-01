from datetime import datetime

from flask import g, request
import flask_restful as restful
from flask_restful import fields, marshal_with

from app import LOGGER

from app.applicationModel.models import ApplicationForm
from app.applicationModel.repository import ApplicationFormRepository as application_form_repository
from app.events.models import Event
from app.events.repository import EventRepository as event_repository
from app.utils.errors import EVENT_NOT_FOUND, USER_NOT_FOUND, RESPONSE_NOT_FOUND, FORBIDDEN,\
                        REFRERENCE_REQUEST_WITH_TOKEN_NOT_FOUND, DUPLICATE_REFERENCE_SUBMISSION,\
                        APPLICATIONS_CLOSED, REFERENCE_REQUEST_NOT_FOUND, BAD_CONFIGURATION

from app.utils.auth import auth_optional, auth_required
from app.utils.emailer import send_mail
from app.references.repository import ReferenceRequestRepository as reference_request_repository
from app.references.repository import ReferenceRepository as reference_repository
from app.references.models import ReferenceRequest, Reference
from app.references.mixins import ReferenceRequestsMixin, ReferenceRequestsListMixin, ReferenceRequestDetailMixin, \
    ReferenceMixin
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
    'reference_submitted': fields.Boolean(attribute='has_reference')
}

reference_request_details_fields = {
    'candidate': fields.String,
    'nominator': fields.String,
    'relation': fields.String,
    'name': fields.String,
    'description': fields.String,
    'is_application_open': fields.Boolean,
    'email_from': fields.String,
    'reference_submitted_timestamp': fields.DateTime,
    }

reference_fields = {
    'id': fields.Integer,
    'reference_request_id': fields.String,
    'uploaded_document': fields.String,
    'timestamp': fields.DateTime
}

def _get_candidate_nominator(response):
    nominating_capacity = response_repository.get_answer_by_question_key_and_response_id('nominating_capacity', response.id)
    if not nominating_capacity:
        raise ValueError('Missing nominating capacity answer')
    is_nomination = nominating_capacity.value == 'other'

    if is_nomination:
        question_answers = response_repository.get_question_answers_by_section_key_and_response_id(
            'nominee_section', response.id)
        
        nomination_info = {
            qa.Question.key: qa.Answer.value
            for qa in question_answers
        }
        candidate = '{nomination_title} {nomination_firstname} {nomination_lastname}'.format(**nomination_info)
        candidate_firstname = nomination_info['nomination_firstname']
        nominator = '{} {} {}'.format(response.user.user_title, response.user.firstname, response.user.lastname)
    else:
        candidate = '{} {} {}'.format(response.user.user_title, response.user.firstname, response.user.lastname)
        candidate_firstname = response.user.firstname
        nominator = None
    
    return candidate, candidate_firstname, nominator


class ReferenceRequestAPI(ReferenceRequestsMixin, restful.Resource):

    @marshal_with(reference_request_fields)
    @auth_required
    def get(self):
        args = self.get_req_parser.parse_args()
        return reference_request_repository.get_by_id(args['id']), 200

    @marshal_with(reference_request_fields)
    @auth_required
    def post(self):
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

        event = event_repository.get_event_by_response_id(response_id)
        if not event:
            return EVENT_NOT_FOUND
        
        response = response_repository.get_by_id(response_id)
        if not response:
            return RESPONSE_NOT_FOUND

        reference_request = ReferenceRequest(response_id=response_id,title=title,
                firstname=firstname, lastname=lastname, relation=relation, email=email)
        reference_request_repository.create(reference_request)

        link = "{host}/reference/{token}".format(host=misc.get_baobab_host(),
                                                 token=reference_request.token)

        try:
            candidate, candidate_firstname, nominator = _get_candidate_nominator(response)
        except ValueError as e:
            LOGGER.error(e)
            return BAD_CONFIGURATION

        if nominator is None:
            nomination_text = "has nominated themself"
        else:
            nomination_text = "has been nominated by {}".format(nominator)

        subject = 'REFERENCE REQUEST - {}'.format(event.name)
        body = REFERENCE_REQUEST_EMAIL_BODY.format(            
            title=title,
            firstname=firstname,
            lastname=lastname,
            candidate=candidate,
            candidate_firstname=candidate_firstname,
            nomination_text=nomination_text,
            event_name=event.name,
            event_url=event.url,
            application_close_date=event.application_close,
            link=link)
        send_mail(recipient=email, subject=subject, body_text=body)

        reference_request.set_email_sent(datetime.now())
        reference_request_repository.add(reference_request)
        return reference_request, 201


class ReferenceRequestListAPI(ReferenceRequestsListMixin, restful.Resource):

    @marshal_with(reference_request_fields)
    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        response = response_repository.get_by_id_and_user_id(args['response_id'], g.current_user['id'])
        if not response:
            return RESPONSE_NOT_FOUND

        return reference_request_repository.get_all_by_response_id(response.id), 200

class ReferenceRequestDetailAPI(ReferenceRequestDetailMixin, restful.Resource):

    @marshal_with(reference_request_details_fields)
    def get(self):
        args = self.post_req_parser.parse_args()
        token = args['token']

        reference_request = reference_request_repository.get_by_token(token)  # type: ReferenceRequest
        if not reference_request:
            return REFRERENCE_REQUEST_WITH_TOKEN_NOT_FOUND

        response_id = reference_request.response_id
        response = response_repository.get_by_id(response_id)  # type: Response
        if not response:
            return RESPONSE_NOT_FOUND

        event = event_repository.get_event_by_response_id(response_id)  # type: Event

        if not event:
            return EVENT_NOT_FOUND

        reference = reference_repository.get_by_reference_request_id(reference_request.id)
        app_form = event.get_application_form()  # type: ApplicationForm

        # Determine whether the response is a nomination
        try:
            candidate, _, nominator = _get_candidate_nominator(response)
        except ValueError as e:
            LOGGER.error(e)
            return BAD_CONFIGURATION

        return_object = {
            'candidate': candidate,
            'nominator': nominator,
            'relation': reference_request.relation,
            'name': event.name,
            'description': event.description,
            'is_application_open': event.is_application_open,
            'email_from': event.email_from,
            'reference_submitted_timestamp': reference.timestamp if reference is not None else None
        }

        return return_object, 200


REFERENCE_REQUEST_EMAIL_BODY="""
Dear {title} {firstname} {lastname},

{candidate} {nomination_text} for the {event_name} ({event_url}). 
In order for their application to be considered for the award, we require a reference letter from someone who knows {candidate_firstname} in a professional capacity, and they have selected you. 
Please use the upload link below to submit your reference letter for {candidate_firstname} by {application_close_date}. 
The reference letter should describe your relationship to {candidate_firstname}, how long you've known them, and should comment on the work {candidate_firstname} has done, and its worthiness of the {event_name}. 
Their application will NOT be considered if this reference letter is not submitted by the deadline

Please visit {link} to upload your reference by {application_close_date}

Kind regards,
The {event_name} team.
"""


class ReferenceAPI(ReferenceMixin, restful.Resource):

    @marshal_with(reference_fields)
    @auth_required
    def get(self):
        args = self.get_req_parser.parse_args()
        user = user_repository.get_by_id(g.current_user['id'])
        response = response_repository.get_by_id(args['response_id'])
        if not response:
            return RESPONSE_NOT_FOUND

        event = event_repository.get_event_by_response_id(response.id)

        if not user.is_event_admin(event.id):
            return FORBIDDEN
        reference_responses = reference_request_repository.get_references_by_response_id(response.id)
        return [reference_response.Reference for reference_response in reference_responses], 200

    def post(self):
        args = self.post_req_parser.parse_args()
        token = args['token']
        uploaded_document = args['uploaded_document']
        reference_request = reference_request_repository.get_by_token(token)
        event = event_repository.get_event_by_response_id(reference_request.response_id)

        if not reference_request:
            return REFRERENCE_REQUEST_WITH_TOKEN_NOT_FOUND

        if reference_request.has_reference:
            return DUPLICATE_REFERENCE_SUBMISSION

        if not event.is_application_open:
            return APPLICATIONS_CLOSED

        reference = Reference(reference_request_id=reference_request.id, uploaded_document=uploaded_document)
        reference_request_repository.add(reference)
        return {}, 201

    def put(self):
        args = self.put_req_parser.parse_args()
        token = args['token']
        uploaded_document = args['uploaded_document']
        reference_request = reference_request_repository.get_by_token(token)
        event = event_repository.get_event_by_response_id(reference_request.response_id)
        reference = reference_request_repository.get_reference_by_reference_request_id(reference_request.id)

        if not reference_request:
            return REFERENCE_REQUEST_NOT_FOUND

        if not event.is_application_open:
            return APPLICATIONS_CLOSED

        reference.uploaded_document = uploaded_document

        reference_request_repository.commit()

        return {}, 200
