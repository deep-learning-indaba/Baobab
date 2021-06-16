# -*- coding: latin-1 -*-

import json
from app.applicationModel.repository import ApplicationFormRepository as application_form_repository

from app.responses.repository import ResponseRepository as response_repository

from functools import partial

from app import LOGGER, app, db



from app.utils.emailer import email_user
from app.utils.strings import build_response_html_answers, build_response_html_app_info
from app.utils.testing import ApiTestCase
from mock import patch



class EmailerTest(ApiTestCase):
    """Test Emailer functionality."""

    def seed_static_data(self):
        def set_language(u, language):
            u.user_primaryLanguage = language

        self.english_user = self.add_user(email='english@person.com', post_create_fn=partial(set_language, language='en'))
        self.french_user = self.add_user(email='french@person.com', post_create_fn=partial(set_language, language='fr'))
        self.zulu_user = self.add_user(email='zulu@person.com', post_create_fn=partial(set_language, language='zu'))

        self.event = self.add_event(
            name={'en': 'English Event Name', 'fr': 'Nom de lévénement en français'},
            description={'en': 'English Description', 'fr': 'Description en français'}
        )
        self.add_email_template('template1', 'English template no event {param}', subject='English subject no event')
        self.add_email_template('template1', 'Modèle français sans événement {param}', subject='Sujet français sans événement', language='fr')
        self.add_email_template('template1', 'English template {event_name} {param}', subject='English subject {event_name}', event_id=1)
        self.add_email_template('template1', 'Modèle français {event_name} {param}', subject='Sujet français {event_name}', language='fr', event_id=1)

    @patch('app.utils.emailer.send_mail')
    def test_email_no_event_english(self, send_mail_fn):
        """Check email to an English user with no event."""
        self.seed_static_data()
        
        email_user('template1', template_parameters={'param': 'Blah'}, user=self.english_user)

        send_mail_fn.assert_called_with(
            recipient=self.english_user.email, 
            subject='English subject no event', 
            body_text='English template no event Blah', 
            file_name='', 
            file_path='')

    @patch('app.utils.emailer.send_mail')
    def test_email_no_event_french(self, send_mail_fn):
        """Check email to an French user with no event."""
        self.seed_static_data()
        
        email_user('template1', template_parameters={'param': 'bleu'}, user=self.french_user)

        send_mail_fn.assert_called_with(
            recipient=self.french_user.email, 
            subject='Sujet français sans événement', 
            body_text='Modèle français sans événement bleu', 
            file_name='', 
            file_path='')

    @patch('app.utils.emailer.send_mail')
    def test_email_english_default(self, send_mail_fn):
        """Check email to use with unsupported language defaults to English."""
        self.seed_static_data()
        
        email_user('template1', template_parameters={'param': 'Blah'}, user=self.zulu_user)

        send_mail_fn.assert_called_with(
            recipient=self.zulu_user.email, 
            subject='English subject no event', 
            body_text='English template no event Blah', 
            file_name='', 
            file_path='')

    @patch('app.utils.emailer.send_mail')
    def test_files(self, send_mail_fn):
        """Check that file parameters are correctly passed to send_mail function."""
        self.seed_static_data()
        
        email_user('template1', template_parameters={'param': 'Blah'}, user=self.english_user, 
                file_name='myfile.pdf', file_path='/long/way/home')

        send_mail_fn.assert_called_with(
            recipient=self.english_user.email, 
            subject='English subject no event', 
            body_text='English template no event Blah', 
            file_name='myfile.pdf', 
            file_path='/long/way/home')

    
    @patch('app.utils.emailer.send_mail')
    def test_email_event_english(self, send_mail_fn):
        """Check email to an English user with an event."""
        self.seed_static_data()
        
        email_user('template1', template_parameters={'param': 'Blah'}, user=self.english_user, event=self.event)

        send_mail_fn.assert_called_with(
            recipient=self.english_user.email, 
            subject='English subject English Event Name', 
            body_text='English template English Event Name Blah', 
            file_name='', 
            file_path='')

    @patch('app.utils.emailer.send_mail')
    def test_email_event_french(self, send_mail_fn):
        """Check email to an French user with an event."""
        self.seed_static_data()
        
        email_user('template1', template_parameters={'param': 'bleu'}, user=self.french_user, event=self.event)

        send_mail_fn.assert_called_with(
            recipient=self.french_user.email, 
            subject='Sujet français Nom de lévénement en français', 
            body_text='Modèle français Nom de lévénement en français bleu', 
            file_name='', 
            file_path='')

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

