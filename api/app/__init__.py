from flask import Flask
from flask_cors import CORS
import flask_restful as restful
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_redis import FlaskRedis
from utils.logger import Logger
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

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

# set optional bootswatch theme
app.config['FLASK_ADMIN_SWATCH'] = 'cosmo'
from applicationModel.models import Question, Section
from responses.models import Response, Answer
from users.models import UserCategory, AppUser
from events.models import Event, EventRole
admin = Admin(app, name='Deep Learning Indaba Admin Portal')


admin.add_view(ModelView(Question, db.session))
admin.add_view(ModelView(Section, db.session))
admin.add_view(ModelView(Response, db.session))
admin.add_view(ModelView(Answer, db.session))

admin.add_view(ModelView(Event, db.session))
admin.add_view(ModelView(EventRole, db.session))
admin.add_view(ModelView(UserCategory, db.session))


