import uuid
from flask import g


def get_baobab_host():
    return g.organisation.system_url


def make_code():
    return str(uuid.uuid4())


def try_parse_float(text):
    try:
        return float(text)
    except:
        return 0.0
