
from app import db

class Event(db.Model):

    __tablename__ = "event"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.DateTime(), nullable=False)
    end_date = db.Column(db.DateTime(), nullable=False)
    

    def __init__(self, name, description, start_date, end_date):
        self.name = name
        self.description = description
        self.start_date = start_date
        self.end_date = end_date

    def set_name(self, new_name):
       self.name = new_name

    def set_description(self, new_description):
       self.description = new_description

    def set_start_date(self, new_start_date):
       self.start_date = new_start_date

    def set_end_date(self, new_end_date):
       self.end_date = new_end_date

class EventRole(db.Model):

    __tablename__ = "event_role"

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey("event.id"), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey("app_user.id"), nullable=False)
    role = db.Column(db.String(50), nullable=False)


    def __init__(self, role, user_id, event_id):
        self.role = role
        self.user_id = user_id
        self.event_id = event_id        

    def set_user(self, new_user_id):
       self.user_id = new_user_id

    def set_event(self, new_event_id):
       self.event_id = new_event_id

    def set_role(self, new_role):
       self.role = new_role