"""Reviewing with new-system review forms.

A review assignment is a FormResponse on a review Form whose
linked_response_id is the applicant's application FormResponse (see
FormReviewAssignmentAPI). Reviewers fill it in through the ordinary response
endpoints; these resources provide the reviewer's queue and history, and the
organisers' review dashboard.
"""
from math import ceil
import traceback

import flask_restful as restful
from flask import g, request

from app import db, LOGGER
from app.forms import system as form_system
from app.forms.api import serialize_form, serialize_response, _error
from app.forms.models import Form, FormResponse
from app.forms.review_serializers import (
    identifiers, numeric_answer, person, review_status, score_questions, serialize_review,
)
from app.users.repository import UserRepository as user_repository
from app.utils import errors
from app.utils.auth import auth_required, event_admin_required
from app.utils.language import translation_for

NO_REVIEW_FORM = ({'message': 'Reviewing is not yet available for this event.'}, 404)


def _language():
    return request.args.get('language') or 'en'


def _review_form_for_event(form_id, event_id):
    return db.session.query(Form).filter_by(
        id=form_id, form_type=form_system.REVIEW, event_id=event_id
    ).first()


def _require_reviewer(event_id):
    user = user_repository.get_by_id(g.current_user['id'])
    return user is not None and (user.is_reviewer(event_id) or user.is_event_admin(event_id))


def _reviewer_queue(review_form, reviewer_id):
    """The reviewer's assignments on `review_form` that still count: the
    application they review must still be submitted and not withdrawn."""
    application = db.aliased(FormResponse)
    return (db.session.query(FormResponse)
            .join(application, application.id == FormResponse.linked_response_id)
            .filter(FormResponse.form_id == review_form.id,
                    FormResponse.user_id == reviewer_id,
                    FormResponse.is_withdrawn == False,  # noqa: E712
                    application.is_submitted == True,  # noqa: E712
                    application.is_withdrawn == False)  # noqa: E712
            .order_by(FormResponse.id)
            .all())


class ReviewerAssignmentListAPI(restful.Resource):
    """The current reviewer's assignments for the event's active review stage."""

    @auth_required
    def get(self):
        event_id = request.args.get('event_id', type=int)
        if not event_id:
            return _error('event_id is required', 400)
        if not _require_reviewer(event_id):
            return errors.FORBIDDEN

        review_form = form_system.get_active_review_form(event_id)
        if review_form is None:
            return NO_REVIEW_FORM

        language = _language()
        queue = _reviewer_queue(review_form, g.current_user['id'])
        assignments = []
        for review in queue:
            assignments.append({
                'review_response_id': review.id,
                'application_response_id': review.linked_response_id,
                'identifiers': identifiers(review.linked_response, language),
                'status': review_status(review),
                'submitted_timestamp': review.submitted_timestamp.isoformat() if review.submitted_timestamp else None,
                'total_score': review.calculate_score(),
            })
        submitted = sum(1 for a in assignments if a['status'] == 'submitted')
        name = translation_for(review_form, language)
        return {
            'review_form_id': review_form.id,
            'form_name': name.name if name else None,
            'stage': review_form.stage,
            'is_open': review_form.is_open,
            'assignments': assignments,
            'counts': {
                'total': len(assignments),
                'submitted': submitted,
                'remaining': len(assignments) - submitted,
            },
        }, 200


class ReviewerAssignmentDetailAPI(restful.Resource):
    """Everything a reviewer needs to review one application: the review form
    and their review so far, the application form and answers, and where this
    review sits in their queue."""

    @auth_required
    def get(self, review_response_id):
        event_id = request.args.get('event_id', type=int)
        if not event_id:
            return _error('event_id is required', 400)
        user_id = g.current_user['id']

        review = db.session.query(FormResponse).filter_by(id=review_response_id, user_id=user_id).first()
        if (review is None or review.is_withdrawn or review.form.event_id != event_id
                or review.form.form_type != form_system.REVIEW):
            return errors.OBJECT_NOT_FOUND
        if not form_system.event_uses_new_forms(event_id):
            return NO_REVIEW_FORM

        application = review.linked_response
        if application is None:
            return errors.OBJECT_NOT_FOUND

        language = _language()
        queue = _reviewer_queue(review.form, user_id)
        queue_ids = [r.id for r in queue]
        pending_ids = [r.id for r in queue if not r.is_submitted]
        position = queue_ids.index(review.id) if review.id in queue_ids else None
        # The next unfinished review after this one, wrapping round, so "skip"
        # cycles through everything still to do.
        later = [rid for rid in pending_ids if position is None or queue_ids.index(rid) > position]
        earlier = [rid for rid in pending_ids if rid not in later and rid != review.id]
        next_ids = later + earlier

        application_data = serialize_response(application)
        # Tags are an organiser's notes on the application, not reviewer material.
        application_data.pop('tags', None)

        return {
            'review_form': serialize_form(review.form, language),
            'review_response': serialize_response(review),
            'application_form': serialize_form(application.form, language),
            'application_response': application_data,
            'applicant_user_id': application.user_id,
            'identifiers': identifiers(application, language),
            'status': review_status(review),
            'total_score': review.calculate_score(),
            'navigation': {
                'position': position + 1 if position is not None else None,
                'total': len(queue_ids),
                'remaining': len(pending_ids),
                'next_review_response_id': next_ids[0] if next_ids else None,
            },
        }, 200


