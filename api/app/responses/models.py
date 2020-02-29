
from app import db
from datetime import date

class Response(db.Model):

    __tablename__ = "response"

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(db.Integer(),db.ForeignKey("application_form.id"), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey("app_user.id"), nullable=False)
    is_submitted = db.Column(db.Boolean(), nullable=False)
    submitted_timestamp = db.Column(db.DateTime(), nullable=True)
    is_withdrawn = db.Column(db.Boolean(), nullable=False)
    withdrawn_timestamp = db.Column(db.DateTime(), nullable=True)
    started_timestamp = db.Column(db.DateTime(), nullable=True)
    nomination_title = db.Column(db.String(20), nullable=True)
    nomination_firstname = db.Column(db.String(100), nullable=True)
    nomination_lastname = db.Column(db.String(100), nullable=True)
    nomination_email = db.Column(db.String(255), nullable=True)

    application_form = db.relationship('ApplicationForm', foreign_keys=[application_form_id])
    user = db.relationship('AppUser', foreign_keys=[user_id])
    answers = db.relationship('Answer')

    @property
    def candidate_title(self):
        if self.application_form.nominations:
            return self.nomination_title
        else:
            return self.user.user_title

    @property
    def candidate_firstname(self):
        if self.application_form.nominations:
            return self.nomination_firstname
        else:
            return self.user.firstname

    @property
    def candidate_lastname(self):
        if self.application_form.nominations:
            return self.nomination_lastname
        else:
            return self.user.lastname

    @property
    def candidate_email(self):
        if self.application_form.nominations:
            return self.nomination_email
        else:
            return self.user.email

    def __init__(self, application_form_id, user_id, is_submitted=False, submitted_timestamp=None,
                 is_withdrawn=False, withdrawn_timestamp=None,
                 nomination_title=None, nomination_firstname=None, nomination_lastname=None, nomination_email=None,
                 ):
        self.application_form_id = application_form_id
        self.user_id = user_id
        self.is_submitted = is_submitted
        self.submitted_timestamp = submitted_timestamp
        self.is_withdrawn = is_withdrawn
        self.withdrawn_timestamp = withdrawn_timestamp
        self.started_timestamp = date.today()
        self.nomination_title = nomination_title
        self.nomination_firstname = nomination_firstname
        self.nomination_lastname = nomination_lastname
        self.nomination_email = nomination_email

    def submit_response(self):
        self.is_submitted = True
        self.submitted_timestamp = date.today()

    def withdraw_response(self):
        self.is_withdrawn = True
        self.withdrawn_timestamp = date.today()


class Answer(db.Model):

    __tablename__ = "answer"

    id = db.Column(db.Integer(), primary_key=True)
    response_id = db.Column(db.Integer(), db.ForeignKey("response.id"), nullable=False)
    question_id = db.Column(db.Integer(), db.ForeignKey("question.id"), nullable=False)
    value = db.Column(db.String(), nullable=False)

    response = db.relationship('Response', foreign_keys=[response_id])
    question = db.relationship('Question', foreign_keys=[question_id])

    def __init__(self, response_id, question_id, value):
        self.response_id = response_id
        self.question_id = question_id
        self.value = value
    
    @property
    def value_display(self):
        if self.question.type == 'multi-choice' and self.question.options is not None:
            option = [option for option in self.question.options if option['value'] == self.value]
            if option is not None:
                return option[0]['label']
        return self.value


class ResponseReviewer(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    response_id = db.Column(db.Integer(), db.ForeignKey('response.id'), nullable=False)
    reviewer_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)

    response = db.relationship('Response', foreign_keys=[response_id])
    user = db.relationship('AppUser', foreign_keys=[reviewer_user_id])

    def __init__(self, response_id, reviewer_user_id):
        self.response_id = response_id
        self.reviewer_user_id = reviewer_user_id
