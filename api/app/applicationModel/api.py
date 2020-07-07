from datetime import datetime
import traceback

import flask_restful as restful
import applicationModel.repository as app_repository
from flask_restful import reqparse, fields, marshal_with, marshal
from sqlalchemy.exc import SQLAlchemyError
from flask import g

from app.applicationModel.mixins import ApplicationFormMixin
from app.applicationModel.models import ApplicationForm, Question, Section
from app.users.repository import UserRepository as user_repository
from app.events.models import Event

from app.utils.auth import auth_required

from app.utils.errors import EVENT_NOT_FOUND, FORM_NOT_FOUND_BY_ID, APPLICATION_FORM_EXISTS, QUESTION_NOT_FOUND, \
    SECTION_NOT_FOUND, DB_NOT_AVAILABLE, FORM_NOT_FOUND, APPLICATIONS_CLOSED, FORBIDDEN

from app import db, bcrypt
from app import LOGGER


class ApplicationFormAPI(ApplicationFormMixin, restful.Resource):
    question_fields = {
        'id': fields.Integer,
        'type': fields.String,
        'description': fields.String,
        'headline': fields.String,
        'order': fields.Integer,
        'options': fields.Raw,
        'placeholder': fields.String,
        'validation_regex': fields.String,
        'validation_text': fields.String,
        'is_required': fields.Boolean,
        'depends_on_question_id': fields.Integer,
        'show_for_values': fields.Raw,
        'key': fields.String
    }

    section_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
        'order': fields.Integer,
        'questions': fields.List(fields.Nested(question_fields)),
        'depends_on_question_id': fields.Integer,
        'show_for_values': fields.Raw
    }

    form_fields = {
        'id': fields.Integer,
        'event_id': fields.Integer,
        'is_open': fields.Boolean,
        'deadline': fields.DateTime,
        'sections': fields.List(fields.Nested(section_fields)),
        'nominations': fields.Boolean
    }

    def get(self):
        LOGGER.debug('Received get request for application form')
        args = self.req_parser.parse_args()
        LOGGER.debug('Parsed Args for event_id: {}'.format(args))

        try:
            form = db.session.query(ApplicationForm).filter(ApplicationForm.event_id == args['event_id']).first()
            if (not form):
                LOGGER.warn('Form not found for event_id: {}'.format(args['event_id']))
                return FORM_NOT_FOUND

            if not form.is_open:
                return APPLICATIONS_CLOSED

            sections = db.session.query(Section).filter(
                Section.application_form_id == form.id).all()  # All sections in our form
            if (not sections):
                LOGGER.warn('Sections not found for event_id: {}'.format(args['event_id']))
                return SECTION_NOT_FOUND

            questions = db.session.query(Question).filter(
                Question.application_form_id == form.id).all()  # All questions in our form
            if (not questions):
                LOGGER.warn('Questions not found for  event_id: {}'.format(args['event_id']))
                return QUESTION_NOT_FOUND

            form.sections = sections

            for s in form.sections:
                s.questions = []
                for q in questions:
                    if (q.section_id == s.id):
                        s.questions.append(q)

            if (form):
                return marshal(form, self.form_fields)
            else:
                LOGGER.warn("Event not found for event_id: {}".format(args['event_id']))
                return EVENT_NOT_FOUND

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return DB_NOT_AVAILABLE
        except:
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return DB_NOT_AVAILABLE

    @auth_required
    def post(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']

        event = db.session.query(Event).get(event_id)
        if not event:
            return EVENT_NOT_FOUND

        user_id = g.current_user["id"]
        current_user = user_repository.get_by_id(user_id)
        if not current_user.is_admin:
            return FORBIDDEN

        app_form = app_repository.get_by_event_id(event_id)
        if app_form:
            return APPLICATION_FORM_EXISTS
        else:
            is_open = args['is_open']
            nominations = args['nominations']

            app_form = ApplicationForm(
                event_id,
                is_open,
                nominations
            )
            db.session.add(app_form)

        section_args = args['section']
        for s in section_args: # TODO: Confirm this makes sense / works
            section = Section(s)
            section = section(app_form.id)
            db.session.add(section)

        question_args = args['question']
        for q in question_args: # TODO: Confirm this makes sense / works
            question = Question(q)
            question = question(app_form.id, section.id)
            db.session.add(question)

        app_form = app_repository.get_by_id(app_form.id)
        return app_form, 201

    @auth_required
    def put(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']

        event = db.session.query(Event).get(event_id)
        if not event:
            return EVENT_NOT_FOUND

        user_id = g.current_user["id"]
        current_user = user_repository.get_by_id(user_id)
        if not current_user.is_admin:
            return FORBIDDEN

        app_form = app_repository.get_by_event_id(event_id)

        old_section = app_repository.get_sections_by_app_id(app_form.id)
        new_section_args = args['section']

        for s in new_section_args:  # TODO: Confirm this makes sense / works. Repeat for questions
            section = Section(s)
            new_section = section(app_form.id)
        if old_section(app_form.id) == new_section(app_form.id):
            old_section.update(new_section)
            db.session.commit()

        # except IntegrityError as e: # TODO confirm error messages / notification
        #     LOGGER.error("Application with id: {} already exists".format(app_form.id))
        #     return FORM_NOT_FOUND_BY_ID
        #
        # question.update
        # try:
        #     db.session.commit()
        #
        # except IntegrityError as e:
        #     LOGGER.error("Application with id: {} already exists".format(app_form.id))
        #     return FORM_NOT_FOUND_BY_ID

        return {'new_app_form': app_form}, 201
