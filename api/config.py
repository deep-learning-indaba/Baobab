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