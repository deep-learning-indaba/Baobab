from flask import Flask, g, url_for, redirect, render_template, request, flash
from flask_cors import CORS
import flask_restful as restful
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_redis import FlaskRedis
from .utils.logger import Logger
from flask_admin import Admin, AdminIndexView, helpers, expose
from flask_admin.contrib.sqla import ModelView
import flask_login as login
from wtforms import form, fields, validators
from werkzeug.security import generate_password_hash, check_password_hash
import tldextract

app = Flask(__name__)
app.config.from_object('config')
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
print((app.config['SQLALCHEMY_DATABASE_URI']))
rest_api = restful.Api(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
redis = FlaskRedis(app)
LOGGER = Logger().get_logger()

from . import routes

migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

from .organisation.resolver import OrganisationResolver

def get_domain():
    # TODO: Remove this test-related hack!
    if app.config['TESTING'] and 'HTTP_ORIGIN' not in request.environ and 'HTTP_REFERER' not in request.environ:
        return 'org'

    origin = request.environ.get('HTTP_ORIGIN', '')
    if not origin:  # Try to get from Referer header
        origin = request.environ.get('HTTP_REFERER', '')
        LOGGER.debug('No ORIGIN header, falling back to Referer: {}'.format(origin))
    
    if origin:
        domain = tldextract.extract(origin).domain
    else:
        LOGGER.warning('Could not determine origin domain')
        domain = ''
    
    return domain

def get_signed_payload_and_signature():
    signature = request.environ.get('HTTP_STRIPE_SIGNATURE')
    elements = signature.split(',')
    elements_dict = {}
    for elem in elements:
        key, val = elem.split('=')
        elements_dict[key] = val
    
    signed_payload = f"{elements_dict['t']}.{request.data.decode('utf-8')}"
    expected_signature = elements_dict['v1']
    return signed_payload, expected_signature

def is_from_stripe():
    stripe_user_agent = 'Stripe/1.0 (+https://stripe.com/docs/webhooks)'
    return request.environ.get('HTTP_USER_AGENT') == stripe_user_agent

@app.before_request
def populate_organisation():
    if is_from_stripe():
        signed_payload, expected_signature = get_signed_payload_and_signature()
        g.organisation = OrganisationResolver.resolve_from_stripe_signature(
            signed_payload,
            expected_signature
        )
    else:
        domain = get_domain()
        LOGGER.info('Origin Domain: {}'.format(domain))  # TODO: Remove this after testing
        g.organisation = OrganisationResolver.resolve_from_domain(domain)

## Flask Admin Config

# set optional bootswatch theme
app.config['FLASK_ADMIN_SWATCH'] = 'darkly'
from .applicationModel.models import Question, Section
from .responses.models import Response, Answer, ResponseReviewer
from .users.models import UserCategory, AppUser, UserComment
from .email_template.models import EmailTemplate
from .outcome.models import Outcome
from .events.models import Event, EventRole
from app.utils.auth import auth_required, admin_required, generate_token
from app.utils.errors import UNAUTHORIZED, FORBIDDEN
from .reviews.models import ReviewForm, ReviewQuestion
from .registration.models import Offer, RegistrationForm, RegistrationSection, RegistrationQuestion, Registration, RegistrationAnswer
from .invitationletter.models import InvitationTemplate, InvitationLetterRequest
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
        # TODO: What organisation should we use to query here?
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
admin.add_view(BaobabModelView(Offer, db.session))
admin.add_view(BaobabModelView(RegistrationForm, db.session))
admin.add_view(BaobabModelView(RegistrationSection, db.session))
admin.add_view(BaobabModelView(RegistrationQuestion, db.session))
admin.add_view(BaobabModelView(Registration, db.session))
admin.add_view(BaobabModelView(RegistrationAnswer, db.session))

admin.add_view(BaobabModelView(InvitationTemplate, db.session))
admin.add_view(BaobabModelView(InvitationLetterRequest, db.session))
admin.add_view(BaobabModelView(EmailTemplate, db.session))

