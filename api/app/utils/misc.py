import uuid
from flask import g


def get_baobab_host():
    return g.organisation.system_url


def make_code():
    return str(uuid.uuid4())
