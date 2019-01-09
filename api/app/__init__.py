from flask import Flask
from flask.ext import restful
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager
from flask_redis import Redis


app = Flask(__name__)
app.config.from_object('config')
print(app.config['SQLALCHEMY_DATABASE_URI'])
rest_api = restful.Api(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
redis = Redis(app)


import routes


migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)
