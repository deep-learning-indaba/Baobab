
from app import db

class Event(db.Model):

    __tablename__ = "Event"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(255))
    startDate = db.Column(db.DateTime())
    endDate = db.Column(DateTime())
    

    def __init__(self, name, description, startDate, endDate):
        self.name = name
        self.description = description
        self.startDate = startDate
        self.endDate = endDate

    def setName(self, newName):
       self.name = newName

    def setDescription(self, newDescription):
       self.description = newDescription

    def setStartDate(self, newStartDate):
       self.startDate = newStartDate

    def setEndDate(self, newEndDate):
       self.endDate = newEndDate

class EventRole(db.Model):

    __tablename__ = "Event_Role"

    id = db.Column(db.Integer(), primary_key=True)
    eventID = db.Column(db.Integer(), db.ForeignKey("Event.event_id"))
    userID = db.Column(Integer(), db.ForeignKey("app_user.id"))
    role = db.Column(db.String(50))


    def __init__(self, role, userID, eventID):
        self.role = role
        self.userID = userID
        self.eventID = eventID        

    def setUser(self, newUserID):
       self.userID = newUserID

    def setEvent(self, newEventID):
       self.eventID = newEventID

    def setRole(self, newRole):
       self.role = newRole