from app import db
from app.references.models import ReferenceRequest
from app.events.models import Event
import uuid


class ReferenceRequestRepository():
    
    @staticmethod
    def get_by_id(reference_request_id):
        return db.session.query(ReferenceRequest).get(reference_request_id)

    @staticmethod
    def get_all():
        return db.session.query(ReferenceRequest).all()

    @staticmethod
    def create(reference_request):
        reference_request.set_token(str(uuid.uuid4()))
        db.session.add(reference_request)
        db.session.commit()
    
    @staticmethod
    def add(obj_to_commit):
        db.session.add(obj_to_commit)
        db.session.commit()

    @staticmethod
    def get_all_by_response_id(response_id):
        return db.session.query(ReferenceRequest)\
                         .filter_by(response_id=response_id)\
                         .all()

    @staticmethod
    def get_by_token(token):
        return db.session.query(ReferenceRequest)\
                         .filter_by(token=token)\
                         .first()

    @staticmethod
    def get_reference_by_response_id(response_id):
        return db.session.query(ReferenceRequest.response_id, Reference)\
                         .join(ReferenceRequest, ReferenceRequest.id == Reference.reference_request_id)\
                         .filter_by(ReferenceRequest.response_id=response_id)\
                         .all()