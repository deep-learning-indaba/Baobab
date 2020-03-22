
from app import db
from datetime import date, datetime

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

    application_form = db.relationship('ApplicationForm', foreign_keys=[application_form_id])
    user = db.relationship('AppUser', foreign_keys=[user_id])
    answers = db.relationship('Answer')

    def __init__(self, application_form_id, user_id, is_submitted=False, submitted_timestamp=None,
                 is_withdrawn=False, withdrawn_timestamp=None):
        self.application_form_id = application_form_id
        self.user_id = user_id
        self.is_submitted = is_submitted
        self.submitted_timestamp = datetime.now() if is_submitted else submitted_timestamp
        self.is_withdrawn = is_withdrawn
        self.withdrawn_timestamp = withdrawn_timestamp
        self.started_timestamp = date.today()

    def submit(self):
        self.is_submitted = True
        self.submitted_timestamp = datetime.now()
        self.is_withdrawn = False
        self.withdrawn_timestamp = None

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

    def update(self, value):
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
    active = db.Column(db.Boolean(), nullable=False)

    response = db.relationship('Response', foreign_keys=[response_id])
    user = db.relationship('AppUser', foreign_keys=[reviewer_user_id])

    def __init__(self, response_id, reviewer_user_id):
        self.response_id = response_id
        self.reviewer_user_id = reviewer_user_id
        self.active = True

    def deactivate(self):
        self.active = False