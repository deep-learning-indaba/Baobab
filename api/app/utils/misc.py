import uuid
from flask import g


ISO_8601_UTC_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def get_baobab_host():
    return g.organisation.system_url


def make_code():
    return str(uuid.uuid4())


def try_parse_float(text):
    try:
        return float(text)
    except:
        return 0.0
