"""Single-language events inside a multi-language organisation: content is served
in the viewer's language only when the event is authored in it, and otherwise in
the event's primary language."""
import json
from unittest.mock import patch

from app import db
from app.announcements.api import _enqueue
from app.announcements.models import Announcement, AnnouncementTranslation
from app.forms.models import (
    Form, FormSection, FormSectionTranslation,
    FormQuestion, FormQuestionTranslation, FormResponse
)
from app.organisation.models import Organisation
from app.outbox.models import OutboxMessage
from app.tags.models import Tag, TagTranslation, TagType
from app.users.models import AppUser
from app.utils.emailer import email_user
from app.utils.language import translation_for, user_language_for_event
from app.utils.testing import ApiTestCase
from app.events.models import Event


class EventLanguageTest(ApiTestCase):

    def seed_static_data(self):
        organisation = db.session.query(Organisation).get(1)
        organisation.languages = [
            {'code': 'en', 'description': 'English'},
            {'code': 'fr', 'description': 'French'},
        ]
        db.session.commit()

        self.english_event_id = self.add_event(
            {'en': 'English Event'}, {'en': 'English only'},
            key='ENONLY', languages=['en']).id
        self.french_event_id = self.add_event(
            {'fr': 'Evenement Francais'}, {'fr': 'Francais seulement'},
            key='FRONLY', languages=['fr']).id

        self.french_user = self.add_user('fr@user.com')
        self.french_user.user_primaryLanguage = 'fr'
        self.english_user = self.add_user('en@user.com')
        self.english_user.user_primaryLanguage = 'en'
        db.session.commit()
        self.french_user_id = self.french_user.id
        self.english_user_id = self.english_user.id
        self.admin_id = self.add_user('admin@user.com').id

    def _event(self, event_id):
        return db.session.query(Event).get(event_id)

    def _user(self, user_id):
        return db.session.query(AppUser).get(user_id)

    # ------------------------------------------------------------------
    # Language helpers
    # ------------------------------------------------------------------

    def test_user_language_for_event(self):
        self.seed_static_data()
        english_event = self._event(self.english_event_id)
        french_event = self._event(self.french_event_id)
        self.assertEqual(user_language_for_event(self._user(self.french_user_id), english_event), 'en')
        self.assertEqual(user_language_for_event(self._user(self.english_user_id), french_event), 'fr')
        self.assertEqual(user_language_for_event(self._user(self.french_user_id), french_event), 'fr')

    def test_translation_for_falls_back_to_existing_translation(self):
        self.seed_static_data()
        tag = Tag(event_id=self.french_event_id, tag_type=TagType.RESPONSE)
        db.session.add(tag)
        db.session.flush()
        db.session.add(TagTranslation(tag_id=tag.id, language='fr', name='Etiquette'))
        db.session.commit()

        self.assertIsNone(tag.get_translation('en'))
        self.assertEqual(translation_for(tag, 'en').name, 'Etiquette')
        self.assertEqual(tag.stringify_tag_name('en'), 'Etiquette')

    def test_event_name_falls_back_to_primary_language(self):
        self.seed_static_data()
        self.assertEqual(self._event(self.french_event_id).get_name('en'), 'Evenement Francais')
        self.assertEqual(self._event(self.english_event_id).get_description('fr'), 'English only')

    # ------------------------------------------------------------------
    # Emails
    # ------------------------------------------------------------------

    def _send(self, user_id, event_id):
        with patch('app.utils.emailer.send_mail') as send_mail:
            email_user('some-template', user=self._user(user_id), event=self._event(event_id))
        return send_mail.call_args.kwargs

    def test_french_user_gets_english_only_event_template(self):
        self.seed_static_data()
        self.add_email_template('some-template', template='Global French', language='fr',
                                subject='Sujet')
        self.add_email_template('some-template', template='Event English {event_name}', language='en',
                                subject='Subject {event_name}', event_id=self.english_event_id)

        sent = self._send(self.french_user_id, self.english_event_id)
        self.assertEqual(sent['body_text'], 'Event English English Event')
        self.assertEqual(sent['subject'], 'Subject English Event')

    def test_english_user_gets_french_only_event_content(self):
        self.seed_static_data()
        self.add_email_template('some-template', template='Global English {event_name}', language='en')
        self.add_email_template('some-template', template='Global French {event_name}', language='fr')

        sent = self._send(self.english_user_id, self.french_event_id)
        self.assertEqual(sent['body_text'], 'Global French Evenement Francais')

    # ------------------------------------------------------------------
    # Forms
    # ------------------------------------------------------------------

    def _build_choice_form(self, event_id, language):
        form = Form(event_id=event_id, created_by_user_id=self.admin_id, is_open=True, allow_edits=True)
        db.session.add(form)
        db.session.flush()
        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        db.session.add(FormSectionTranslation(form_section_id=section.id, language=language, name='S'))
        question = FormQuestion(form_id=form.id, section_id=section.id, order=1,
                                question_type='multi-choice', is_required=True)
        db.session.add(question)
        db.session.flush()
        db.session.add(FormQuestionTranslation(
            form_question_id=question.id, language=language, headline='Q',
            options=[{'value': 'a', 'label': 'A'}, {'value': 'b', 'label': 'B'}]))
        db.session.commit()
        return form.id, question.id

    def _create_response(self, form_id, email, language, answers):
        return self.app.post(
            f'/api/v1/forms/{form_id}/response',
            data=json.dumps({'language': language, 'answers': answers}),
            headers=self.get_auth_header_for(email),
            content_type='application/json')

    def test_response_records_event_language_not_ui_language(self):
        self.seed_static_data()
        form_id, question_id = self._build_choice_form(self.english_event_id, 'en')
        response = self._create_response(form_id, 'fr@user.com', 'fr',
                                         [{'question_id': question_id, 'value': 'a'}])
        self.assertEqual(response.status_code, 201, response.data)
        stored = db.session.query(FormResponse).filter_by(form_id=form_id).one()
        self.assertEqual(stored.language, 'en')

    def test_french_only_form_validates_options_for_english_user(self):
        self.seed_static_data()
        form_id, question_id = self._build_choice_form(self.french_event_id, 'fr')
        response = self._create_response(form_id, 'en@user.com', 'en',
                                         [{'question_id': question_id, 'value': 'not-an-option'}])
        self.assertEqual(response.status_code, 201, response.data)
        response_id = json.loads(response.data)['id']
        self.assertEqual(db.session.query(FormResponse).get(response_id).language, 'fr')

        submit = self.app.post(
            f'/api/v1/forms/{form_id}/responses/{response_id}/submit',
            data=json.dumps({}), headers=self.get_auth_header_for('en@user.com'),
            content_type='application/json')
        self.assertEqual(submit.status_code, 400)

    # ------------------------------------------------------------------
    # Announcements
    # ------------------------------------------------------------------

    def test_announcement_sent_in_event_language(self):
        self.seed_static_data()
        announcement = Announcement(event_id=self.english_event_id, created_by_user_id=self.admin_id)
        db.session.add(announcement)
        db.session.flush()
        translation = AnnouncementTranslation(announcement_id=announcement.id, language='en',
                                              title='Hello', body_markdown='English body')
        db.session.add(translation)
        db.session.commit()

        with patch('app.announcements.api._audience_user_ids', return_value=[self.french_user_id]):
            _enqueue(db.session.query(Announcement).get(announcement.id),
                     self._event(self.english_event_id), critical=True)

        email = db.session.query(OutboxMessage).filter_by(channel='email').one()
        self.assertEqual(email.subject, 'Hello')
        self.assertIn('English body', email.body_text)
