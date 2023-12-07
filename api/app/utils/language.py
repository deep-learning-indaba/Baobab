"""Language utilities."""

from functools import wraps
from flask_restful import reqparse

def translatable(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('language', type=str, required=False)
        req_args = req_parser.parse_args()

        language = req_args['language'] or 'en'

        return func(*args, language=language, **kwargs)

    return wrapper