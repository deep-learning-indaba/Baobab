from sqlalchemy.sql import func, exists
from sqlalchemy import and_
from app import db
from app.applicationModel.models import ApplicationForm
from app.responses.models import ResponseReviewer, Response
from app.reviews.models import ReviewResponse, ReviewForm
from app.users.models import AppUser
from app.events.models import EventRole

_GENDER_SQL = """SELECT 
	app_user.user_gender, count(*) as gender_count
FROM 
	app_user
	INNER JOIN response ON app_user.id = response.user_id
	INNER JOIN application_form ON response.application_form_id = application_form.id
WHERE 
	response.is_submitted IS TRUE
	AND response.is_withdrawn IS FALSE
	AND application_form.event_id = {event_id}
GROUP BY 
	app_user.user_gender"""

_REVIEW_SQL = """(SELECT 
	'reviews' as category, COUNT(*)*3 as number
FROM 
	response
	INNER JOIN application_form ON response.application_form_id = application_form.id
WHERE
	response.is_submitted = true
	AND response.is_withdrawn = false
	AND application_form.event_id = {event_id})
UNION
(SELECT
	'allocated' as category, COUNT(*)
FROM
	response_reviewer
	INNER JOIN response on response_reviewer.response_id = response.id
	INNER JOIN application_form ON response.application_form_id = application_form.id
WHERE
	application_form.event_id = {event_id}
)
UNION
(SELECT 
	'completed' as category, COUNT(*)
FROM 
	review_response
	INNER JOIN review_form on review_response.review_form_id = review_form.id
	INNER JOIN application_form on review_form.application_form_id = application_form.id
WHERE
	application_form.event_id = {event_id}
)
"""

class EventStatsRepository():
    
    @staticmethod
    def application_gender_counts(event_id):
        results = db.engine.execute(_GENDER_SQL.format(event_id=event_id))
        return {
            r.user_gender: r.gender_count
            for r in results
        }

    @staticmethod
    def review_counts(event_id):
        results = db.engine.execute(_REVIEW_SQL.format(event_id=event_id))
        data = {
            r.category: r.number
            for r in results
        }
        return {
            'Unallocated': data['reviews'] - data['allocated'],
            'Completed': data['completed'],
            'Not Started': data['allocated'] - data['completed']
        }
