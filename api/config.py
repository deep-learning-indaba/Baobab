import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE_CONNECT_OPTIONS = {}

DEBUG = os.getenv('DEBUG', False)

PORT = os.getenv('PORT', 5000)

SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',
    'postgres://docker:docker@{0}/docker'.format(os.getenv('DB_PORT_5432_TCP_ADDR')))

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
