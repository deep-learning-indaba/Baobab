from app import db

class Organisation(db.Model):

    __tablename__ = "organisation"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    system_name = db.Column(db.String(50), nullable=False)
    small_logo = db.Column(db.String(100), nullable=False)
    large_logo = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(100), nullable=False)

    events = db.relationship('Event')

    def __init__(self, name, system_name, small_logo, large_logo, domain, url):
        self.name = name
        self.small_logo = small_logo
        self.large_logo = large_logo
        self.domain = domain
        self.system_name = system_name
        self.url = url
