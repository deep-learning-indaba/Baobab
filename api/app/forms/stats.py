"""Event dashboard figures for events on the new form system."""
from sqlalchemy import func
from sqlalchemy.orm import aliased

from app import db
from app.forms.models import FormResponse
from app.forms.system import review_setting
from app.invitedGuest.models import InvitedGuest
from app.utils.timeseries import daily_counts


def application_stats(app_form):
    if app_form is None:
        return {'total': 0, 'submitted': 0, 'withdrawn': 0, 'submitted_timeseries': []}
    responses = db.session.query(FormResponse).filter(FormResponse.form_id == app_form.id)
    submitted = responses.filter(FormResponse.is_submitted == True)  # noqa: E712
    return {
        'total': responses.count(),
        'submitted': submitted.count(),
        'withdrawn': responses.filter(FormResponse.is_withdrawn == True).count(),  # noqa: E712
        'submitted_timeseries': daily_counts(submitted, FormResponse.submitted_timestamp),
    }


def count_unallocated_reviews(review_form, tag_ids=()):
    """Reviews still to be assigned so that every submitted application
    (with all of `tag_ids`, if given) has the required number of reviewers."""
    if review_form is None or not review_form.linked_form_id:
        return 0
    num_reviews_required = review_setting(review_form, 'num_reviews_required')

    applications = db.session.query(FormResponse).filter(
        FormResponse.form_id == review_form.linked_form_id,
        FormResponse.is_submitted == True,  # noqa: E712
        FormResponse.is_withdrawn == False,  # noqa: E712
    ).all()
    if tag_ids:
        applications = [
            a for a in applications
            if set(tag_ids) <= {rt.tag_id for rt in a.response_tags}
        ]
    application_ids = [a.id for a in applications]
    if not application_ids:
        return 0

    assignment_counts = dict(
        db.session.query(FormResponse.linked_response_id, func.count(FormResponse.id))
        .filter(FormResponse.form_id == review_form.id,
                FormResponse.linked_response_id.in_(application_ids),
                FormResponse.is_withdrawn == False)  # noqa: E712
        .group_by(FormResponse.linked_response_id)
        .all()
    )
    assigned = sum(min(assignment_counts.get(aid, 0), num_reviews_required) for aid in application_ids)
    return len(application_ids) * num_reviews_required - assigned


def _unfinished_reviews_of_live_applications(reviews):
    """Unsubmitted reviews whose application hasn't been withdrawn. A withdrawn
    application leaves reviewers' queues, so its reviews will never be done."""
    application = aliased(FormResponse)
    return (reviews.filter(FormResponse.is_submitted == False)  # noqa: E712
            .join(application, application.id == FormResponse.linked_response_id)
            .filter(application.is_withdrawn == False))  # noqa: E712


def review_stats(review_form):
    if review_form is None:
        return {'required': 0, 'completed': 0, 'incomplete': 0, 'unallocated': 0, 'timeseries': []}
    reviews = db.session.query(FormResponse).filter(
        FormResponse.form_id == review_form.id,
        FormResponse.is_withdrawn == False,  # noqa: E712
    )
    completed = reviews.filter(FormResponse.is_submitted == True)  # noqa: E712
    return {
        'required': review_setting(review_form, 'num_reviews_required'),
        'completed': completed.count(),
        'incomplete': _unfinished_reviews_of_live_applications(reviews).count(),
        'unallocated': count_unallocated_reviews(review_form),
        'timeseries': daily_counts(completed, FormResponse.submitted_timestamp),
    }


def registration_stats(event_id, registration_form):
    """Submitted registrations, split into invited guests and everyone else
    (who registers through an accepted offer)."""
    guests = db.session.query(InvitedGuest.user_id).filter(InvitedGuest.event_id == event_id)
    num_guests = guests.count()
    if registration_form is None:
        return {'registrations': 0, 'guests': num_guests, 'registered_guests': 0}
    submitted = db.session.query(FormResponse).filter(
        FormResponse.form_id == registration_form.id,
        FormResponse.is_submitted == True,  # noqa: E712
        FormResponse.is_withdrawn == False,  # noqa: E712
    )
    registered_guests = submitted.filter(FormResponse.user_id.in_(guests.subquery())).count()
    return {
        'registrations': submitted.count() - registered_guests,
        'guests': num_guests,
        'registered_guests': registered_guests,
    }
