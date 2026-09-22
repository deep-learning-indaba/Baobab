"""Tag/predicate evaluation shared by document eligibility, variant selection
and derived placeholder rules.

One expression language, three uses: the same JSON structure and the same
evaluator (app/forms/visibility.py's VisibilityEvaluator), so the admin UI
needs only one rule-builder component.
"""
from app import db
from app.forms.visibility import VisibilityEvaluator
from app.forms.models import FormResponse
from app.attendance.models import Attendance


class EligibilityContext:
    """Everything a tag/predicate expression might need about one user at one event."""

    def __init__(self, tag_names, tag_ids, attended, submitted_form_ids, answer_resolver=None):
        self.tag_names = tag_names
        self.tag_ids = tag_ids
        self.attended = attended
        self.submitted_form_ids = submitted_form_ids
        # Optional key -> value lookup backing the `key`/`operator` answer-
        # comparison leaf, bound by the caller to a PlaceholderResolver so
        # "bringing_poster equals yes" reads through the same linked-form /
        # user-data / profile precedence a placeholder would. None when the
        # caller has no template to resolve against (e.g. a bare tag check),
        # in which case that leaf always evaluates False - see
        # VisibilityEvaluator._evaluate_answer.
        self._answer_resolver = answer_resolver

    def get_answer_value(self, key):
        return self._answer_resolver(key) if self._answer_resolver else None


def build_eligibility_context(user_id, event_id, answer_resolver=None):
    tag_names = VisibilityEvaluator.get_user_tags_for_event(user_id, event_id)
    tag_ids = VisibilityEvaluator.get_user_tag_ids_for_event(user_id, event_id)

    attendance = db.session.query(Attendance).filter_by(
        event_id=event_id, user_id=user_id).first()
    attended = bool(attendance and attendance.confirmed)

    submitted_form_ids = {
        row.form_id for row in db.session.query(FormResponse.form_id).filter(
            FormResponse.user_id == user_id,
            FormResponse.is_submitted == True,   # noqa: E712
            FormResponse.is_withdrawn == False,  # noqa: E712
        ).all()
    }

    return EligibilityContext(tag_names, tag_ids, attended, submitted_form_ids, answer_resolver)


def evaluate_expression(expression, context):
    """True when `expression` (the shared tag/predicate JSON) holds for `context`.

    A None expression matches everyone - the same "no rule means unrestricted"
    convention as form visibility_expression.
    """
    return VisibilityEvaluator.evaluate(expression, context.tag_names, context)
