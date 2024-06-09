from app.utils.testing import ApiTestCase
from app import db

class ReportingTest(ApiTestCase):
    
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
            
            self.user1, self.user2, self.user3, self.reviewer1, self.reviewer2, self.admin_user = self.add_n_users(6)
            self.add_event_role('admin', self.admin_user.id, self.event.id)
            self.user1_firstname, self.user1_lastname = self.user1.firstname, self.user1.lastname
            self.user2_firstname, self.user2_lastname = self.user2.firstname, self.user2.lastname
            self.user3_firstname, self.user3_lastname = self.user3.firstname, self.user3.lastname
            self.reviewer1_firstname, self.reviewer1_lastname = self.reviewer1.firstname, self.reviewer1.lastname
            self.reviewer2_firstname, self.reviewer2_lastname = self.reviewer2.firstname, self.reviewer2.lastname

            self.response1 = self.add_response(self.application_form.id, self.user1.id, is_submitted=True, language='en')
            self.response2 = self.add_response(self.application_form.id, self.user2.id, is_submitted=True, language='fr')
            self.response3 = self.add_response(self.application_form.id, self.user3.id, is_submitted=False, language='en')
            
            self.add_answer(self.response1.id, self.question1.id, 'John Doe')
            self.add_answer(self.response1.id, self.question2.id, 'Blue')
            self.add_answer(self.response2.id, self.question1.id, 'Jean Dupont')
            self.add_answer(self.response2.id, self.question2.id, 'Rouge')
            self.add_answer(self.response3.id, self.question1.id, 'Jane Doe')
            self.add_answer(self.response3.id, self.question2.id, 'Green')
            
            self.review_form = self.add_review_form(self.application_form.id)
            self.review_section1 = self.add_review_section(self.review_form.id)
            self.review_section1_translation_en = self.add_review_section_translation(self.review_section1.id, 'en', 'Review Section 1')
            self.review_section1_translation_fr = self.add_review_section_translation(self.review_section1.id, 'fr', 'Review Section 1 FR')

            self.review_question1 = self.add_review_question(self.review_section1.id)
            self.review_question1_translation_en = self.add_review_question_translation(self.review_question1.id, 'en', headline='How good are they?')
            self.review_question1_translation_fr = self.add_review_question_translation(self.review_question1.id, 'fr', headline='How good are they? FR')

            self.review_question2 = self.add_review_question(self.review_section1.id)
            self.review_question2_translation_en = self.add_review_question_translation(self.review_question2.id, 'en', headline='Any other comments?')
            self.review_question2_translation_fr = self.add_review_question_translation(self.review_question2.id, 'fr', headline='Any other comments? FR')

            self.response1_review1 = self.add_review_response(self.reviewer1.id, self.response1.id)
            self.response1_review2 = self.add_review_response(self.reviewer2.id, self.response1.id)

            self.response2_review1 = self.add_review_response(self.reviewer1.id, self.response2.id)
            self.response2_review2 = self.add_review_response(self.reviewer2.id, self.response2.id)

            self.response1_review1_answer1 = self.add_review_score(self.response1_review1.id, self.review_question1.id, '5')
            self.response1_review1_answer2 = self.add_review_score(self.response1_review1.id, self.review_question2.id, 'Good job!')

            self.response1_review2_answer1 = self.add_review_score(self.response1_review2.id, self.review_question1.id, '3')
            self.response1_review2_answer2 = self.add_review_score(self.response1_review2.id, self.review_question2.id, 'Could be better')

            self.response2_review1_answer1 = self.add_review_score(self.response2_review1.id, self.review_question1.id, '4')
            self.response2_review1_answer2 = self.add_review_score(self.response2_review1.id, self.review_question2.id, 'Good job!')

            self.response2_review2_answer1 = self.add_review_score(self.response2_review2.id, self.review_question1.id, '2')
            self.response2_review2_answer2 = self.add_review_score(self.response2_review2.id, self.review_question2.id, 'Could be better')

            self.tag1 = self.add_tag(self.event.id, tag_type='GRANT')
            self.tag2 = self.add_tag(self.event.id, tag_type='GRANT', names={'en': 'Tag 2 en', 'fr': 'Tag 2 fr'})

            self.offer1 = self.add_offer(self.user1.id, self.event.id, tags=[self.tag1, self.tag2])
            self.offer1_id = self.offer1.id
            self.offer2 = self.add_offer(self.user2.id, self.event.id, tags=[self.tag1])
            # User 2 has both an offer and is a guest, to check the de-duplication works
            self.add_invited_guest(self.user2.id, self.event.id, 'Guest', tags=[self.tag1])
            self.add_invited_guest(self.user3.id, self.event.id, 'Guest', tags=[self.tag2])

            self.registration_form = self.create_registration_form(self.event.id)
            self.registration_section1 = self.add_registration_section(self.registration_form.id)
            self.registration_question1 = self.add_registration_question(self.registration_form.id, self.registration_section1.id)
            self.registration_question2 = self.add_registration_question(self.registration_form.id, self.registration_section1.id, 'Question 2')
            
            self.registration1 = self.add_registration_response(self.offer1.id, self.registration_form.id, answers=[
                self.registration_answer(self.registration_question1.id, 'Answer 1'),
                self.registration_answer(self.registration_question2.id, 'Answer 2')
            ])
            self.registration2 = self.add_registration_response(self.offer2.id, self.registration_form.id, answers=[
                self.registration_answer(self.registration_question1.id, 'Answer 3'),
                self.registration_answer(self.registration_question2.id, 'Answer 4')
            ])

            self.guest_registration1 = self.add_guest_registration(self.user2.id, self.event.id, answers=[
                self.guest_registration_answer(self.registration_question1.id, 'Answer 5'),
                self.guest_registration_answer(self.registration_question2.id, 'Answer 6')
            ])
            self.guest_registration2 = self.add_guest_registration(self.user3.id, self.event.id, answers=[
                self.guest_registration_answer(self.registration_question1.id, 'Answer 7'),
                self.guest_registration_answer(self.registration_question2.id, 'Answer 8')
            ])

            db.session.flush()

        def test_get_application_response_report_en(self):
            response = self.app.get(
                f'/api/v1/reporting/applications?language=en&event_id={self.event.id}',
                headers=self.get_auth_header_for(self.admin_user.email, password='abcd')
            )

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

        def test_get_reviews_report(self):
            response = self.app.get(
                f'/api/v1/reporting/reviews?language=en&event_id={self.event.id}',
                headers=self.get_auth_header_for(self.admin_user.email, password='abcd')
            )
            
            self.assertEqual(200, response.status_code)

            print(response.json)
            self.assertEqual(8, len(response.json))

            response1_review1_answer1 = response.json[0]
            self.assertEqual('5', response1_review1_answer1['score'])
            self.assertEqual('How good are they?', response1_review1_answer1['question'])
            self.assertEqual('en', response1_review1_answer1['review_language'])
            self.assertEqual('Review Section 1', response1_review1_answer1['section'])
            self.assertEqual(self.user1_firstname, response1_review1_answer1['firstname'])
            self.assertEqual(self.user1_lastname, response1_review1_answer1['lastname'])
            self.assertEqual(self.reviewer1_firstname, response1_review1_answer1['reviewer_firstname'])
            self.assertEqual(self.reviewer1_lastname, response1_review1_answer1['reviewer_lastname'])

            response1_review1_answer2 = response.json[1]
            self.assertEqual('Good job!', response1_review1_answer2['score'])
            self.assertEqual('Any other comments?', response1_review1_answer2['question'])
            self.assertEqual('en', response1_review1_answer2['review_language'])
            self.assertEqual('Review Section 1', response1_review1_answer2['section'])
            self.assertEqual(self.user1_firstname, response1_review1_answer2['firstname'])
            self.assertEqual(self.user1_lastname, response1_review1_answer2['lastname'])
            self.assertEqual(self.reviewer1_firstname, response1_review1_answer2['reviewer_firstname'])
            self.assertEqual(self.reviewer1_lastname, response1_review1_answer2['reviewer_lastname'])

            response1_review2_answer1 = response.json[2]
            self.assertEqual('3', response1_review2_answer1['score'])
            self.assertEqual('How good are they?', response1_review2_answer1['question'])
            self.assertEqual('en', response1_review2_answer1['review_language'])
            self.assertEqual('Review Section 1', response1_review2_answer1['section'])
            self.assertEqual(self.user1_firstname, response1_review2_answer1['firstname'])
            self.assertEqual(self.user1_lastname, response1_review2_answer1['lastname'])
            self.assertEqual(self.reviewer2_firstname, response1_review2_answer1['reviewer_firstname'])
            self.assertEqual(self.reviewer2_lastname, response1_review2_answer1['reviewer_lastname'])

            response1_review2_answer2 = response.json[3]
            self.assertEqual('Could be better', response1_review2_answer2['score'])
            self.assertEqual('Any other comments?', response1_review2_answer2['question'])
            self.assertEqual('en', response1_review2_answer2['review_language'])
            self.assertEqual('Review Section 1', response1_review2_answer2['section'])
            self.assertEqual(self.user1_firstname, response1_review2_answer2['firstname'])
            self.assertEqual(self.user1_lastname, response1_review2_answer2['lastname'])
            self.assertEqual(self.reviewer2_firstname, response1_review2_answer2['reviewer_firstname'])
            self.assertEqual(self.reviewer2_lastname, response1_review2_answer2['reviewer_lastname'])

            response2_review1_answer1 = response.json[4]
            self.assertEqual('4', response2_review1_answer1['score'])
            self.assertEqual('How good are they?', response2_review1_answer1['question'])
            self.assertEqual('en', response2_review1_answer1['review_language'])
            self.assertEqual('Review Section 1', response2_review1_answer1['section'])
            self.assertEqual(self.user2_firstname, response2_review1_answer1['firstname'])
            self.assertEqual(self.user2_lastname, response2_review1_answer1['lastname'])
            self.assertEqual(self.reviewer1_firstname, response2_review1_answer1['reviewer_firstname'])
            self.assertEqual(self.reviewer1_lastname, response2_review1_answer1['reviewer_lastname'])

            response2_review1_answer2 = response.json[5]
            self.assertEqual('Good job!', response2_review1_answer2['score'])
            self.assertEqual('Any other comments?', response2_review1_answer2['question'])
            self.assertEqual('en', response2_review1_answer2['review_language'])
            self.assertEqual('Review Section 1', response2_review1_answer2['section'])
            self.assertEqual(self.user2_firstname, response2_review1_answer2['firstname'])
            self.assertEqual(self.user2_lastname, response2_review1_answer2['lastname'])
            self.assertEqual(self.reviewer1_firstname, response2_review1_answer2['reviewer_firstname'])
            self.assertEqual(self.reviewer1_lastname, response2_review1_answer2['reviewer_lastname'])

            response2_review2_answer1 = response.json[6]
            self.assertEqual('2', response2_review2_answer1['score'])
            self.assertEqual('How good are they?', response2_review2_answer1['question'])
            self.assertEqual('en', response2_review2_answer1['review_language'])
            self.assertEqual('Review Section 1', response2_review2_answer1['section'])
            self.assertEqual(self.user2_firstname, response2_review2_answer1['firstname'])
            self.assertEqual(self.user2_lastname, response2_review2_answer1['lastname'])
            self.assertEqual(self.reviewer2_firstname, response2_review2_answer1['reviewer_firstname'])
            self.assertEqual(self.reviewer2_lastname, response2_review2_answer1['reviewer_lastname'])

            response2_review2_answer2 = response.json[7]
            self.assertEqual('Could be better', response2_review2_answer2['score'])
            self.assertEqual('Any other comments?', response2_review2_answer2['question'])
            self.assertEqual('en', response2_review2_answer2['review_language'])
            self.assertEqual('Review Section 1', response2_review2_answer2['section'])
            self.assertEqual(self.user2_firstname, response2_review2_answer2['firstname'])
            self.assertEqual(self.user2_lastname, response2_review2_answer2['lastname'])
            self.assertEqual(self.reviewer2_firstname, response2_review2_answer2['reviewer_firstname'])
            self.assertEqual(self.reviewer2_lastname, response2_review2_answer2['reviewer_lastname'])

        def test_get_registrations_report(self):
            response = self.app.get(
                f'/api/v1/reporting/registrations?event_id={self.event.id}',
                headers=self.get_auth_header_for(self.admin_user.email, password='abcd')
            )
            
            self.assertEqual(200, response.status_code)

            self.assertEqual(3, len(response.json))

            guest_registration1 = response.json[0]
            self.assertEqual('Answer 5', guest_registration1['answers'][0]['answer'])
            self.assertEqual('Answer 6', guest_registration1['answers'][1]['answer'])
            self.assertEqual(self.user2_firstname, guest_registration1['firstname'])
            self.assertEqual(self.user2_lastname, guest_registration1['lastname'])
            self.assertEqual('guest', guest_registration1['type'])
            self.assertEqual('Guest', guest_registration1['role'])
            
            guest_registration2 = response.json[1]
            self.assertEqual('Answer 7', guest_registration2['answers'][0]['answer'])
            self.assertEqual('Answer 8', guest_registration2['answers'][1]['answer'])
            self.assertEqual(self.user3_firstname, guest_registration2['firstname'])
            self.assertEqual(self.user3_lastname, guest_registration2['lastname'])
            self.assertEqual('guest', guest_registration2['type'])
            self.assertEqual('Guest', guest_registration2['role'])

            registration1 = response.json[2]
            self.assertEqual('Answer 1', registration1['answers'][0]['answer'])
            self.assertEqual('Answer 2', registration1['answers'][1]['answer'])
            self.assertEqual(self.user1_firstname, registration1['firstname'])
            self.assertEqual(self.user1_lastname, registration1['lastname'])
            self.assertEqual('attendee', registration1['type'])
            self.assertEqual(self.offer1_id, registration1['offer_id'])
