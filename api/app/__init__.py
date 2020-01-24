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

# Initialize the flask app
app = Flask(__name__)
app.config.from_object('config')
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
print(app.config['SQLALCHEMY_DATABASE_URI'])
rest_api = restful.Api(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
redis = FlaskRedis(app)
LOGGER = Logger().get_logger()

# Define the Routes
from app import rest_api
from .applicationModel import api as form_api
from .users import api as users_api
from .responses import api as responses_api
from .content import api as content_api
from .files import api as files_api
from .events import api as events_api
from .reviews import api as reviews_api
from .invitedGuest import api as invitedGuest_api
from .registration import api as registration_api
from .registrationResponse import api as registration_response
from .guestRegistrations import api as guest_registration
from .invitationletter import api as invitation_letter_api
from .attendance import api as attendance_api

rest_api.add_resource(users_api.UserAPI, '/api/v1/user')
rest_api.add_resource(users_api.UserCommentAPI, '/api/v1/user-comment')
rest_api.add_resource(users_api.AuthenticationAPI, '/api/v1/authenticate')
rest_api.add_resource(users_api.PasswordResetRequestAPI,
                      '/api/v1/password-reset/request')
rest_api.add_resource(users_api.PasswordResetConfirmAPI,
                      '/api/v1/password-reset/confirm')
rest_api.add_resource(users_api.AdminOnlyAPI, '/api/v1/admin')
rest_api.add_resource(users_api.EmailerAPI,
                      '/api/v1/admin/emailer')
rest_api.add_resource(form_api.ApplicationFormAPI, '/api/v1/application-form')
rest_api.add_resource(responses_api.ResponseAPI, '/api/v1/response')
rest_api.add_resource(content_api.CountryContentAPI,
                      '/api/v1/content/countries')
rest_api.add_resource(files_api.FileUploadAPI, '/api/v1/file')
rest_api.add_resource(content_api.CategoryContentAPI,
                      '/api/v1/content/categories')
rest_api.add_resource(content_api.EthnicityContentAPI,
                      '/api/v1/content/ethnicity')
rest_api.add_resource(content_api.TitleContentAPI,
                      '/api/v1/content/title'),
rest_api.add_resource(content_api.DisabilityContentAPI,
                      '/api/v1/content/disability'),
rest_api.add_resource(content_api.GenderContentAPI,
                      '/api/v1/content/gender'),
rest_api.add_resource(events_api.EventsAPI,
                      '/api/v1/events'),
rest_api.add_resource(events_api.EventStatsAPI,
                      '/api/v1/eventstats'),
rest_api.add_resource(users_api.VerifyEmailAPI,
                      '/api/v1/verify-email'),
rest_api.add_resource(users_api.ResendVerificationEmailAPI,
                      '/api/v1/resend-verification-email'),
rest_api.add_resource(reviews_api.ReviewAPI, '/api/v1/review')
rest_api.add_resource(reviews_api.ReviewResponseAPI, '/api/v1/reviewresponse')
rest_api.add_resource(reviews_api.ReviewAssignmentAPI,
                      '/api/v1/reviewassignment')
rest_api.add_resource(reviews_api.ReviewSummaryAPI,
                      '/api/v1/reviewassignment/summary')
rest_api.add_resource(events_api.NotSubmittedReminderAPI,
                      '/api/v1/reminder-unsubmitted')
rest_api.add_resource(events_api.NotStartedReminderAPI,
                      '/api/v1/reminder-not-started')
rest_api.add_resource(reviews_api.ReviewHistoryAPI, '/api/v1/reviewhistory')
rest_api.add_resource(users_api.UserProfileList, '/api/v1/userprofilelist')
rest_api.add_resource(users_api.UserProfile, '/api/v1/userprofile')
rest_api.add_resource(invitedGuest_api.InvitedGuestAPI, '/api/v1/invitedGuest')
rest_api.add_resource(invitedGuest_api.CreateUser,
                      '/api/v1/invitedGuest/create')
rest_api.add_resource(invitedGuest_api.InvitedGuestList,
                      '/api/v1/invitedGuestList')
rest_api.add_resource(invitedGuest_api.CheckIfInvitedGuest,
                      '/api/v1/checkIfInvitedGuest')
rest_api.add_resource(registration_api.OfferAPI, '/api/v1/offer')
rest_api.add_resource(registration_api.RegistrationFormAPI,
                      '/api/v1/registration-form')
rest_api.add_resource(registration_api.RegistrationSectionAPI,
                      '/api/v1/registration-section')
rest_api.add_resource(registration_api.RegistrationQuestionAPI,
                      '/api/v1/registration-question')
rest_api.add_resource(registration_response.RegistrationApi,
                      '/api/v1/registration-response')
rest_api.add_resource(guest_registration.GuestRegistrationApi,
                      '/api/v1/guest-registration')
rest_api.add_resource(guest_registration.GuestRegistrationFormAPI,
                      '/api/v1/guest-registration-form')
rest_api.add_resource(registration_response.RegistrationUnconfirmedAPI,
                      '/api/v1/registration/unconfirmed')
rest_api.add_resource(registration_response.RegistrationConfirmedAPI,
                      '/api/v1/registration/confirmed')
rest_api.add_resource(registration_response.RegistrationConfirmAPI,
                      '/api/v1/registration/confirm')
rest_api.add_resource(invitation_letter_api.InvitationLetterAPI,
                      '/api/v1/invitation-letter')
rest_api.add_resource(attendance_api.AttendanceAPI, '/api/v1/attendance')

migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

from organisation.resolver import OrganisationResolver

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

@app.before_request
def populate_organisation():
    domain = get_domain()
    LOGGER.info('Origin Domain: {}'.format(domain))  # TODO: Remove this after testing
    g.organisation = OrganisationResolver.resolve_from_domain(domain)

## Flask Admin Config

# set optional bootswatch theme
app.config['FLASK_ADMIN_SWATCH'] = 'darkly'
from .applicationModel.models import Question, Section
from .responses.models import Response, Answer, ResponseReviewer
from .users.models import UserCategory, AppUser, UserComment
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