class ReviewerHistoryAPI(restful.Resource):
    """Reviews the current reviewer has submitted for the event, all stages."""

    SORT_COLUMNS = {
        'review_response_id': FormResponse.id,
        'submitted_timestamp': FormResponse.submitted_timestamp,
    }

    @auth_required
    def get(self):
        event_id = request.args.get('event_id', type=int)
        if not event_id:
            return _error('event_id is required', 400)
        if not _require_reviewer(event_id):
            return errors.FORBIDDEN

        page_number = max(0, request.args.get('page_number', 0, type=int))
        limit = min(100, max(1, request.args.get('limit', 10, type=int)))
        sort_column = self.SORT_COLUMNS.get(request.args.get('sort_column'), FormResponse.submitted_timestamp)
        language = _language()

        form_ids = [f.id for f in form_system.get_review_forms(event_id)]
        query = db.session.query(FormResponse).filter(
            FormResponse.form_id.in_(form_ids or [-1]),
            FormResponse.user_id == g.current_user['id'],
            FormResponse.is_submitted == True,  # noqa: E712
            FormResponse.is_withdrawn == False,  # noqa: E712
        )
        num_entries = query.count()
        reviews = query.order_by(sort_column.desc(), FormResponse.id.desc()) \
            .offset(page_number * limit).limit(limit).all()

        return {
            'reviews': [{
                'review_response_id': r.id,
                'application_response_id': r.linked_response_id,
                'stage': r.form.stage,
                'identifiers': identifiers(r.linked_response, language) if r.linked_response else [],
                'submitted_timestamp': r.submitted_timestamp.isoformat() if r.submitted_timestamp else None,
                'total_score': r.calculate_score(),
            } for r in reviews],
            'num_entries': num_entries,
            'current_pagenumber': page_number,
            'total_pages': ceil(num_entries / limit) if num_entries else 0,
        }, 200


class ReviewDashboardAPI(restful.Resource):
    """Organisers' view of one review stage: every review with its scores, and
    every submitted application with its average scores."""

    @event_admin_required
    def get(self, form_id, event_id):
        try:
            review_form = _review_form_for_event(form_id, event_id)
            if review_form is None:
                return errors.FORM_NOT_FOUND

            language = _language()
            questions = score_questions(review_form, language)
            num_reviews_required = form_system.review_setting(review_form, 'num_reviews_required')

            reviews = (db.session.query(FormResponse)
                       .filter(FormResponse.form_id == review_form.id,
                               FormResponse.is_withdrawn == False)  # noqa: E712
                       .order_by(FormResponse.linked_response_id, FormResponse.id)
                       .all())
            reviews_data = [serialize_review(r, language) for r in reviews]

            applications = []
            if review_form.linked_form_id:
                submitted_apps = (db.session.query(FormResponse)
                                  .filter(FormResponse.form_id == review_form.linked_form_id,
                                          FormResponse.is_submitted == True,  # noqa: E712
                                          FormResponse.is_withdrawn == False)  # noqa: E712
                                  .order_by(FormResponse.id)
                                  .all())
                by_application = {}
                for data in reviews_data:
                    by_application.setdefault(data['application_response_id'], []).append(data)

                for app in submitted_apps:
                    app_reviews = by_application.get(app.id, [])
                    submitted = [r for r in app_reviews if r['status'] == 'submitted']
                    averages = {}
                    for q in questions:
                        values = [numeric_answer(r, q['question_id']) for r in submitted]
                        values = [v for v in values if v is not None]
                        averages[str(q['question_id'])] = sum(values) / len(values) if values else None
                    average_total = (sum(r['total_score'] for r in submitted) / len(submitted)) if submitted else None
                    applications.append({
                        'application_response_id': app.id,
                        'applicant': person(app.user),
                        'identifiers': identifiers(app, language),
                        'reviews_assigned': len(app_reviews),
                        'reviews_submitted': len(submitted),
                        'average_scores': averages,
                        'average_total': average_total,
                    })

            name = translation_for(review_form, language)
            return {
                'review_form_id': review_form.id,
                'application_form_id': review_form.linked_form_id,
                'form_name': name.name if name else None,
                'stage': review_form.stage,
                'num_reviews_required': num_reviews_required,
                'score_questions': questions,
                'reviews': reviews_data,
                'applications': applications,
            }, 200

        except Exception as e:
            LOGGER.error('Error building review dashboard for form {}: {}'.format(form_id, e))
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE


class ReviewFormStageAPI(restful.Resource):
    """List the event's review stages and choose which one is active."""

    @staticmethod
    def _payload(event_id):
        forms = form_system.get_review_forms(event_id)
        active = form_system.get_active_review_form(event_id)
        stages = []
        for form in forms:
            name = translation_for(form, _language())
            stages.append({
                'stage': form.stage,
                'form_id': form.id,
                'form_name': name.name if name else None,
                'is_active': active is not None and form.id == active.id,
            })
        return {
            'current_stage': active.stage if active else None,
            'stages': stages,
        }

    @event_admin_required
    def get(self, event_id):
        return self._payload(event_id), 200

    @event_admin_required
    def put(self, event_id):
        args = request.get_json() or {}
        stage = args.get('stage')
        if not isinstance(stage, int):
            return _error('stage must be a number', 400)
        if form_system.set_active_review_stage(event_id, stage) is None:
            return errors.FORM_NOT_FOUND
        db.session.commit()
        return self._payload(event_id), 200
