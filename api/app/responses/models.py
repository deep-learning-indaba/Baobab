
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
    

    def __init__(self, application_form_id, user_id, is_submitted = False, submitted_timestamp = None, is_withdrawn = False, withdrawn_timestamp = None):
        self.application_form_id = application_form_id
        self.user_id = user_id
        self.is_submitted = is_submitted
        self.submitted_timestamp = submitted_timestamp
        self.is_withdrawn = is_withdrawn
        self.withdrawn_timestamp = withdrawn_timestamp
        self.started_timestamp = date.today().strftime('%Y/%m/%d')

    def submit_response(self):
       self.is_submitted = True
       self.submitted_timestamp = date.today().strftime('%Y/%m/%d')

    def withdraw_response(self):
       self.is_withdrawn = True
       self.withdrawn_timestamp = date.today().strftime('%Y/%m/%d')

class Answer(db.Model):

    __tablename__ = "answer"

    id = db.Column(db.Integer(), primary_key=True)
    response_id = db.Column(db.Integer(), db.ForeignKey("response.id"), nullable=False)
    question_id = db.Column(db.Integer(), db.ForeignKey("question.id"), nullable=False)
    value = db.Column(db.String(), nullable=False)


    def __init__(self, response_id, question_id, value):
        self.response_id = response_id
        self.question_id = question_id
        self.value = value

