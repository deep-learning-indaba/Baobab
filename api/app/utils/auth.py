from functools import wraps

from flask import request, g
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature

from app import app
from app.utils.errors import UNAUTHORIZED, FORBIDDEN


TWO_WEEKS = 1209600


def generate_token(user, expiration=TWO_WEEKS):
    s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps({
        'id': user.id,
        'email': user.email,
        'is_admin': user.is_admin
    })


def verify_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except (SignatureExpired, BadSignature):
        return None
    return data


def auth_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization', '')
        if token:
            user = verify_token(token)
            if user:
                g.current_user = user
                return func(*args, **kwargs)
        return UNAUTHORIZED
    return wrapper


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization', '')
        if token:
            user = verify_token(token)
            if user and user['is_admin']:
                g.current_user = user
                return func(*args, **kwargs)
        return FORBIDDEN
    return wrapper
