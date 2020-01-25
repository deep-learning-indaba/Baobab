import unittest

from datetime import datetime
from app import db, app
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection
from app.organisation.models import Organisation
from app.users.models import AppUser, UserCategory, Country


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class ApiTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(ApiTestCase, self).__init__(*args, **kwargs)
        self.test_users = []
    
    def add_user(self, 
                 email='user@user.com', 
                 firstname='User', 
                 lastname='Lastname', 
                 user_title='Mrs',
                 nationality_country_id=1,
                 residence_country_id=1,
                 user_gender='female',
                 affiliation='university X',
                 department='Computer science',
                 user_disability='None',
                 user_category_id=1,
                 user_dateOfBirth=None,
                 user_primaryLanguage='Swahili',
                 password='abc',
                 organisation_id=1,
                 is_admin=False,
                 post_create_fn=lambda x: None):
        user_dateOfBirth = user_dateOfBirth or datetime(1984, 12, 12)
        user = AppUser(email,
                 firstname,
                 lastname,
                 user_title,
                 nationality_country_id,
                 residence_country_id,
                 user_gender,
                 affiliation,
                 department,
                 user_disability,
                 user_category_id,
                 user_dateOfBirth,
                 user_primaryLanguage,
                 password,
                 organisation_id,
                 is_admin)
        user.verify()

        post_create_fn(user)

        db.session.add(user)
        self.test_users.append(user)
        return user

    def setUp(self):
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        self.app = app.test_client()
        db.reflect()
        db.drop_all()
        db.create_all()

        # Add dummy metadata
        self.user_category = UserCategory('Postdoc')
        db.session.add(self.user_category)
        self.country = Country('South Africa')
        db.session.add(self.country)

        # Add a dummy organisation
        organisation = Organisation(name='My Org', system_name='Baobab', small_logo='org.png', 
                                    large_logo='org_big.png', domain='org', url='www.org.net')
        db.session.add(organisation)
        db.session.commit()
        db.session.flush()

    def tearDown(self):
        db.session.remove()
        db.reflect()
        db.drop_all()