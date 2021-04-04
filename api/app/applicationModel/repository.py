from app import db
from app.applicationModel.models import ApplicationForm, Question, QuestionTranslation, Section, SectionTranslation
from app.events.models import Event


class ApplicationFormRepository():

    @staticmethod
    def get_by_id(id):
        return db.session.query(ApplicationForm).get(id)

    @staticmethod
    def get_by_event_id(event_id):
        return db.session.query(ApplicationForm)\
            .filter_by(event_id=event_id)\
            .first()

    def add(obj):
        db.session.add(obj)
        db.session.commit()
        return obj

    @staticmethod
    def get_questions_for_event(event_id):
        return (db.session.query(Question)
                    .join(ApplicationForm, Question.application_form_id == ApplicationForm.id)
                    .filter_by(event_id=event_id)
                    .join(Section, Question.section_id == Section.id)
                    .order_by(Section.order, Question.order)
                    .all())

    @staticmethod
    def delete_question(question_to_delete: Question):
        # Remove any dependencies
        for question in question_to_delete.application_form.questions:
            if question.depends_on_question_id == question_to_delete.id:
                question.depends_on_question_id = None
        for section in question_to_delete.application_form.sections:
            if section.depends_on_question_id == question_to_delete.id:
                section.depends_on_question_id = None

        db.session.commit()
        
        # Delete question and translations
        db.session.query(QuestionTranslation).filter_by(question_id=question_to_delete.id).delete()
        db.session.query(Question).filter_by(id=question_to_delete.id).delete()
        db.session.commit()

    @staticmethod
    def delete_section(section):
        db.session.query(SectionTranslation).filter_by(section_id=section.id).delete()

        for question in db.session.query(Question).filter_by(section_id=section.id).all():
            ApplicationFormRepository.delete_question(question)

        db.session.query(Section).filter_by(id=section.id).delete()
        db.session.commit()
