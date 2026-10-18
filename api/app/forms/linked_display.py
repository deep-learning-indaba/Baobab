"""Which of a linked form's answers are shown alongside a form.

A form with a linked form (a review form, linked to the application form)
can hide parts of the linked response through `settings['linked_display']`:

    {"hidden_section_ids": [12], "hidden_question_ids": [101, 107]}

Everything is shown when the setting is absent. Hiding a section hides every
question in it, including questions added to it later. Hidden answers are
removed server-side rather than just not rendered, so the setting can be used
for blind review.
"""

LINKED_DISPLAY_KEY = 'linked_display'
_ID_LIST_KEYS = ('hidden_section_ids', 'hidden_question_ids')


def validate_linked_display(settings):
    """An error message if `settings['linked_display']` is malformed, else None.

    Ids that don't belong to the linked form are accepted: the linked form can
    change after this form is saved, and unknown ids simply match nothing.
    """
    if not isinstance(settings, dict) or settings.get(LINKED_DISPLAY_KEY) is None:
        return None
    value = settings[LINKED_DISPLAY_KEY]
    if not isinstance(value, dict):
        return 'settings.linked_display must be an object'
    for key in _ID_LIST_KEYS:
        ids = value.get(key, [])
        # bool is a subclass of int, so it has to be excluded explicitly.
        if not isinstance(ids, list) or not all(isinstance(i, int) and not isinstance(i, bool) for i in ids):
            return 'settings.linked_display.{} must be a list of ids'.format(key)
    return None


def hidden_question_ids(form, linked_form):
    """Ids of `linked_form` questions that `form` hides."""
    display = (form.settings or {}).get(LINKED_DISPLAY_KEY) or {}
    hidden_sections = set(display.get('hidden_section_ids') or [])
    hidden = set(display.get('hidden_question_ids') or [])
    for question in linked_form.questions:
        if question.section_id in hidden_sections:
            hidden.add(question.id)
    return hidden


def _expression_question_ids(expression, ids):
    if isinstance(expression, dict):
        if 'question_id' in expression:
            try:
                ids.add(int(expression['question_id']))
            except (TypeError, ValueError):
                pass
        for condition in expression.get('conditions') or []:
            _expression_question_ids(condition, ids)
    return ids


def dependency_question_ids(form):
    """Ids of every question referenced by `form`'s active sections' and
    questions' dependency expressions."""
    ids = set()
    for section in form.sections:
        if not section.is_active:
            continue
        _expression_question_ids(section.dependency_expression, ids)
        for question in section.questions:
            if question.is_active:
                _expression_question_ids(question.dependency_expression, ids)
    return ids


def filter_serialized_form(form_data, hidden_ids):
    """`form_data` (from serialize_form) without the hidden questions, and
    without sections left with nothing shown."""
    sections = []
    for section in form_data['sections']:
        questions = [q for q in section['questions'] if q['id'] not in hidden_ids]
        if questions:
            sections.append({**section, 'questions': questions})
    return {**form_data, 'sections': sections}
