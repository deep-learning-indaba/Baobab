"""Auth helpers for the documents module, mirroring app/forms/mixins.py.

Authorisation is always derived from the resource's own event_id, never from
a caller-supplied one - an admin of event A must not be able to act on event
B's document templates just by knowing a template id and passing their own
event_id. See app/forms/mixins.py's verify_form_event for the same hazard.
"""
from functools import wraps

from flask import g

from app import db
from app.documents.models import DocumentTemplate
from app.utils import errors
from app.utils.auth import get_user_from_request
from app.users.repository import UserRepository as user_repository


def document_admin_required(func):
    """Require the caller be an event admin of the template's own event.

    Resolves the `template_id` URL parameter to a DocumentTemplate and passes
    it through as `document_template`, so handlers don't re-query it.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_user_from_request()
        if not user:
            return errors.UNAUTHORIZED

        template_id = kwargs.pop('template_id', None)
        document_template = db.session.query(DocumentTemplate).filter_by(id=template_id).first()
        if not document_template:
            return errors.DOCUMENT_TEMPLATE_NOT_FOUND

        user_info = user_repository.get_by_id(user['id'])
        if not user_info or not user_info.is_event_admin(document_template.event_id):
            return errors.FORBIDDEN

        g.current_user = user
        return func(*args, document_template=document_template, **kwargs)

    return wrapper


def is_document_admin_of_event(user_info, event_id):
    return bool(user_info and user_info.is_event_admin(event_id))


def event_admin_required_from_path(func):
    """Like app.utils.auth.event_admin_required, but for routes where
    event_id is a URL path segment (/events/<int:event_id>/...) rather than a
    query parameter.

    event_admin_required always re-derives event_id itself via reqparse and
    re-injects it as a keyword argument; on a route where Flask has already
    supplied event_id from the path, that collides - the call ends up passing
    event_id twice. This variant trusts the value Flask already resolved
    instead of parsing a second copy.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_user_from_request()
        if not user:
            return errors.UNAUTHORIZED

        event_id = kwargs.get('event_id')
        user_info = user_repository.get_by_id(user['id'])
        if not user_info or not user_info.is_event_admin(event_id):
            return errors.FORBIDDEN

        g.current_user = user
        return func(*args, **kwargs)

    return wrapper
