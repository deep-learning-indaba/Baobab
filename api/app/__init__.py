from flask import Flask
from flask_cors import CORS
import flask_restful as restful
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_redis import FlaskRedis
from utils.logger import Logger

app = Flask(__name__)
app.config.from_object('config')
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
print(app.config['SQLALCHEMY_DATABASE_URI'])
rest_api = restful.Api(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
redis = FlaskRedis(app)
LOGGER = Logger().get_logger()


import routes

migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)
