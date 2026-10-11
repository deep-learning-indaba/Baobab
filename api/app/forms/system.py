"""Which form system drives an event's application, review and registration flows.

`Event.uses_new_forms` is the single switch. When it is set, the event's typed
generic Forms are used and the legacy ApplicationForm / ReviewForm /
RegistrationForm are ignored entirely; when it is clear, the reverse. Every
caller that has to pick a system goes through these helpers so the two can
never disagree.
"""
from app import db
from app.events.models import Event
from app.forms.models import Form, FormResponse, FormAnswer, FormQuestion

APPLICATION = 'application'
REVIEW = 'review'
REGISTRATION = 'registration'

REVIEW_SETTING_DEFAULTS = {
    'page_per_section': False,
    'num_reviews_required': 3,
    'num_optional_reviews': 0,
    'drop_optional_question_id': None,
    'drop_optional_agreement_values': None,
}


def review_setting(review_form, key):
    """A review form setting, falling back to the default it was created with."""
    settings = review_form.settings or {}
    value = settings.get(key)
    return REVIEW_SETTING_DEFAULTS.get(key) if value is None else value


def _event(event_or_id):
    if isinstance(event_or_id, Event):
        return event_or_id
    return db.session.query(Event).get(event_or_id)


def event_uses_new_forms(event_or_id):
    event = _event(event_or_id)
    return bool(event and event.uses_new_forms)


def get_typed_form(event_or_id, form_type):
    """The event's new-system form of `form_type`, or None when the event is on
    the legacy system or has no such form yet. For review forms this is the
    active stage (see get_active_review_form)."""
    event = _event(event_or_id)
    if not event or not event.uses_new_forms:
        return None
    if form_type == REVIEW:
        return get_active_review_form(event)
    return db.session.query(Form).filter_by(event_id=event.id, form_type=form_type).first()


def get_application_form(event_or_id):
    return get_typed_form(event_or_id, APPLICATION)


def get_registration_form(event_or_id):
    return get_typed_form(event_or_id, REGISTRATION)


def get_review_forms(event_or_id):
    """All review stages of a new-system event, in stage order."""
    event = _event(event_or_id)
    if not event or not event.uses_new_forms:
        return []
    return (db.session.query(Form)
            .filter_by(event_id=event.id, form_type=REVIEW)
            .order_by(Form.stage)
            .all())


def get_active_review_form(event_or_id):
    """The review stage currently in use. Exactly one stage is meant to be
    active at a time (see set_active_review_stage); if none is, the latest
    stage is used so that an event with a single review form still works."""
    forms = get_review_forms(event_or_id)
    active = [f for f in forms if f.is_active]
    if active:
        return active[-1]
    return forms[-1] if forms else None


def set_active_review_stage(event_id, stage):
    """Make `stage` the only active review stage. Returns the form, or None if
    there is no review form for that stage. The caller commits."""
    forms = get_review_forms(event_id)
    selected = next((f for f in forms if f.stage == stage), None)
    if selected is None:
        return None
    for form in forms:
        form.is_active = form is selected
    return selected


def get_submitted_response(form, user_id):
    """The user's latest submitted, non-withdrawn response to `form`."""
    return (db.session.query(FormResponse)
            .filter_by(form_id=form.id, user_id=user_id, is_submitted=True, is_withdrawn=False)
            .order_by(FormResponse.id.desc())
            .first())


def get_answer_by_question_key(response, question_key):
    """The active answer on `response` to the question whose key is `question_key`."""
    return (db.session.query(FormAnswer)
            .join(FormQuestion, FormQuestion.id == FormAnswer.question_id)
            .filter(FormQuestion.key == question_key,
                    FormAnswer.response_id == response.id,
                    FormAnswer.is_active == True)  # noqa: E712
            .first())
