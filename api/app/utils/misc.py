import uuid
from config import BOABAB_HOST


def get_baobab_host():
    return BOABAB_HOST[:-1] if BOABAB_HOST.endswith('/') else BOABAB_HOST


def make_code():
    return str(uuid.uuid4())
