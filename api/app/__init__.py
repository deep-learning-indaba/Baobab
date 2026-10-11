from flask import Flask, g, request
import flask_restful as restful
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from .utils.logger import Logger
import tldextract

app = Flask(__name__)
app.config.from_object('config')
print((app.config['SQLALCHEMY_DATABASE_URI']))
rest_api = restful.Api(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
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
    LOGGER.info(f"Processing stripe signature {signature}")
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

@app.route('/_ah/start')
@app.route('/_ah/stop')
@app.route('/_ah/warmup')
def appengine_lifecycle():
    return 'OK', 200


@app.before_request
def populate_organisation():
    if request.path.startswith('/_ah/'):
        return
    if request.path.startswith('/api/v1/tasks/'):
        # Scheduled tasks are invoked by App Engine cron, which sends no Origin
        # or Referer, and resolve_from_domain rejects an empty domain. Task
        # handlers carry the organisation on the work they process instead.
        return
    if request.path == '/api/v1/file' and request.method == 'GET':
        # File downloads are opened as direct top-level navigations (e.g. clicking
        # a link opened in a new tab), not XHR/fetch calls from the webapp, so there's
        # no reliable Origin header, and the link is rel="noreferrer" so there's no
        # Referer either. The handler doesn't use g.organisation, so skip resolution.
        return
    if is_from_stripe():
        signed_payload, expected_signature = get_signed_payload_and_signature()
        g.organisation = OrganisationResolver.resolve_from_stripe_signature(
            signed_payload,
            expected_signature
        )
    else:
        domain = get_domain()
        g.organisation = OrganisationResolver.resolve_from_domain(domain)

CORS_ALLOWED_METHODS = 'GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS'

@app.after_request
def set_cors_headers(response):
    # populate_organisation() above already rejects any /api/* request whose
    # Origin/Referer domain doesn't match a known Organisation, so reflecting
    # the Origin back here is only ever done for domains we've already
    # validated against the Organisation table - no separate allow-list to
    # keep in sync with webapp/dispatch.yaml.
    if not request.path.startswith('/api/') or getattr(g, 'organisation', None) is None:
        return response
    origin = request.environ.get('HTTP_ORIGIN', '')
    if not origin:
        return response
    response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers.add('Vary', 'Origin')
    # Browsers hide this header from cross-origin JS unless explicitly exposed;
    # needed so axios-based file downloads can read the server-supplied filename.
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
    if request.method == 'OPTIONS':
        response.headers['Access-Control-Allow-Methods'] = CORS_ALLOWED_METHODS
        requested_headers = request.environ.get('HTTP_ACCESS_CONTROL_REQUEST_HEADERS')
        if requested_headers:
            response.headers['Access-Control-Allow-Headers'] = requested_headers
    return response
