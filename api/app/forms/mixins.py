"""Helper functions for the generic forms migration."""
from app import db
from app.forms.models import Form


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
