from functools import wraps

from flask import request, g
from flask_restful import reqparse
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature

from app import app
from app.users.repository import UserRepository as user_repository
from app.utils.errors import UNAUTHORIZED, FORBIDDEN


TWO_WEEKS = 1209600


def generate_token(user, expiration=TWO_WEEKS):
    s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps({
        'id': user.id,
        'email': user.email,
        'is_admin': user.is_admin
    }).decode('utf-8')


def verify_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except (SignatureExpired, BadSignature):
        return None
    return data


def get_user_from_request():
    token = request.headers.get('Authorization', '')
    if token:
        user = verify_token(token)
        return user
    return None


def auth_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_user_from_request()
        if user:
            g.current_user = user
            return func(*args, **kwargs)
        return UNAUTHORIZED
    return wrapper


def auth_optional(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_user_from_request()
        if user:
            g.current_user = user

        return func(*args, **kwargs)
    return wrapper


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_user_from_request()
        if user and user['is_admin']:
            g.current_user = user
            return func(*args, **kwargs)
        return FORBIDDEN
    return wrapper


def event_admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()

        user = get_user_from_request()
        if user:
            user_info = user_repository.get_by_id(user['id'])
            if user_info.is_event_admin(args['event_id']):
                g.current_user = user
                return func(*args, event_id=args['event_id'], **kwargs)
        
        return FORBIDDEN

    return wrapper