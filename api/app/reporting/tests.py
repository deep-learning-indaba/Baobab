from app.utils.testing import ApiTestCase
from app import db

class ApplicationResponseReportAPITest(ApiTestCase):
    
        def setUp(self):
            super().setUp()
            self.add_organisation()
            self.event = self.add_event()
            self.application_form = self.create_application_form(self.event.id)
            self.section1 = self.add_section(self.application_form.id)
            self.section1_translation_en = self.add_section_translation(self.section1.id, 'en', 'Section 1')
            self.section1_translation_fr = self.add_section_translation(self.section1.id, 'fr', 'Section 1 FR')
            self.question1 = self.add_question(self.application_form.id, self.section1.id)
            self.question1_translation_en = self.add_question_translation(self.question1.id, 'en', 'What is your name?')
            self.question1_translation_fr = self.add_question_translation(self.question1.id, 'fr', 'What is your name? FR')

            self.section2 = self.add_section(self.application_form.id)
            self.section2_translation_en = self.add_section_translation(self.section2.id, 'en', 'Section 2')
            self.section2_translation_fr = self.add_section_translation(self.section2.id, 'fr', 'Section 2 FR')

            self.question2 = self.add_question(self.application_form.id, self.section2.id)
            self.question2_translation_en = self.add_question_translation(self.question2.id, 'en', 'What is your favourite colour?')
            self.question2_translation_fr = self.add_question_translation(self.question2.id, 'fr', 'What is your favourite colour? FR')
            
            self.user1, self.user2, self.user3, self.admin_user = self.add_n_users(4)
            self.add_event_role('admin', self.admin_user.id, self.event.id)

            self.response1 = self.add_response(self.application_form.id, self.user1.id, is_submitted=True, language='en')
            self.response2 = self.add_response(self.application_form.id, self.user2.id, is_submitted=True, language='fr')
            self.response3 = self.add_response(self.application_form.id, self.user3.id, is_submitted=False, language='en')
            
            self.add_answer(self.response1.id, self.question1.id, 'John Doe')
            self.add_answer(self.response1.id, self.question2.id, 'Blue')
            self.add_answer(self.response2.id, self.question1.id, 'Jean Dupont')
            self.add_answer(self.response2.id, self.question2.id, 'Rouge')
            self.add_answer(self.response3.id, self.question1.id, 'Jane Doe')
            self.add_answer(self.response3.id, self.question2.id, 'Green')

            db.session.flush()

        def test_get_application_response_report_en(self):
            response = self.app.get(
                f'/api/v1/reporting/applications?language=en&event_id={self.event.id}',
                headers=self.get_auth_header_for(self.admin_user.email, password='abcd')
            )

            print("response.json", response.json)
            print()

            self.assertEqual(200, response.status_code)
            self.assertEqual(4, len(response.json))  # 2 responses, 2 questions each
            self.assertEqual('John Doe', response.json[0]['answer'])
            self.assertEqual('Blue', response.json[1]['answer'])
            self.assertEqual('Jean Dupont', response.json[2]['answer'])
            self.assertEqual('Rouge', response.json[3]['answer'])
            self.assertEqual('en', response.json[0]['response_language'])
            self.assertEqual('fr', response.json[2]['response_language'])
            self.assertEqual('Section 1', response.json[0]['section'])
            self.assertEqual('Section 2', response.json[1]['section'])
            self.assertEqual('What is your name?', response.json[0]['question'])
            self.assertEqual('What is your favourite colour?', response.json[1]['question'])

        def test_get_application_response_report_fr(self):
            response = self.app.get(
                f'/api/v1/reporting/applications?language=fr&event_id={self.event.id}',
                headers=self.get_auth_header_for(self.admin_user.email, password='abcd')
            )
            self.assertEqual(200, response.status_code)
            self.assertEqual(4, len(response.json))
            self.assertEqual('John Doe', response.json[0]['answer'])
            self.assertEqual('Blue', response.json[1]['answer'])
            self.assertEqual('Jean Dupont', response.json[2]['answer'])
            self.assertEqual('Rouge', response.json[3]['answer'])
            self.assertEqual('en', response.json[0]['response_language'])
            self.assertEqual('fr', response.json[2]['response_language'])
            self.assertEqual('Section 1 FR', response.json[0]['section'])
            self.assertEqual('Section 2 FR', response.json[1]['section'])
            self.assertEqual('What is your name? FR', response.json[0]['question'])
            self.assertEqual('What is your favourite colour? FR', response.json[1]['question'])
