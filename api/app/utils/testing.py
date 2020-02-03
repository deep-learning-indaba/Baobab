import unittest

import json
from datetime import datetime,timedelta
from app import db, app
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection
from app.organisation.models import Organisation
from app.users.models import AppUser, UserCategory, Country
from app.events.models import Event


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
                 password='abc',
                 organisation_id=1,
                 is_admin=False,
                 post_create_fn=lambda x: None):
        user = AppUser(email,
                 firstname,
                 lastname,
                 user_title,
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
        self.add_organisation(domain='org')
        db.session.flush()

    def add_organisation(self, name='My Org', system_name='Baobab', small_logo='org.png', 
                                    large_logo='org_big.png', domain='com', url='www.org.com',
                                    email_from='contact@org.com', system_url='baobab.deeplearningindaba.com'):
        org = Organisation(name, system_name, small_logo, large_logo, domain, url, email_from, system_url)
        db.session.add(org)
        db.session.commit()
        return org

    def add_event(self, 
                 name ='Test Event', 
                 description = 'Event Description', 
                 start_date = datetime.now() + timedelta(days=30), 
                 end_date = datetime.now() + timedelta(days=60),
                 key = 'INDABA2025', 
                 organisation_id = 1, 
                 email_from = 'abx@indaba.deeplearning', 
                 url = 'indaba.deeplearning',
                 application_open = datetime.now(),
                 application_close = datetime.now() + timedelta(days=10),
                 review_open = datetime.now() ,
                 review_close = datetime.now() + timedelta(days=15),
                 selection_open = datetime.now(),
                 selection_close = datetime.now() + timedelta(days=15),
                 offer_open = datetime.now(),
                 offer_close = datetime.now(),
                 registration_open = datetime.now(),
                 registration_close = datetime.now() + timedelta(days=15)):

        event = Event(name, description, start_date,  end_date, key,  organisation_id,  email_from,  url, 
                      application_open, application_close, review_open, review_close, selection_open, 
                      selection_close, offer_open,  offer_close, registration_open, registration_close)
        db.session.add(event)
        db.session.commit()
        return event

    def get_auth_header_for(self, email, password='abc'):
        body = {
            'email': email,
            'password': password
        }
        response = self.app.post('api/v1/authenticate', data=body)
        data = json.loads(response.data)
        header = {'Authorization': data['token']}
        return header

    def add_to_db(self, obj):
        db.session.add(obj)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.reflect()
        db.drop_all()