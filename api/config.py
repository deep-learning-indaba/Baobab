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
FILE_SIZE_LIMIT = int(os.getenv('FILE_SIZE_LIMIT', None))

BOABAB_HOST = os.getenv('BOABAB_HOST', None)
STRIPE_API_KEY = os.getenv('STRIPE_API_KEY', None)