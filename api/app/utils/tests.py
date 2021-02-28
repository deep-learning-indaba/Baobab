# -*- coding: latin-1 -*-
from app.utils.testing import ApiTestCase
from app.utils.emailer import email_user
from mock import patch
from functools import partial

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
    