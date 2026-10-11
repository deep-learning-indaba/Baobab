"""Serialisation of new-system reviews (FormResponses on review forms), shared
by the reviewer and organiser endpoints."""
from app.forms.lifecycle import display_value
from app.forms.models import DISPLAY_ONLY_QUESTION_TYPES, answer_is_blank
from app.utils.language import translation_for

REVIEW_IDENTIFIER_KEY = 'review-identifier'


def person(user):
    return {
        'user_id': user.id,
        'user_title': user.user_title,
        'firstname': user.firstname,
        'lastname': user.lastname,
        'email': user.email,
    }


def _active_answers(response):
    return {a.question_id: a for a in response.answers if a.is_active}


def identifiers(application, language):
    """Answers to application questions keyed 'review-identifier' - the short
    description of an application shown in review lists."""
    result = []
    answers = _active_answers(application)
    for question in application.form.questions:
        if question.key != REVIEW_IDENTIFIER_KEY or not question.is_active:
            continue
        answer = answers.get(question.id)
        translation = translation_for(question, language)
        if answer is None or translation is None:
            continue
        result.append({
            'headline': translation.headline,
            'value': display_value(question, translation, answer.value),
        })
    return result


def review_status(review):
    if review.is_submitted:
        return 'submitted'
    if any(a.is_active and not a.is_blank() for a in review.answers):
        return 'in_progress'
    return 'not_started'


def _weight(question):
    return (question.settings or {}).get('weight') or 0


def score_questions(review_form, language):
    """Weighted review questions, in form order - the columns of a score table."""
    result = []
    for section in review_form.sections:
        if not section.is_active:
            continue
        for question in section.questions:
            if not question.is_active or _weight(question) <= 0:
                continue
            translation = translation_for(question, language)
            result.append({
                'question_id': question.id,
                'headline': translation.headline if translation else '',
                'type': question.type,
                'weight': _weight(question),
            })
    return result


def _review_answers(review, language):
    """Every answered review question with its display value, in form order."""
    answers = _active_answers(review)
    result = []
    for section in review.form.sections:
        if not section.is_active:
            continue
        for question in section.questions:
            if not question.is_active or question.type in DISPLAY_ONLY_QUESTION_TYPES:
                continue
            answer = answers.get(question.id)
            if answer is None or answer_is_blank(question.type, answer.value):
                continue
            translation = translation_for(question, language)
            if translation is None:
                continue
            result.append({
                'question_id': question.id,
                'headline': translation.headline,
                'type': question.type,
                'weight': _weight(question),
                'value': answer.value,
                'display_value': display_value(question, translation, answer.value),
            })
    return result


def serialize_review(review, language):
    """A review as organisers see it: who, about whom, status, answers and score."""
    application = review.linked_response
    return {
        'review_response_id': review.id,
        'review_form_id': review.form_id,
        'stage': review.form.stage,
        'application_response_id': review.linked_response_id,
        'reviewer': person(review.user),
        'applicant': person(application.user) if application else None,
        'identifiers': identifiers(application, language) if application else [],
        'status': review_status(review),
        'submitted_timestamp': review.submitted_timestamp.isoformat() if review.submitted_timestamp else None,
        'total_score': review.calculate_score(),
        'answers': _review_answers(review, language),
    }


def numeric_answer(review_data, question_id):
    answer = next((a for a in review_data['answers'] if a['question_id'] == question_id), None)
    try:
        return float(answer['value']) if answer else None
    except (TypeError, ValueError):
        return None
