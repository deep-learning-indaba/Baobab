import unittest

from app import db, app
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection
from app.organisation.models import Organisation


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class ApiTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        self.app = app.test_client()
        db.reflect()
        db.drop_all()
        db.create_all()
        
        # Add a dummy organisation
        organisation = Organisation('My Org', 'org.png', 'org_big.png', 'org')
        db.session.add(organisation)
        db.session.commit()
        db.session.flush()

    def tearDown(self):
        db.session.remove()
        db.reflect()
        db.drop_all()