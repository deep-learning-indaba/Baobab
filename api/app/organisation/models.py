from app import db

class Organisation(db.Model):

    __tablename__ = "organisation"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    small_logo = db.Column(db.String(100), nullable=False)
    large_logo = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(100), nullable=False)

    def __init__(self, name, small_logo, large_logo, domain):
        self.name = name
        self.small_logo = small_logo
        self.large_logo = large_logo
        self.domain = domain
