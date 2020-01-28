from app import db
from app.references.models import ReferenceRequest
from app.responses.models import Response
from app.applicationModel.models import ApplicationForm
from app.events.models import Event
import uuid


class ReferenceRequestRepository():
    
    @staticmethod
    def get_by_id(reference_request_id):
        return db.session.query(ReferenceRequest).get(reference_request_id)

    @staticmethod
    def get_event_by_response_id(response_id):
        return db.session.query(Response.application_form_id, ApplicationForm.event_id, Event)\
                         .filter_by(id=response_id)\
                         .join(ApplicationForm, ApplicationForm.id == Response.application_form_id)\
                         .join(Event, Event.id == ApplicationForm.event_id)\
                         .first()

    @staticmethod
    def create(reference_request):
        reference_request.set_token(str(uuid.uuid4()))
        db.session.add(reference_request)
        db.session.commit()
    
    @staticmethod
    def update(reference_request):
        db.session.add(reference_request)
        db.session.commit()

    @staticmethod
    def get_all_by_response_id(response_id):
        return db.session.query(ReferenceRequest)\
                         .filter_by(response_id=response_id)\
                         .all()