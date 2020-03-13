from app import db
from app.references.models import ReferenceRequest, Reference
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
    def commit():
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
                         .filter_by(response_id=ReferenceRequest.response_id)\
                         .all()

    @staticmethod
    def get_reference_by_reference_request_id(reference_request_id):
        return db.session.query(Reference)\
                         .filter_by(reference_request_id=Reference.reference_request_id)\
                         .first()


class ReferenceRepository():

    @staticmethod
    def get_by_id(reference_id):
        return db.session.query(Reference).get(reference_id)

    @staticmethod
    def get_all():
        return db.session.query(Reference).all()

    @staticmethod
    def add(reference):
        db.session.add(reference)
        db.session.commit()

    @staticmethod
    def get_by_response_id(response_id):
        return db.session.query(ReferenceRequest.response_id, Reference)\
            .join(ReferenceRequest, ReferenceRequest.id == Reference.reference_request_id)\
            .filter_by(response_id=ReferenceRequest.response_id)\
            .all()

    @staticmethod
    def get_by_reference_request_id(reference_request_id):
        return db.session.query(Reference)\
            .filter_by(reference_request_id=Reference.reference_request_id)\
            .first()
