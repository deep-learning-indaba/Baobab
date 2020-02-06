
from datetime import datetime

from app import db

class ReferenceRequest(db.Model):

    __tablename__ = "reference_request"

    id = db.Column(db.Integer(), primary_key=True)
    response_id = db.Column(db.Integer(), db.ForeignKey('response.id'), nullable=False)
    title = db.Column(db.String(50), nullable=False)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    relation = db.Column(db.String(50), nullable=False)
    token = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=True)
    email_sent = db.Column(db.DateTime(), nullable=True)


    response = db.relationship('Response', foreign_keys=[response_id])

    def __init__(self, 
                response_id, 
                title,
                firstname,
                lastname, 
                relation,
                email
                 ):
        self.response_id = response_id
        self.title = title
        self.firstname = firstname
        self.lastname = lastname
        self.relation = relation
        self.email = email

    def set_email_sent(self, email_sent):
        self.email_sent = email_sent

    def set_token(self, token):
        self.token = token



class Reference(db.Model):

    __tablename__ = "reference"

    id = db.Column(db.Integer(), primary_key=True)
    reference_request_id = db.Column(db.Integer(), db.ForeignKey('reference_request.id'), nullable=False)
    uploaded_document = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime(), nullable=True)

    def __init__(self, reference_request_id, uploaded_document, timestamp):
        self.reference_request_id = reference_request_id
        self.uploaded_document = uploaded_document
        self.timestamp = timestamp