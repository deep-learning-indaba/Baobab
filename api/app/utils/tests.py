# -*- coding: utf-8 -*-

import json
from app.applicationModel.repository import ApplicationFormRepository as application_form_repository

from app.responses.repository import ResponseRepository as response_repository

from functools import partial

from app import LOGGER, app, db



from app.email_template.service import queue_email
from app.outbox.models import OutboxMessage
from app.utils.strings import build_response_html_answers, build_response_html_app_info
from app.utils.testing import ApiTestCase
from mock import patch



class EmailerTest(ApiTestCase):
    """Language and override resolution when queueing an email."""

    VERIFY = {'verification': 'https://example.org/verifyEmail?token=t'}

    def seed_static_data(self):
        def set_language(u, language):
            u.user_primaryLanguage = language

        self.english_user = self.add_user(email='english@person.com', post_create_fn=partial(set_language, language='en'))
        self.french_user = self.add_user(email='french@person.com', post_create_fn=partial(set_language, language='fr'))
        self.zulu_user = self.add_user(email='zulu@person.com', post_create_fn=partial(set_language, language='zu'))

        self.event = self.add_event(
            name={'en': 'English Event Name', 'fr': 'Nom de l\'événement en français'},
            description={'en': 'English Description', 'fr': 'Description en français'},
            languages=['en', 'fr']
        )
        self.add_email_template('verify-email', 'English template no event {{ verification.url }}', subject='English subject no event')
        self.add_email_template('verify-email', 'Modèle français sans événement', subject='Sujet français sans événement', language='fr')
        self.add_email_template('withdrawal', 'English template {{ event.name }}', subject='English subject {{ event.name }}', event_id=1)
        self.add_email_template('withdrawal', 'Modèle français {{ event.name }}', subject='Sujet français {{ event.name }}', language='fr', event_id=1)

    def _queued(self):
        db.session.commit()
        return db.session.query(OutboxMessage).order_by(OutboxMessage.id.desc()).first()

    def test_email_no_event_english(self):
        self.seed_static_data()
        queue_email('verify-email', self.english_user, context=self.VERIFY)
        message = self._queued()
        self.assertEqual(message.recipient, self.english_user.email)
        self.assertEqual(message.subject, 'English subject no event')
        self.assertEqual(message.body_text, 'English template no event https://example.org/verifyEmail?token=t')
        self.assertIsNone(message.event_id)

    def test_salutation_with_title(self):
        self.seed_static_data()
        self.add_email_template('withdrawal', 'Dear {{ recipient.salutation }},', event_id=None)
        queue_email('withdrawal', self.english_user, event=self.add_event(key='OTHER'))
        self.assertEqual(self._queued().body_text, 'Dear Mrs User Lastname,')

    def test_salutation_and_title_without_title(self):
        self.seed_static_data()
        self.english_user.user_title = None
        db.session.commit()
        self.add_email_template('withdrawal', 'Dear {{ recipient.salutation }}, [{{ recipient.title }}]', event_id=None)
        queue_email('withdrawal', self.english_user, event=self.add_event(key='OTHER'))
        self.assertEqual(self._queued().body_text, 'Dear User Lastname, []')

    def test_email_no_event_french(self):
        self.seed_static_data()
        queue_email('verify-email', self.french_user, context=self.VERIFY)
        message = self._queued()
        self.assertEqual(message.subject, 'Sujet français sans événement')
        self.assertEqual(message.body_text, 'Modèle français sans événement')

    def test_email_english_default(self):
        """A user whose language has no template gets English."""
        self.seed_static_data()
        queue_email('verify-email', self.zulu_user, context=self.VERIFY)
        message = self._queued()
        self.assertEqual(message.subject, 'English subject no event')
        self.assertEqual(message.language, 'en')

    def test_email_event_english(self):
        self.seed_static_data()
        queue_email('withdrawal', self.english_user, event=self.event)
        message = self._queued()
        self.assertEqual(message.subject, 'English subject English Event Name')
        self.assertEqual(message.body_text, 'English template English Event Name')

    def test_email_event_french(self):
        self.seed_static_data()
        queue_email('withdrawal', self.french_user, event=self.event)
        message = self._queued()
        self.assertEqual(message.subject, "Sujet français Nom de l'événement en français")
        self.assertEqual(message.body_text, "Modèle français Nom de l'événement en français")


class BuildResponseHTMLTest(ApiTestCase):
    """
    Test HTML builder functionality for the application information as well as 
    the question-answer mapping functionalities
    """

    def _seed_static_data(self):

        self.event1 = self.add_event(key='event1')
        self.event1admin = self.add_user('event1admin@mail.com', is_admin=True)
        self.user1 = self.add_user('user1@mail.com', user_title='Ms', firstname='Danai', lastname='Gurira')

        application_form = self.create_application_form(self.event1.id)
        self.application_form_id = application_form.id
        # Section 1, one question
        section1 = self.add_section(application_form.id)
        self.add_section_translation(section1.id, 'en', name='Section1')
        question1 = self.add_question(application_form.id, section1.id)
        self.add_question_translation(question1.id, 'en', headline='Question 1, S1')

        # Section 2, 1 question
        section2 = self.add_section(application_form.id)
        self.add_section_translation(section2.id, 'en', name='Section2')
        question2_1 = self.add_question(application_form.id, section2.id)
        self.add_question_translation(question2_1.id, 'en', headline='Question 1, S2')
 

        self.response = self.add_response(application_form.id, self.user1.id, is_submitted=True)
        self.response_submitted = self.response.submitted_timestamp
        self.response_started = self.response.started_timestamp
        self.response_id = self.response.id
        self.add_answer(self.response_id, question1.id, 'Section 1 Answer 1')

        self.add_answer(self.response_id, question2_1.id, 'Section 2 Answer 1')

        # Second response, same application form with missing answers
        self.response2 = self.add_response(application_form.id, self.user1.id, is_submitted=True)
        self.response_submitted = self.response2.submitted_timestamp
        self.response_started = self.response2.started_timestamp
        self.response_id2 = self.response2.id


    def test_build_response_html_answers(self):
        self._seed_static_data()

        application_form = application_form_repository.get_by_id(self.application_form_id)
        answers = response_repository.get_by_id(self.response_id).answers

        html_answer_string = build_response_html_answers(answers, 'en', application_form)
        
        self.assertIsNotNone(html_answer_string)

    def test_build_response_html_answers_with_answers_missing(self):
        """
        Tests that the builder doesn't break when a question is submitted without an answer
        """

        self._seed_static_data()

        application_form = application_form_repository.get_by_id(self.application_form_id)
        answers = response_repository.get_by_id(self.response_id2).answers

        html_string = build_response_html_answers(answers, 'en', application_form)
        
        self.assertIsNotNone(html_string)

    def test_build_response_html_app_info(self):
        
        self._seed_static_data()

        response = response_repository.get_by_id(self.response_id)
        
        html_info_string = build_response_html_app_info(response, 'en')
        
        self.assertIsNotNone(html_info_string)

