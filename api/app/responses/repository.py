from typing import List

from app import db
from app.responses.models import Response, Answer, ResponseTag, ResponseReviewer
from app.applicationModel.models import ApplicationForm, Question, Section
from app.users.models import AppUser
from sqlalchemy import func, cast, Date
import itertools


class ResponseRepository():

    @staticmethod
    def get_by_id(response_id):
        return db.session.query(Response).get(response_id)

    @staticmethod
    def save(response):
        db.session.add(response)
        db.session.commit()

    @staticmethod
    def save_answers(answers):
        db.session.add_all(answers)
        db.session.commit()

    @staticmethod
    def merge_answer(answer):
        db.session.merge(answer)
        db.session.commit()

    @staticmethod
    def get_by_id_and_user_id(response_id, user_id):
        return db.session.query(Response) \
            .filter_by(id=response_id, user_id=user_id) \
            .first()

    @staticmethod
    def get_by_user_id_for_event(user_id, event_id):
        return db.session.query(Response) \
            .filter_by(user_id=user_id) \
            .join(ApplicationForm, Response.application_form_id == ApplicationForm.id) \
            .filter_by(event_id=event_id) \
            .first()

    @staticmethod
    def get_submitted_by_user_id_for_event(user_id, event_id):
        return db.session.query(Response) \
            .filter_by(user_id=user_id, is_submitted=True) \
            .join(ApplicationForm, Response.application_form_id == ApplicationForm.id) \
            .filter_by(event_id=event_id) \
            .first()

    @staticmethod
    def get_answers_by_response_id(response_id):
        return db.session.query(Answer) \
            .filter_by(response_id=response_id, is_active=True) \
            .all()

    @staticmethod
    def get_answers_by_question_id(question_id):
        return db.session.query(Answer) \
            .filter_by(question_id=question_id, is_active=True) \
            .all()

    @staticmethod
    def get_all_for_user_application(user_id, application_form_id):
        return (db.session.query(Response)
                .filter(Response.application_form_id == application_form_id, Response.user_id == user_id)
                .all())

    @staticmethod
    def get_answer_by_question_id_and_response_id(question_id, response_id):
        return db.session.query(Answer) \
            .filter_by(question_id=question_id, response_id=response_id, is_active=True) \
            .first()

    @staticmethod
    def get_question_answers_by_section_key_and_response_id(section_key, response_id):
        return db.session.query(Question, Answer) \
            .join(Question, Question.id == Answer.question_id) \
            .join(Section, Question.section_id == Section.id) \
            .filter(Answer.response_id == response_id,
                    Answer.is_active == True,
                    Section.key == section_key) \
            .all()

    @staticmethod
    def get_answer_by_question_key_and_response_id(question_key, response_id):
        return db.session.query(Answer) \
            .join(Question, Question.id == Answer.question_id) \
            .filter(Question.key == question_key,
                    Answer.response_id == response_id,
                    Answer.is_active == True) \
            .first()

    @staticmethod
    def get_total_count_by_event(event_id):
        return (db.session.query(Response)
                .join(ApplicationForm, Response.application_form_id == ApplicationForm.id)
                .filter(ApplicationForm.event_id == event_id)
                .count())

    @staticmethod
    def get_submitted_count_by_event(event_id):
        return (db.session.query(Response)
                .filter(Response.is_submitted == True)
                .join(ApplicationForm, Response.application_form_id == ApplicationForm.id)
                .filter(ApplicationForm.event_id == event_id)
                .count())

    @staticmethod
    def get_withdrawn_count_by_event(event_id):
        return (db.session.query(Response)
                .filter(Response.is_withdrawn == True)
                .join(ApplicationForm, Response.application_form_id == ApplicationForm.id)
                .filter(ApplicationForm.event_id == event_id)
                .count())

    @staticmethod
    def get_submitted_timeseries_by_event(event_id):
        return (db.session.query(cast(Response.submitted_timestamp, Date), func.count(Response.submitted_timestamp))
                .filter(Response.is_submitted == True)
                .join(ApplicationForm, Response.application_form_id == ApplicationForm.id)
                .filter(ApplicationForm.event_id == event_id)
                .group_by(cast(Response.submitted_timestamp, Date))
                .order_by(cast(Response.submitted_timestamp, Date))
                .all())

    @staticmethod
    def get_all_for_event(event_id, submitted_only=True) -> List[Response]:
        query = db.session.query(Response)
        if submitted_only:
            query = query.filter_by(is_submitted=True)

        return (query
                .join(ApplicationForm, Response.application_form_id == ApplicationForm.id)
                .filter_by(event_id=event_id)
                .all())
        
    def get_all_for_action_editor(event_id, action_editor_id, submitted_only=True) -> List[Response]:
        query = db.session.query(Response)
        if submitted_only:
            query = query.filter_by(is_submitted=True)
        
        return (query
                .join(ApplicationForm, Response.application_form_id == ApplicationForm.id)
                .filter_by(event_id=event_id)
                .join(ResponseReviewer, Response.id == ResponseReviewer.response_id)
                .filter_by(reviewer_user_id=action_editor_id, is_action_editor=True)
                .all())

    @staticmethod
    def tag_response(response_id, tag_id):
        rt = ResponseTag(response_id, tag_id)
        db.session.add(rt)
        db.session.commit()
        return rt

    @staticmethod
    def remove_tag_from_response(response_id, tag_id):
        (db.session.query(ResponseTag)
         .filter_by(response_id=response_id, tag_id=tag_id)
         .delete())
        db.session.commit()

    @staticmethod
    def filter_ids_to_event(response_ids, event_id):
        ids = (db.session.query(Response.id)
               .filter(Response.id.in_(response_ids))
               .join(ApplicationForm, Response.application_form_id == ApplicationForm.id)
               .filter_by(event_id=event_id)
               .all())
        return itertools.chain.from_iterable(ids)
