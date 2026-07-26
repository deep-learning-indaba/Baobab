"""Helper functions for the generic forms migration."""
from functools import wraps

from flask import g

from app import db
from app.forms.models import Form
from app.utils import errors
from app.utils.auth import get_user_from_request
from app.users.repository import UserRepository as user_repository


def is_admin_of_form(form):
    """Whether the caller is an event admin for the event that owns `form`.

    Authorisation for form administration is derived from the form's own
    event_id rather than a caller-supplied event_id - otherwise an admin of
    event A can act on a form belonging to event B just by passing their own
    event_id (see verify_form_event below for the same problem on endpoints
    that must keep taking event_id as an argument).
    """
    user = get_user_from_request()
    if not user:
        return False
    user_info = user_repository.get_by_id(user['id'])
    if not user_info:
        return False
    return user_info.is_event_admin(form.event_id)


def form_admin_required(func):
    """Require that the caller is an event admin of the form's own event.

    Resolves the `form_id` URL parameter to a Form and passes it through as a
    `form` keyword argument so handlers don't re-query it.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_user_from_request()
        if not user:
            return errors.UNAUTHORIZED

        form_id = kwargs.get('form_id')
        form = db.session.query(Form).filter_by(id=form_id).first()
        if not form:
            return errors.FORM_NOT_FOUND

        user_info = user_repository.get_by_id(user['id'])
        if not user_info or not user_info.is_event_admin(form.event_id):
            return errors.FORBIDDEN

        g.current_user = user
        return func(*args, form=form, **kwargs)

    return wrapper


def verify_form_event(form, event_id):
    """Guard for endpoints that take event_id as a request argument.

    `event_admin_required` only proves the caller administers `event_id`; it
    says nothing about whether `form` belongs to that event. Without this
    check any event admin can read or mutate another event's forms and
    responses by passing their own event_id.
    """
    return form is not None and form.event_id == event_id


def uses_new_form(event_id, form_type):
    """Check if an event uses the new generic form system for a given form type."""
    return db.session.query(Form).filter_by(
        event_id=event_id, form_type=form_type
    ).first() is not None


def get_form_by_type(event_id, form_type, stage=None):
    """Get the Form for a given event, form type, and optional stage."""
    query = db.session.query(Form).filter_by(
        event_id=event_id, form_type=form_type
    )
    if stage is not None:
        query = query.filter_by(stage=stage)
    else:
        query = query.filter_by(is_active=True)
    return query.first()


def apply_form_type_defaults(form, form_type, stage=None):
    """Apply role-specific defaults when creating a typed form."""
    if form_type == 'application':
        if form.settings is None:
            form.settings = {}
        if 'page_per_section' not in form.settings:
            form.settings['page_per_section'] = True
        form.multiple_responses = False
        form.allow_edits = True

    elif form_type == 'review':
        if form.settings is None:
            form.settings = {}
        defaults = {
            'page_per_section': False,
            'num_reviews_required': 3,
            'num_optional_reviews': 0,
            'drop_optional_question_id': None,
            'drop_optional_agreement_values': None
        }
        for key, value in defaults.items():
            if key not in form.settings:
                form.settings[key] = value
        form.multiple_responses = True
        form.allow_edits = True
        if stage is not None:
            form.stage = stage

    elif form_type == 'registration':
        form.visibility_expression = {
            'operator': 'OR',
            'conditions': [
                {'tag': 'selected_attendee'},
                {'tag': 'invited_guest'}
            ]
        }
        form.multiple_responses = False
        form.allow_edits = True


def validate_form_type_constraints(event_id, form_type):
    """
    Validate that form type assignments are consistent.
    Returns an error message string if invalid, None if valid.
    """
    if form_type == 'review':
        app_form = db.session.query(Form).filter_by(
            event_id=event_id, form_type='application'
        ).first()
        if not app_form:
            return (
                'Cannot create a new-style review form without a new-style application form. '
                'Application and review forms must use the same system.'
            )
    return None
