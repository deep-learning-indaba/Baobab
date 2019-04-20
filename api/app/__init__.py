from flask import Flask, g, url_for, redirect, render_template, request, flash
from flask_cors import CORS
import flask_restful as restful
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_redis import FlaskRedis
from utils.logger import Logger
from flask_admin import Admin, AdminIndexView, helpers, expose
from flask_admin.contrib.sqla import ModelView
import flask_login as login
from wtforms import form, fields, validators
from werkzeug.security import generate_password_hash, check_password_hash

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
app.config['FLASK_ADMIN_SWATCH'] = 'darkly'
from applicationModel.models import Question, Section
from responses.models import Response, Answer, ResponseReviewer
from users.models import UserCategory, AppUser, UserComment
from events.models import Event, EventRole
from app.utils.auth import auth_required, admin_required, generate_token
from app.utils.errors import UNAUTHORIZED, FORBIDDEN
from reviews.models import ReviewForm, ReviewQuestion

# Define login and registration forms (for flask-login)
class LoginForm(form.Form):
    email = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate(self):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')


        if not bcrypt.check_password_hash(user.password, self.password.data):
            raise validators.ValidationError('Invalid password')

        if not user.is_admin:
            raise validators.ValidationError("Adminstrator rights required")

        LOGGER.debug("Successful authentication for email: {}".format(self.email.data))
        return True

    def get_user(self):
        return db.session.query(AppUser).filter(AppUser.email==self.email.data).first()

# Initialize flask-login
def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(AppUser).get(user_id)



# Create customized index view class that handles login & registration
class BaobabAdminIndexView(AdminIndexView):

    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(BaobabAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        try:

            # handle user login
            form = LoginForm(request.form)
            if request.method == 'POST': 
                if form.validate():
                    user = form.get_user()
                    login.login_user(user)

                if login.current_user.is_authenticated:
                    return redirect(url_for('.index'))
        except validators.ValidationError as error:
            flash(str(error))

        self._template_args['form'] = form
        return super(BaobabAdminIndexView, self).index()


    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))

# Initialize flask-login
init_login()

admin = Admin(app, name='Deep Learning Indaba Admin Portal', index_view=BaobabAdminIndexView(), template_mode='bootstrap3')


class BaobabModelView(ModelView):
    def is_accessible(self):
        return login.current_user.is_authenticated and login.current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('admin.login_view', next=request.url))

admin.add_view(BaobabModelView(Question, db.session))
admin.add_view(BaobabModelView(Section, db.session))
admin.add_view(BaobabModelView(Response, db.session))
admin.add_view(BaobabModelView(Answer, db.session))

admin.add_view(BaobabModelView(Event, db.session))
admin.add_view(BaobabModelView(EventRole, db.session))
admin.add_view(BaobabModelView(UserCategory, db.session))
admin.add_view(BaobabModelView(AppUser, db.session))

admin.add_view(BaobabModelView(ResponseReviewer, db.session))
admin.add_view(BaobabModelView(UserComment, db.session))
admin.add_view(BaobabModelView(ReviewForm, db.session))
admin.add_view(BaobabModelView(ReviewQuestion, db.session))
