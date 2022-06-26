from app import db
from app.organisation.models import Organisation


class OrganisationRepository():

    @staticmethod
    def get_by_id(organisation_id):
        return db.session.query(Organisation).get(organisation_id)

    @staticmethod
    def get_by_domain(domain):
        return db.session.query(Organisation).Filter(Organisation.domain == domain).one_or_none()

    @staticmethod
    def get_all():
        return db.session.query(Organisation).all()
