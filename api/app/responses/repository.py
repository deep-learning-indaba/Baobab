from app import db
from app.responses.models import Response, Answer
from app.applicationModel.models import Question, Section
from app.users.models import AppUser


class ResponseRepository():

    @staticmethod
    def get_by_id(response_id):
        return db.session.query(Response).get(response_id)


    @staticmethod
    def get_by_id_and_user_id(response_id, user_id):
        return db.session.query(Response)\
                         .filter_by(id=response_id, user_id=user_id)\
                         .first()

    @staticmethod
    def get_by_user_id(user_id, application_form_id):
        return db.session.query(Response)\
            .filter_by(user_id=user_id, application_form_id=application_form_id)\
            .all()

    @staticmethod
    def get_answers_by_response_id(response_id):
        return db.session.query(Answer)\
            .filter_by(response_id=response_id)\
            .all()

    @staticmethod
    def get_answers_by_question_id(question_id):
        return db.session.query(Answer)\
            .filter_by(question_id=question_id)\
            .all()

    @staticmethod
    def get_answer_by_question_id_and_response_id(question_id, response_id):
        return db.session.query(Answer)\
            .filter_by(question_id=question_id, response_id=response_id)\
            .first()

    @staticmethod
    def get_question_answers_by_section_key_and_response_id(section_key, response_id):
        return db.session.query(Question, Answer)\
            .join(Question, Question.id == Answer.question_id)\
            .join(Section, Question.section_id == Section.id)\
            .filter(Answer.response_id == response_id,
                    Section.key == section_key)\
            .all()

    @staticmethod
    def get_answer_by_question_key_and_response_id(question_key, response_id):
        return db.session.query(Answer)\
            .join(Question, Question.id == Answer.question_id)\
            .filter(Question.key == question_key,
                    Answer.response_id == response_id)\
            .first()
