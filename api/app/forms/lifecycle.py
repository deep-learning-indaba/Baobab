"""Behaviour that typed forms (application / review / registration) add on top of
the generic response endpoints: who may respond, and what happens when a
response is submitted or withdrawn."""
import json

from app import db, LOGGER
from app.email_template.service import queue_email
from app.events.models import EventType
from app.events.repository import EventRepository
from app.forms import system as form_system
from app.forms.models import (
    DependencyEvaluator, DISPLAY_ONLY_QUESTION_TYPES, MULTI_VALUE_SEPARATOR,
)
from app.invitedGuest.models import InvitedGuest
from app.offer.models import Offer
from app.utils.language import translation_for, user_language_for_event


FORM_NOT_AVAILABLE = ({'message': 'This form is not available for this event.'}, 404)
NOT_ELIGIBLE_TO_REGISTER = (
    {'message': 'Only invited guests and applicants who have accepted an offer can register.'}, 403
)
REVIEWS_ARE_ASSIGNED = (
    {'message': 'Reviews are assigned by the event organisers and cannot be created directly.'}, 403
)


def _is_eligible_to_register(user_id, event_id):
    if db.session.query(InvitedGuest).filter_by(user_id=user_id, event_id=event_id).first():
        return True
    offer = db.session.query(Offer).filter_by(user_id=user_id, event_id=event_id).first()
    return bool(offer and offer.candidate_response)


def check_can_respond(form, user_id, creating=False):
    """Error response if `user_id` may not create (creating=True) or edit a
    response to `form`, else None. Generic forms have no extra rules."""
    if not form.form_type:
        return None
    # A typed form only drives its flow while the event is on the new system.
    if not form.event.uses_new_forms:
        return FORM_NOT_AVAILABLE
    if form.form_type == form_system.REVIEW and creating:
        return REVIEWS_ARE_ASSIGNED
    if form.form_type == form_system.REGISTRATION and not _is_eligible_to_register(user_id, form.event_id):
        return NOT_ELIGIBLE_TO_REGISTER
    return None


def display_value(question, translation, value):
    if question.type == 'file':
        return 'Fichier téléchargé' if translation.language == 'fr' else 'Uploaded File'
    if question.type == 'multi-file':
        try:
            return '\n'.join(f['name'] for f in json.loads(value))
        except (ValueError, TypeError, KeyError):
            return value
    if translation.options:
        labels = {o['value']: o['label'] for o in translation.options}
        return MULTI_VALUE_SEPARATOR.join(labels.get(v, v) for v in value.split(MULTI_VALUE_SEPARATOR))
    return value


def answer_sections(response, language):
    """[{'name': section name, 'answers': [{'question', 'answer'}]}] for every
    visible section with an answered question - the copy of a response that
    goes into confirmation emails."""
    answers = {a.question_id: a for a in response.answers if a.is_active}
    answers_dict = {qid: a.value for qid, a in answers.items()}
    sections = []
    for section in response.form.sections:
        if not section.is_active or not DependencyEvaluator.evaluate(section.dependency_expression, answers_dict):
            continue
        pairs = []
        for question in section.questions:
            if not question.is_active or question.type in DISPLAY_ONLY_QUESTION_TYPES:
                continue
            if not DependencyEvaluator.evaluate(question.dependency_expression, answers_dict):
                continue
            answer = answers.get(question.id)
            if answer is None or answer.is_blank():
                continue
            translation = translation_for(question, language)
            if translation is None:
                continue
            pairs.append({
                'question': translation.headline,
                'answer': display_value(question, translation, answer.value),
            })
        if pairs:
            section_translation = translation_for(section, language)
            sections.append({
                'name': section_translation.name if section_translation else '',
                'answers': pairs,
            })
    return sections


def _registration_confirmed(user_id, event_id):
    if db.session.query(InvitedGuest).filter_by(user_id=user_id, event_id=event_id).first():
        return True
    offer = db.session.query(Offer).filter_by(user_id=user_id, event_id=event_id).first()
    return bool(offer and offer.is_confirmed)


def _queue(email_type, user, event, context=None):
    """Emails are a side effect: a failure is logged, never surfaced, so the
    submission it accompanies still succeeds."""
    try:
        queue_email(email_type, user, event=event, context=context)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        LOGGER.error('Could not queue {} email for user {}: {}'.format(email_type, user.id, e))


def on_submitted(response):
    form = response.form
    if form.form_type not in (form_system.APPLICATION, form_system.REGISTRATION):
        return
    user = response.user
    event = form.event
    language = user_language_for_event(user, event)
    sections = answer_sections(response, language)

    if form.form_type == form_system.APPLICATION:
        context = {'response': {'applicant': user, 'sections': sections}}
        _queue('application-submitted', user, event, context)
        if event.event_type == EventType.JOURNAL:
            for admin in EventRepository.get_event_admins(event_id=event.id):
                _queue('application-submitted', admin, event, context)
    else:
        answers = [pair for section in sections for pair in section['answers']]
        context = {'registration': {
            'confirmed': _registration_confirmed(user.id, event.id),
            'answers': answers,
        }}
        _queue('registration-received', user, event, context)


def on_withdrawn(response):
    if response.form.form_type == form_system.APPLICATION:
        _queue('withdrawal', response.user, response.form.event)


def on_offer_paid(offer):
    """Payment completes a pending new-system registration, so the attendee
    gets the same confirmation the legacy registration admin sends."""
    form = form_system.get_registration_form(offer.event_id)
    if form is None:
        return
    if form_system.get_submitted_response(form, offer.user_id) is None:
        return
    _queue('registration-confirmed', offer.user, offer.event)
