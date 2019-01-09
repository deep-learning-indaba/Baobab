from functools import wraps

from flask import request, g
from time import time

from app import app, redis
from app.utils.errors import TOO_MANY_REQUESTS


def rate_limit(limit=100, window=60):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = "{0}: {1}".format(request.remote_addr, request.path)

            try:
                remaining = limit - int(redis.get(key))
            except (ValueError, TypeError):
                remaining = limit
                redis.set(key, 0)

            expires_in = redis.ttl(key)
            if not expires_in:
                redis.expire(key, window)
                expires_in = window

            g.rate_limits = (limit, remaining-1, time()+expires_in)

            if remaining > 0:
                redis.incr(key, 1)
                return func(*args, **kwargs)
            return TOO_MANY_REQUESTS
        return wrapper
    return decorator


@app.after_request
def add_rate_limit_headers(response):
    try:
        limit, remaining, expires = map(int, g.rate_limits)
    except (AttributeError, ValueError):
        return response
    else:
        response.headers.add('X-RateLimit-Remaining', remaining)
        response.headers.add('X-RateLimit-Limit', limit)
        response.headers.add('X-RateLimit-Reset', expires)
        return response
