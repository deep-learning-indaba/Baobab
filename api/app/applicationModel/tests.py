import json
from datetime import datetime, timedelta

from app import LOGGER, db
from app.applicationModel.models import ApplicationForm, Question, Section
from app.applicationModel.repository import ApplicationFormRepository as application_form_repository
from app.events.models import Event, EventType
from app.organisation.models import Organisation
from app.utils.testing import ApiTestCase


class ApplicationFormApiTest(ApiTestCase):

    def setUp(self):
        super(ApplicationFormApiTest, self).setUp()
        self._seed_data()

    def _seed_data(self):
        self.test_user = self.add_user('something@email.com')

        self.add_organisation('IndabaX')
        start_time = datetime.now() + timedelta(days=30)
        end_time = datetime.now() + timedelta(days=60)

        self.event = self.add_event({'en': 'Test Event'}, {'en': 'Event Description'}, start_time, end_time)
        self.form = self.create_application_form(self.event.id, True, False)

        self.section = self.add_section(self.form.id, 1)
        self.section_translation_en = self.add_section_translation(self.section.id, 'en', 'Test Section', 'Test Description', ['no'])
        self.section_translation_fr = self.add_section_translation(self.section.id, 'fr', 'Section francaise', 'Description du test', ['non'])
        self.question = self.add_question(self.form.id, self.section.id, question_type='multi-choice')
        self.question_translation_en = self.add_question_translation(
            question_id=self.question.id,
            language='en',
            headline='English Headline',
            description='English Question Description',
            placeholder='English Placeholder',
            validation_regex='^\\W*(\\w+(\\W+|$)){0,150}$',
            validation_text='Enter a maximum of 150 words',
            options=[{'label': 'Yes', 'value': 'yes'}, {'label': 'No', 'value': 'no'}],
            show_for_values=['yes']
        )
        self.question_translation_fr = self.add_question_translation(
            question_id=self.question.id,
            language='fr',
            headline='Titre francais',
            description='Description de la question en Francais',
            placeholder='Espace reserve Francais',
            validation_regex='^\\W*(\\w+(\\W+|$)){0,200}$',
            validation_text='Entrez un maximum de 200 mots',
            options=[{'label': 'Oui', 'value': 'oui'}, {'label': 'Non', 'value': 'non'}],
            show_for_values=['oui']
        )

        self.section2 = self.add_section(self.form.id, 2)
        self.section_translation2_en = self.add_section_translation(self.section2.id, 'en', 'Test Section 2', 'Test Description 2')
        self.section_translation2_fr = self.add_section_translation(self.section2.id, 'fr', 'Section francaise 2', 'Description du test 2')
        self.question2 = self.add_question(self.form.id, self.section2.id, question_type='text')
        self.question_translation2_en = self.add_question_translation(self.question2.id, 'en', 'English Headline 2')
        self.question_translation2_fr = self.add_question_translation(self.question2.id, 'fr', 'Titre francais 2')

    def test_get_form_in_english(self):
        header = self.get_auth_header_for(self.test_user.email)
        response = self.app.get(
            '/api/v1/application-form',
            headers=header,
            query_string={'event_id': 1, 'language': 'en'}
        )
        data = json.loads(response.data)

        self.assertEqual(data['event_id'], 1)
        self.assertEqual(data['is_open'], True)
        self.assertEqual(data['nominations'], False)

        self.assertEqual(len(data['sections']), 2)
        self.assertEqual(data['sections'][0]['order'], 1)
        self.assertEqual(data['sections'][0]['depends_on_question_id'], None)

        self.assertEqual(data['sections'][0]['name'], 'Test Section')
        self.assertEqual(data['sections'][0]['description'], 'Test Description')
        self.assertEqual(data['sections'][0]['show_for_values'], ['no'])

        self.assertEqual(data['sections'][0]['questions'][0]['type'], 'multi-choice')
        self.assertEqual(data['sections'][0]['questions'][0]['order'], 1)
        self.assertEqual(data['sections'][0]['questions'][0]['is_required'], True)
        self.assertEqual(data['sections'][0]['questions'][0]['depends_on_question_id'], None)
        self.assertEqual(data['sections'][0]['questions'][0]['key'], None)

        self.assertEqual(data['sections'][0]['questions'][0]['description'], 'English Question Description')
        self.assertEqual(data['sections'][0]['questions'][0]['headline'], 'English Headline')
        self.assertEqual(data['sections'][0]['questions'][0]['options'], [{'label': 'Yes', 'value': 'yes'}, {'label': 'No', 'value': 'no'}])
        self.assertEqual(data['sections'][0]['questions'][0]['placeholder'], 'English Placeholder')
        self.assertEqual(data['sections'][0]['questions'][0]['validation_regex'], '^\\W*(\\w+(\\W+|$)){0,150}$')
        self.assertEqual(data['sections'][0]['questions'][0]['validation_text'], 'Enter a maximum of 150 words')
        self.assertEqual(data['sections'][0]['questions'][0]['show_for_values'], ['yes'])
        
    
    def test_get_form_in_french(self):
        header = self.get_auth_header_for(self.test_user.email)
        response = self.app.get(
            '/api/v1/application-form',
            headers=header,
            query_string={'event_id': 1, 'language': 'fr'}
        )
        data = json.loads(response.data)

        self.assertEqual(data['event_id'], 1)
        self.assertEqual(data['is_open'], True)
        self.assertEqual(data['nominations'], False)

        self.assertEqual(len(data['sections']), 2)
        self.assertEqual(data['sections'][0]['order'], 1)
        self.assertEqual(data['sections'][0]['depends_on_question_id'], None)

        self.assertEqual(data['sections'][0]['name'], 'Section francaise')
        self.assertEqual(data['sections'][0]['description'], 'Description du test')
        self.assertEqual(data['sections'][0]['show_for_values'], ['non'])

        self.assertEqual(data['sections'][0]['questions'][0]['type'], 'multi-choice')
        self.assertEqual(data['sections'][0]['questions'][0]['order'], 1)
        self.assertEqual(data['sections'][0]['questions'][0]['is_required'], True)
        self.assertEqual(data['sections'][0]['questions'][0]['depends_on_question_id'], None)
        self.assertEqual(data['sections'][0]['questions'][0]['key'], None)

        self.assertEqual(data['sections'][0]['questions'][0]['description'], 'Description de la question en Francais')
        self.assertEqual(data['sections'][0]['questions'][0]['headline'], 'Titre francais')
        self.assertEqual(data['sections'][0]['questions'][0]['options'], [{'label': 'Oui', 'value': 'oui'}, {'label': 'Non', 'value': 'non'}])
        self.assertEqual(data['sections'][0]['questions'][0]['placeholder'], 'Espace reserve Francais')
        self.assertEqual(data['sections'][0]['questions'][0]['validation_regex'], '^\\W*(\\w+(\\W+|$)){0,200}$')
        self.assertEqual(data['sections'][0]['questions'][0]['validation_text'], 'Entrez un maximum de 200 mots')
        self.assertEqual(data['sections'][0]['questions'][0]['show_for_values'], ['oui'])