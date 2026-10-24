"""The organisers' review dashboard for one review stage, built for events with
thousands of applications.

Everything is loaded in a handful of bulk queries rather than through the
models' lazy relationships, which would issue several queries per review.
Rows are then searched, sorted and paginated in memory: ranking applications by
average score needs every application's averages anyway, and at a few
thousand applications that is quick once the queries are batched.
"""
from math import ceil

from sqlalchemy.orm import joinedload, selectinload

from app import db
from app.forms import system as form_system
from app.forms.lifecycle import display_value
from app.forms.models import DISPLAY_ONLY_QUESTION_TYPES, FormAnswer, FormQuestion, FormResponse, answer_is_blank
from app.forms.review_serializers import REVIEW_IDENTIFIER_KEY, person, score_questions
from app.utils.language import translation_for

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


def _float_or_none(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _float_or_zero(value):
    parsed = _float_or_none(value)
    return 0.0 if parsed is None else parsed


def paginate(rows, page_number, limit):
    """One page of `rows` in the shape the paginated review endpoints share."""
    page_number = max(0, page_number)
    limit = min(MAX_PAGE_SIZE, max(1, limit))
    num_entries = len(rows)
    return rows[page_number * limit:(page_number + 1) * limit], {
        'num_entries': num_entries,
        'current_pagenumber': page_number,
        'total_pages': ceil(num_entries / limit) if num_entries else 0,
    }


def _matches(search, *values):
    if not search:
        return True
    needle = search.lower()
    return any(v and needle in str(v).lower() for v in values)


def _name(p):
    return ' '.join(filter(None, [p['firstname'], p['lastname']])) if p else ''


class ReviewDashboard:
    """Every review and application of `review_form`, as plain dicts."""

    def __init__(self, review_form, language):
        self.review_form = review_form
        self.language = language
        self.num_reviews_required = form_system.review_setting(review_form, 'num_reviews_required')
        self.score_questions = score_questions(review_form, language)

        self._review_questions = [
            q for s in review_form.sections if s.is_active
            for q in s.questions if q.is_active and q.type not in DISPLAY_ONLY_QUESTION_TYPES
        ]
        self._question_types = {q.id: q.type for q in review_form.questions}
        self._weights = {q.id: (q.settings or {}).get('weight') or 0 for q in review_form.questions}

        self._reviews = (db.session.query(FormResponse)
                         .options(selectinload(FormResponse.answers), joinedload(FormResponse.user))
                         .filter(FormResponse.form_id == review_form.id,
                                 FormResponse.is_withdrawn == False)  # noqa: E712
                         .order_by(FormResponse.linked_response_id, FormResponse.id)
                         .all())

        submitted_ids = []
        if review_form.linked_form_id:
            submitted_ids = [row[0] for row in db.session.query(FormResponse.id).filter(
                FormResponse.form_id == review_form.linked_form_id,
                FormResponse.is_submitted == True,  # noqa: E712
                FormResponse.is_withdrawn == False,  # noqa: E712
            ).order_by(FormResponse.id)]
        # A review can outlive its application's submission (a later
        # withdrawal), so its application is loaded even when not listed.
        application_ids = set(submitted_ids) | {r.linked_response_id for r in self._reviews if r.linked_response_id}
        applications = {}
        if application_ids:
            applications = {a.id: a for a in db.session.query(FormResponse)
                            .options(joinedload(FormResponse.user))
                            .filter(FormResponse.id.in_(application_ids))}
        self._submitted_applications = [applications[i] for i in submitted_ids]
        self._applicants = {i: person(a.user) for i, a in applications.items()}
        self._identifiers = self._load_identifiers(application_ids)

        self.review_rows = [self._review_row(r) for r in self._reviews]
        self.application_rows = self._application_rows()

    def _load_identifiers(self, application_ids):
        if not self.review_form.linked_form_id or not application_ids:
            return {}
        questions = (db.session.query(FormQuestion)
                     .filter(FormQuestion.form_id == self.review_form.linked_form_id,
                             FormQuestion.key == REVIEW_IDENTIFIER_KEY,
                             FormQuestion.is_active == True)  # noqa: E712
                     .order_by(FormQuestion.order).all())
        if not questions:
            return {}
        translations = {q.id: translation_for(q, self.language) for q in questions}
        by_id = {q.id: q for q in questions}
        answers = (db.session.query(FormAnswer)
                   .filter(FormAnswer.question_id.in_(list(by_id)),
                           FormAnswer.response_id.in_(list(application_ids)),
                           FormAnswer.is_active == True))  # noqa: E712
        values = {}
        for answer in answers:
            values[(answer.response_id, answer.question_id)] = answer.value
        result = {}
        for app_id in application_ids:
            items = []
            for q in questions:
                value = values.get((app_id, q.id))
                translation = translations[q.id]
                if value is None or translation is None:
                    continue
                items.append({'headline': translation.headline,
                              'value': display_value(q, translation, value)})
            result[app_id] = items
        return result

    def _active_answers(self, review):
        return {a.question_id: a for a in review.answers if a.is_active}

    def _review_row(self, review):
        answers = self._active_answers(review)
        if review.is_submitted:
            status = 'submitted'
        elif any(not answer_is_blank(self._question_types.get(qid), a.value) for qid, a in answers.items()):
            status = 'in_progress'
        else:
            status = 'not_started'
        total = sum(_float_or_zero(a.value) * self._weights.get(qid, 0)
                    for qid, a in answers.items() if self._weights.get(qid, 0) > 0)
        return {
            'review_response_id': review.id,
            'review_form_id': review.form_id,
            'stage': self.review_form.stage,
            'application_response_id': review.linked_response_id,
            'reviewer': person(review.user),
            'applicant': self._applicants.get(review.linked_response_id),
            'identifiers': self._identifiers.get(review.linked_response_id, []),
            'status': status,
            'submitted_timestamp': review.submitted_timestamp.isoformat() if review.submitted_timestamp else None,
            'total_score': total,
            '_scores': {
                q['question_id']: _float_or_none(answers[q['question_id']].value)
                for q in self.score_questions if q['question_id'] in answers
            },
        }

    def _application_rows(self):
        by_application = {}
        for row in self.review_rows:
            by_application.setdefault(row['application_response_id'], []).append(row)
        rows = []
        for app in self._submitted_applications:
            app_reviews = by_application.get(app.id, [])
            submitted = [r for r in app_reviews if r['status'] == 'submitted']
            averages = {}
            for q in self.score_questions:
                values = [r['_scores'].get(q['question_id']) for r in submitted]
                values = [v for v in values if v is not None]
                averages[str(q['question_id'])] = sum(values) / len(values) if values else None
            rows.append({
                'application_response_id': app.id,
                'applicant': self._applicants[app.id],
                'identifiers': self._identifiers.get(app.id, []),
                'reviews_assigned': len(app_reviews),
                'reviews_submitted': len(submitted),
                'average_scores': averages,
                'average_total': (sum(r['total_score'] for r in submitted) / len(submitted)) if submitted else None,
            })
        return rows

    def summary(self):
        return {
            'applications': len(self.application_rows),
            'fully_reviewed': sum(1 for a in self.application_rows
                                  if a['reviews_submitted'] >= self.num_reviews_required),
            'reviews_assigned': len(self.review_rows),
            'reviews_submitted': sum(1 for r in self.review_rows if r['status'] == 'submitted'),
        }

    def search_applications(self, search, sort_column, sort_desc):
        def identifier_values(row):
            return [i['value'] for i in row['identifiers']]

        rows = [a for a in self.application_rows
                if _matches(search, _name(a['applicant']), a['applicant']['email'],
                            a['application_response_id'], *identifier_values(a))]

        def value_of(row):
            if sort_column == 'name':
                return _name(row['applicant']).lower()
            if sort_column == 'reviews':
                return row['reviews_submitted']
            if sort_column in row['average_scores']:
                return row['average_scores'][sort_column]
            return row['average_total']

        # Unscored applications always sink to the bottom, whichever way the
        # column is sorted.
        scored = [r for r in rows if value_of(r) is not None]
        unscored = [r for r in rows if value_of(r) is None]
        scored.sort(key=value_of, reverse=sort_desc)
        return scored + unscored

    def search_reviews(self, search):
        return [r for r in self.review_rows
                if _matches(search, _name(r['reviewer']), r['reviewer']['email'], _name(r['applicant']),
                            r['application_response_id'], *[i['value'] for i in r['identifiers']])]

    def with_answers(self, rows):
        """`rows` (review rows) with each review's answered questions, in form
        order, as organisers read them."""
        translations = {q.id: translation_for(q, self.language) for q in self._review_questions}
        reviews = {r.id: r for r in self._reviews}
        result = []
        for row in rows:
            answers = self._active_answers(reviews[row['review_response_id']])
            items = []
            for question in self._review_questions:
                answer = answers.get(question.id)
                translation = translations[question.id]
                if answer is None or translation is None or answer_is_blank(question.type, answer.value):
                    continue
                items.append({
                    'question_id': question.id,
                    'headline': translation.headline,
                    'type': question.type,
                    'weight': self._weights.get(question.id, 0),
                    'value': answer.value,
                    'display_value': display_value(question, translation, answer.value),
                })
            result.append({**{k: v for k, v in row.items() if not k.startswith('_')}, 'answers': items})
        return result
