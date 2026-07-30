import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE_CONNECT_OPTIONS = {}

DEBUG = os.getenv('DEBUG', False)

PORT = os.getenv('PORT', 5000)

SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgres://docker:docker@db/docker')

SECRET_KEY = os.getenv('SECRET_KEY', None)
assert SECRET_KEY

THREADS_PER_PAGE = 2

SQLALCHEMY_TRACK_MODIFICATIONS = False
SMTP_USERNAME = os.getenv('SMTP_USERNAME', None)
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', None)
SMTP_SENDER_NAME = os.getenv('SMTP_SENDER_NAME', None)
SMTP_SENDER_EMAIL = os.getenv('SMTP_SENDER_EMAIL', None)
SMTP_HOST = os.getenv('SMTP_HOST', None)
SMTP_PORT = os.getenv('SMTP_PORT', None)
# Messages per second a shared SMTP connection will send. SES rejects anything
# above the account's quota, so this must stay under it.
SMTP_MAX_SEND_RATE = float(os.getenv('SMTP_MAX_SEND_RATE', 10))

# Outbox worker tuning. The worker occupies a gunicorn worker for as long as it
# runs, and there are only a handful of those, so the budget is set to well under
# the cron interval to leave capacity for user traffic — not to the largest value
# the gunicorn timeout would allow. The batch is then sized to what the budget can
# usually drain at SMTP_MAX_SEND_RATE, so finishing is the normal case and
# releasing the remainder is the exception.
OUTBOX_BATCH_SIZE = int(os.getenv('OUTBOX_BATCH_SIZE', 250))
OUTBOX_TIME_BUDGET_SECONDS = float(os.getenv('OUTBOX_TIME_BUDGET_SECONDS', 30))

GCP_CREDENTIALS_DICT = {
    'type': 'service_account',
    'client_id': os.getenv('GCP_CLIENT_ID', None),
    'client_email': os.getenv('GCP_CLIENT_EMAIL', None),
    'private_key_id': os.getenv('GCP_PRIVATE_KEY_ID', None),
    'private_key': os.getenv('GCP_PRIVATE_KEY', None),
    'token_uri': 'https://oauth2.googleapis.com/token'
}
GCP_PROJECT_NAME = os.getenv('GCP_PROJECT_NAME', None)
GCP_BUCKET_NAME = os.getenv('GCP_BUCKET_NAME', None)
GCP_API_KEY = os.getenv('GCP_API_KEY', None)
FILE_SIZE_LIMIT = int(os.getenv('FILE_SIZE_LIMIT', None))

BOABAB_HOST = os.getenv('BOABAB_HOST', None)

VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_CLAIM_EMAIL = os.environ.get('VAPID_CLAIM_EMAIL', 'mailto:baobab@deeplearningindaba.com')