import unittest
import unicodedata

import json
import random
import os
import six
from datetime import datetime,timedelta

from sqlalchemy.exc import ProgrammingError

from app import db, app, LOGGER
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection
from app.organisation.models import Organisation
from app.users.models import AppUser, UserCategory, Country
from app.events.models import Event
from app.events.models import EventType
from app.applicationModel.models import ApplicationForm


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

titles = ('Mr', "Ms", 'Mrs', 'Dr', 'Prof', 'Rev', 'Mx')

def strip_accents(text):
    """
    Strip accents from input.
    Helper function to create 'clean' emails
        see https://stackoverflow.com/a/518232/5209000

    :param text: The input string.
    :type text: String.

    :returns: The processed String.
    :rtype: String.
    """
    text = six.ensure_text(text)
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    return str(text)

class ApiTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(ApiTestCase, self).__init__(*args, **kwargs)
        self.test_users = []
        self.firstnames = []
        self.lastnames = []

    def _get_names(self):
        """Retrieve a list of names from a text file for testing"""
        if len(self.firstnames):
            return self.firstnames, self.lastnames

        if os.path.exists("/code/api/app/utils/names.txt"):
            with open("/code/api/app/utils/names.txt") as file_with_names:
                names = file_with_names.readlines()
        else:
            # why yes, these are names of African Hollywood actors (according to Wikipedia)
            names = ["Mehcad Brooks", "Malcolm Barrett", "Nick Cannon", "Lamorne Morris", "Neil Brown Jr.",
                     "William Jackson Harper", "Marques Houston", "Jennifer Hudson", "Alicia Keys", "Meghan Markle",
                     "Beyonce Knowles", "Jesse Williams", "Lance Gross", "Hosea Chanchez", "Daveed Diggs",
                     "Damon Wayans Jr.", "Columbus Short", "Terrence Jenkins", "Ron Funches", "Jussie Smollett",
                     "Donald Glover", "Brian Tyree Henry", "Gabourey Sidibe", "Trai Byers", "Robert Ri'chard",
                     "Arjay Smith", "Tessa Thompson", "J.Lee", "Lauren London", "DeVaughn Nixon", "Rob Brown", ]
        for _name in names:
            split_name = _name.strip().split(" ")
            self.firstnames.append(split_name[0])
            lastname = " ".join(split_name[1:]) if len(split_name) > 1 else ""
            self.lastnames.append(lastname)
        return self.firstnames, self.lastnames

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
        db.session.commit()
        self.test_users.append(user)
        return user

    def add_n_users(self, n,
                    password='abcd',
                    organisation_id=1,
                    is_admin=False,
                    post_create_fn=lambda x: None):
        firstnames, lastnames = self._get_names()

        users = []

        for i in range(n):
            title = random.choice(titles)
            firstname = random.choice(firstnames)
            lastname = random.choice(lastnames)
            email = "{firstname}.{lastname}{num}@bestemail.com".format(firstname=firstname,
                                                                       lastname=lastname if lastname != "" else "x",
                                                                       num=len(self.test_users))
            email = strip_accents(email)
            try:
                user = self.add_user(email, firstname, lastname, title, password, organisation_id, is_admin, post_create_fn)
                users.append(user)
            except ProgrammingError as err:
                LOGGER.debug("info not added for user: {} {} {} {}".format(email, firstname, lastname, title))
                db.session.rollback()

        return users

    def setUp(self):
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        self.app = app.test_client()
        db.reflect()
        db.drop_all()
        db.create_all()
        LOGGER.setLevel('ERROR')

        # Add dummy metadata
        self.user_category = UserCategory('Postdoc')
        db.session.add(self.user_category)
        self.country = Country('South Africa')
        db.session.add(self.country)

        # Add a dummy organisation
        dummy_org = self.add_organisation(domain='org')
        db.session.flush()
        self.dummy_org_id = dummy_org.id

    def add_organisation(self, name='My Org', system_name='Baobab', small_logo='org.png', 
                                    large_logo='org_big.png', domain='com', url='www.org.com',
                                    email_from='contact@org.com', system_url='baobab.deeplearningindaba.com',
                                    privacy_policy='PrivacyPolicy.pdf'):
        org = Organisation(name, system_name, small_logo, large_logo, domain, url, email_from, system_url, privacy_policy)
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
                 registration_close = datetime.now() + timedelta(days=15),
                 event_type = EventType.EVENT):

        event = Event(name, description, start_date,  end_date, key,  organisation_id,  email_from,  url, 
                      application_open, application_close, review_open, review_close, selection_open, 
                      selection_close, offer_open,  offer_close, registration_open, registration_close, event_type)
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

    def create_application_form(self,
                            event_id = 1,
                            is_open = True,
                            nominations = False):
                            
        application_form = ApplicationForm(event_id, is_open, nominations)
        db.session.add(application_form)
        db.session.commit()
        return application_form
