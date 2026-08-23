"""Tag/predicate evaluation shared by document eligibility and variant selection.

One expression language, three uses (document eligibility, variant selection,
and - in a later phase - derived placeholder rules): the same JSON structure
and the same evaluator (app/forms/visibility.py's VisibilityEvaluator), so the
admin UI needs only one rule-builder component.
"""
from app import db
from app.forms.visibility import VisibilityEvaluator
from app.forms.models import FormResponse
from app.attendance.models import Attendance


class EligibilityContext:
    """Everything a tag/predicate expression might need about one user at one event."""

    def __init__(self, tag_names, tag_ids, attended, submitted_form_ids):
        self.tag_names = tag_names
        self.tag_ids = tag_ids
        self.attended = attended
        self.submitted_form_ids = submitted_form_ids


def build_eligibility_context(user_id, event_id):
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

    return EligibilityContext(tag_names, tag_ids, attended, submitted_form_ids)


def evaluate_expression(expression, context):
    """True when `expression` (the shared tag/predicate JSON) holds for `context`.

    A None expression matches everyone - the same "no rule means unrestricted"
    convention as form visibility_expression.
    """
    return VisibilityEvaluator.evaluate(expression, context.tag_names, context)
