from datetime import datetime
import json
import copy
import itertools

from app import db, LOGGER
from app.utils.testing import ApiTestCase
from app.events.models import Event, EventRole
from app.users.models import AppUser, UserCategory, Country
from app.applicationModel.models import ApplicationForm, Question, Section
from app.responses.models import Response, Answer, ResponseReviewer

from app.references.models import ReferenceRequest, Reference
from app.references.repository import ReferenceRequestRepository as reference_request_repository
from app.reviews.models import ReviewForm, ReviewQuestion, ReviewResponse, ReviewScore, ReviewConfiguration

from app.reviews.models import ReviewForm, ReviewQuestion, ReviewQuestionTranslation, ReviewResponse, ReviewScore, ReviewConfiguration
from app.utils.errors import REVIEW_RESPONSE_NOT_FOUND, FORBIDDEN, USER_NOT_FOUND
from nose.plugins.skip import SkipTest
from app.organisation.models import Organisation

from parameterized import parameterized

class ReviewsApiTest(ApiTestCase):

    def seed_static_data(self):
        self.add_organisation('Deep Learning Indaba 2019', 'blah.png', 'blah_big.png')
        self.add_organisation('Deep Learning Indaba 2020', 'blah.png', 'blah_big.png')
        user_categories = [
            UserCategory('Honours'),
            UserCategory('Student'),
            UserCategory('MSc'),
            UserCategory('PhD')
        ]
        db.session.add_all(user_categories)
        db.session.commit()

        countries = [
            Country('Egypt'),
            Country('Botswana'),
            Country('Namibia'),
            Country('Zimbabwe'),
            Country('Mozambique'),
            Country('Ghana'),
            Country('Nigeria')
        ]
        db.session.add_all(countries)
        db.session.commit()

        reviewer1 = AppUser('r1@r.com', 'reviewer', '1', 'Mr', password='abc', organisation_id=1,)
        reviewer2 = AppUser('r2@r.com', 'reviewer', '2', 'Ms',  password='abc', organisation_id=1,)
        reviewer3 = AppUser('r3@r.com', 'reviewer', '3', 'Mr',  password='abc', organisation_id=1,)
        reviewer4 = AppUser('r4@r.com', 'reviewer', '4', 'Ms', password='abc', organisation_id=1,)
        candidate1 = AppUser('c1@c.com', 'candidate', '1', 'Mr',  password='abc', organisation_id=1,)
        candidate2 = AppUser('c2@c.com', 'candidate', '2', 'Ms',  password='abc', organisation_id=1,)
        candidate3 = AppUser('c3@c.com', 'candidate', '3', 'Mr',  password='abc', organisation_id=1,)
        candidate4 = AppUser('c4@c.com', 'candidate', '4', 'Ms',  password='abc', organisation_id=1,)
        system_admin = AppUser('sa@sa.com', 'system_admin', '1', 'Ms', password='abc', organisation_id=1, is_admin=True)
        event_admin = AppUser('ea@ea.com', 'event_admin', '1', 'Ms', password='abc',organisation_id=1)
        users = [reviewer1, reviewer2, reviewer3, reviewer4, candidate1, candidate2, candidate3, candidate4, system_admin, event_admin]
        for user in users:
            user.verify()
        db.session.add_all(users)
        db.session.commit()

        events = [
            self.add_event({'en': 'indaba 2019'}, {'en': 'The Deep Learning Indaba 2019, Kenyatta University, Nairobi, Kenya '}, datetime(2019, 8, 25), datetime(2019, 8, 31),
            'KENYADABA2019'),
            self.add_event({'en': 'indaba 2020'}, {'en': 'The Deep Learning Indaba 2018, Stellenbosch University, South Africa'}, datetime(2018, 9, 9), datetime(2018, 9, 15),
            'INDABA2020', 2)
        ]
        db.session.commit()

        event_roles = [
            EventRole('admin', 10, 1),
            EventRole('reviewer', 3, 1)
        ]
        db.session.add_all(event_roles)
        db.session.commit()

        application_forms = [
            self.create_application_form(1, True, False),
            self.create_application_form(2, False, False)
        ]
        db.session.add_all(application_forms)
        db.session.commit()

        sections = [
            Section(1, 1),
            Section(2, 1)
        ]
        db.session.add_all(sections)
        db.session.commit()

        options = [
            {
                "value": "indaba-2017",
                "label": "Yes, I attended the 2017 Indaba"
            },
            {
                "value": "indaba-2018",
                "label": "Yes, I attended the 2018 Indaba"
            },
            {
                "value": "indaba-2017-2018",
                "label": "Yes, I attended both Indabas"
            },
            {
                "value": "none",
                "label": "No"
            }
        ]
        questions = [
            Question(1, 1, 1, 'long_text'),
            Question(1, 1, 2, 'long_text'),
            Question(2, 2, 1, 'long_text'),
            Question(2, 2, 2, 'long_text'),
            Question(1, 1, 3, 'multi-choice')
        ]
        db.session.add_all(questions)
        db.session.commit()

        self.add_question_translation(1, 'en', 'Question 1')
        self.add_question_translation(2, 'en', 'Question 2')
        self.add_question_translation(3, 'en', 'Question 3')
        self.add_question_translation(4, 'en', 'Question 4')
        self.add_question_translation(5, 'en', 'Did you attend the 2017 or 2018 Indaba', options=options)

        closed_review = ReviewForm(2, datetime(2018, 4, 30), 1, True)
        closed_review.close()
        inactive_review = ReviewForm(2, datetime(2018, 4, 30), 2, False)
        review_forms = [
            ReviewForm(1, datetime(2019, 4, 30), 1, True),
            ReviewForm(1, datetime(2019, 4, 30), 2, False),
            closed_review,
            inactive_review
        ]
        db.session.add_all(review_forms)
        db.session.commit()

        review_configs = [
            ReviewConfiguration(review_form_id=review_forms[0].id, num_reviews_required=3, num_optional_reviews=0),
            ReviewConfiguration(review_form_id=review_forms[1].id, num_reviews_required=3, num_optional_reviews=0)
        ]
        db.session.add_all(review_configs)
        db.session.commit()

        review_section1 = self.add_review_section(review_forms[0].id)
        self.add_review_section_translation(review_section1.id, 'en', 'Review Section 1 English', 'Review Section 1 Description English')
        self.add_review_section_translation(review_section1.id, 'fr', 'Review Section 1 French', 'Review Section 1 Description French')
        review_section2 = self.add_review_section(review_forms[1].id)
        self.add_review_section_translation(review_section2.id, 'en', 'Review Section 2', 'Review Section 2 Description')

        review_questions = [
            ReviewQuestion(review_section1.id, 1, 'multi-choice', True, 1, 0),
            ReviewQuestion(review_section1.id, 2, 'multi-choice', True, 2, 0),
            ReviewQuestion(review_section2.id, 3, 'multi-choice', True, 1, 0),
            ReviewQuestion(review_section2.id, 4, 'information', False, 2, 0)
        ]
        db.session.add_all(review_questions)
        db.session.commit()

        review_question_translations = [
            ReviewQuestionTranslation(review_questions[0].id, 'en'),
            ReviewQuestionTranslation(review_questions[0].id, 'fr'),
            ReviewQuestionTranslation(review_questions[1].id, 'en', headline='English Headline', description='English Description', placeholder='English Placeholder', options=[{'label': 'en1', 'value': 'en'}], validation_regex='EN Regex', validation_text='EN Validation Message'),
            ReviewQuestionTranslation(review_questions[1].id, 'fr', headline='French Headline', description='French Description', placeholder='French Placeholder', options=[{'label': 'fr1', 'value': 'fr'}], validation_regex='FR Regex', validation_text='FR Validation Message'),
            ReviewQuestionTranslation(review_questions[2].id, 'en'),
            ReviewQuestionTranslation(review_questions[2].id, 'fr'),
            ReviewQuestionTranslation(review_questions[3].id, 'en'),
            ReviewQuestionTranslation(review_questions[3].id, 'fr'),
        ]
        db.session.add_all(review_question_translations)
        db.session.commit()

        self.add_email_template('reviews-assigned')

    def get_auth_header_for(self, email):
        body = {
            'email': email,
            'password': 'abc'
        }
        response = self.app.post('api/v1/authenticate', data=body)
        data = json.loads(response.data)
        header = {'Authorization': data['token']}
        return header

    def setup_one_reviewer_one_candidate(self, active=True):
        response = self.add_response(1, 5, is_submitted=True)

        answers = [
            Answer(1, 1, 'I will learn alot.'),
            Answer(1, 2, 'I will share by doing talks.')
        ]
        db.session.add_all(answers)
        db.session.commit()

        response_reviewers = [
            ResponseReviewer(1, 1) # assign reviewer 1 to candidate 1 response
        ]
        if not active:
            response_reviewers[0].deactivate()
        db.session.add_all(response_reviewers)
        db.session.commit()

    def test_one_reviewer_one_candidate(self):
        self.seed_static_data()
        self.setup_one_reviewer_one_candidate()
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1, 'language': 'en'}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 1)

    def test_one_reviewer_one_candidate_inactive(self):
        self.seed_static_data()
        self.setup_one_reviewer_one_candidate(active=False)
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1, 'language': 'en'}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 0)
        self.assertEqual(data['response']['id'], 0)

    @parameterized.expand([
        (True,), (False,)
    ])
    def test_one_reviewer_one_candidate_review_summary(self, active):
        self.seed_static_data()
        self.setup_one_reviewer_one_candidate(active=active)
        header = self.get_auth_header_for('ea@ea.com')
        params = {'event_id': 1}

        response = self.app.get('/api/v1/reviewassignment/summary', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_unallocated'], 2)

    def setup_responses_and_no_reviewers(self):
        response = self.add_response(1, 5, is_submitted=True)

        answers = [
            Answer(1, 1, 'I will learn alot.'),
            Answer(1, 2, 'I will share by doing talks.')
        ]
        db.session.add_all(answers)
        db.session.commit()

    def test_no_response_reviewers(self):
        self.seed_static_data()
        self.setup_responses_and_no_reviewers()
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1, 'language': 'en'}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 0)

    def test_no_response_reviewers_reviews_unallocated(self):
        self.seed_static_data()
        self.setup_responses_and_no_reviewers()
        header = self.get_auth_header_for('ea@ea.com')
        params = {'event_id': 1}
        response = self.app.get('/api/v1/reviewassignment/summary', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_unallocated'], 3)

    def setup_one_reviewer_three_candidates(self):
        self.add_response(application_form_id=1, user_id=5, is_submitted=True)
        self.add_response(application_form_id=1, user_id=6, is_submitted=True)
        self.add_response(application_form_id=1, user_id=7, is_submitted=True)

        answers = [
            Answer(1, 1, 'I will learn alot.'),
            Answer(1, 2, 'I will share by doing talks.'),
            Answer(2, 1, 'I want to do a PhD.'),
            Answer(2, 2, 'I will share by writing a blog.'),
            Answer(3, 1, 'I want to solve new problems.'),
            Answer(3, 2, 'I will share by tutoring.'),
        ]
        db.session.add_all(answers)
        db.session.commit()

        response_reviewers = [
            ResponseReviewer(1, 1),
            ResponseReviewer(2, 1),
            ResponseReviewer(3, 1)
        ]
        response_reviewers[1].deactivate()

        db.session.add_all(response_reviewers)
        db.session.commit()

    def test_one_reviewer_three_candidates(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates()
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1, 'language': 'en'}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 2)

    def setup_one_reviewer_three_candidates_and_one_completed_review(self):
        self.add_response(1, 5, is_submitted=True)
        self.add_response(1, 6, is_submitted=True)
        self.add_response(1, 7, is_submitted=True)

        answers = [
            Answer(1, 1, 'I will learn alot.'),
            Answer(1, 2, 'I will share by doing talks.'),
            Answer(2, 1, 'I want to do a PhD.'),
            Answer(2, 2, 'I will share by writing a blog.'),
            Answer(3, 1, 'I want to solve new problems.'),
            Answer(3, 2, 'I will share by tutoring.')
        ]
        db.session.add_all(answers)
        db.session.commit()

        response_reviewers = [
            ResponseReviewer(1, 1),
            ResponseReviewer(2, 1),
            ResponseReviewer(3, 1)
        ]
        db.session.add_all(response_reviewers)
        db.session.commit()

        review_response = ReviewResponse(1, 1, 1, 'en', False)
        review_response.submit()
        db.session.add(review_response)
        db.session.commit()

    def test_one_reviewer_three_candidates_and_one_completed_review(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates_and_one_completed_review()
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1, 'language': 'en'}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 2)

    def setup_one_reviewer_three_candidates_with_one_withdrawn_response_and_one_unsubmitted_response(self):
        withdrawn_response = self.add_response(1, 5, is_withdrawn=True)
        submitted_response = self.add_response(1, 7, is_submitted=True)
        self.add_response(1, 6)

        answers = [
            Answer(1, 1, 'I will learn alot.'),
            Answer(1, 2, 'I will share by doing talks.'),
            Answer(2, 1, 'I want to do a PhD.'),
            Answer(2, 2, 'I will share by writing a blog.'),
            Answer(3, 1, 'I want to solve new problems.'),
            Answer(3, 2, 'I will share by tutoring.')
        ]
        db.session.add_all(answers)
        db.session.commit()

        response_reviewers = [
            ResponseReviewer(1, 1),
            ResponseReviewer(2, 1),
            ResponseReviewer(3, 1)
        ]
        db.session.add_all(response_reviewers)
        db.session.commit()

    def test_one_reviewer_three_candidates_with_one_withdrawn_response_and_one_unsubmitted_response(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates_with_one_withdrawn_response_and_one_unsubmitted_response()
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1, 'language': 'en'}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 1)

    def setup_multiple_reviewers_with_different_subsets_of_candidates_and_reviews_completed(self):
        self.add_response(1, 5, is_submitted=True)
        self.add_response(1, 6, is_submitted=True)
        self.add_response(1, 7, is_submitted=True)
        self.add_response(1, 8, is_submitted=True)

        answers = [
            Answer(1, 1, 'I will learn alot.'),
            Answer(1, 2, 'I will share by doing talks.'),
            Answer(2, 1, 'I want to do a PhD.'),
            Answer(2, 2, 'I will share by writing a blog.'),
            Answer(3, 1, 'I want to solve new problems.'),
            Answer(3, 2, 'I will share by tutoring.'),
            Answer(4, 1, 'I want to exchange ideas with like minded people'),
            Answer(4, 2, 'I will mentor people interested in ML.')
        ]
        db.session.add_all(answers)
        db.session.commit()

        response_reviewers = [
            ResponseReviewer(1, 1),
            ResponseReviewer(2, 1),
            ResponseReviewer(3, 1),

            ResponseReviewer(2, 2),
            ResponseReviewer(3, 2),

            ResponseReviewer(1, 3),
            ResponseReviewer(2, 3),
            ResponseReviewer(3, 3),
            ResponseReviewer(4, 3),

            ResponseReviewer(1, 4),
            ResponseReviewer(2, 4)
        ]
        response_reviewers[-1].deactivate()
        db.session.add_all(response_reviewers)
        db.session.commit()

        review_responses = [
            ReviewResponse(1, 2, 2, 'en', False),
            ReviewResponse(1, 3, 1, 'en', False),
            ReviewResponse(1, 3, 2, 'en', False),
            ReviewResponse(1, 4, 1, 'en', False)
        ]
        for rr in review_responses:
            rr.submit()

        db.session.add_all(review_responses)
        db.session.commit()

    def test_multiple_reviewers_with_different_subsets_of_candidates_and_reviews_completed(self):
        self.seed_static_data()
        self.setup_multiple_reviewers_with_different_subsets_of_candidates_and_reviews_completed()
        params = {'event_id': 1, 'language': 'en'}

        header = self.get_auth_header_for('r1@r.com')
        response1 = self.app.get('/api/v1/review', headers=header, data=params)
        data1 = json.loads(response1.data)
        header = self.get_auth_header_for('r2@r.com')
        response2 = self.app.get('/api/v1/review', headers=header, data=params)
        data2 = json.loads(response2.data)
        header = self.get_auth_header_for('r3@r.com')
        response3 = self.app.get('/api/v1/review', headers=header, data=params)
        data3 = json.loads(response3.data)
        header = self.get_auth_header_for('r4@r.com')
        response4 = self.app.get('/api/v1/review', headers=header, data=params)
        data4 = json.loads(response4.data)

        self.assertEqual(data1['reviews_remaining_count'], 3)
        self.assertEqual(data2['reviews_remaining_count'], 1)
        self.assertEqual(data3['reviews_remaining_count'], 2)
        self.assertEqual(data4['reviews_remaining_count'], 0)

    def test_skipping(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates()
        params = {'event_id': 1, 'skip': 1, 'language': 'en'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['response']['user_id'], 7)
        self.assertEqual(data['response']['answers'][0]['value'], 'I want to solve new problems.')

    def test_high_skip_defaults_to_last_review(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates()
        params = {'event_id': 1, 'skip': 5, 'language': 'en'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['response']['user_id'], 7)
        self.assertEqual(data['response']['answers'][1]['value'], 'I will share by tutoring.')

    def setup_candidate_who_has_applied_to_multiple_events(self):
        user_id = 5

        self.add_response(application_form_id=1, user_id=user_id, is_submitted=True)
        self.add_response(application_form_id=2, user_id=user_id, is_submitted=True)

        answers = [
            Answer(1, 1, 'I will learn alot.'),
            Answer(1, 2, 'I will share by doing talks.'),
            Answer(2, 3, 'Yes I worked on a vision task.'),
            Answer(2, 4, 'Yes I want the travel award.')
        ]
        db.session.add_all(answers)
        db.session.commit()

        response_reviewers = [
            ResponseReviewer(1, 1),
            ResponseReviewer(2, 1)
        ]
        db.session.add_all(response_reviewers)
        db.session.commit()

    def test_filtering_on_event_when_candidate_has_applied_to_more_than(self):
        self.seed_static_data()
        self.setup_candidate_who_has_applied_to_multiple_events()
        params = {'event_id': 2, 'language': 'en'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 1)
        self.assertEqual(data['response']['user_id'], 5)
        self.assertEqual(data['response']['answers'][0]['value'], 'Yes I worked on a vision task.')

    def setup_multi_choice_answer(self):
        self.add_response(1, 5, is_submitted=True)

        answer = Answer(1, 5, 'indaba-2017')
        db.session.add(answer)
        db.session.commit()

        response_reviewer = ResponseReviewer(1, 1)
        db.session.add(response_reviewer)
        db.session.commit()

    def test_multi_choice_answers_use_label_instead_of_value(self):
        self.seed_static_data()
        self.setup_multi_choice_answer()
        params = {'event_id': 1, 'language': 'en'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)
        print(data)

        self.assertEqual(data['response']['answers'][0]['value'], 'Yes, I attended the 2017 Indaba')

    def test_review_response_not_found(self):
        self.seed_static_data()
        params = {'id': 55, 'language': 'en'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/reviewresponse', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, REVIEW_RESPONSE_NOT_FOUND[1])

    def setup_review_response(self):
        self.add_response(1, 5, is_submitted=True)

        answer = Answer(1, 1, 'To learn alot')
        db.session.add(answer)
        db.session.commit()

        self.review_response = ReviewResponse(1, 1, 1, 'en', False)
        self.review_response.review_scores.append(ReviewScore(1, 'answer1'))
        self.review_response.review_scores.append(ReviewScore(2, 'answer2'))
        db.session.add(self.review_response)
        db.session.commit()

        db.session.flush()

    def test_review_response(self):
        self.seed_static_data()
        self.setup_review_response()
        params = {'id': self.review_response.id, 'language': 'en'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/reviewresponse', headers=header, data=params)
        data = json.loads(response.data)

        print(data)

        self.assertEqual(data['review_form']['id'], 1)
        self.assertEqual(data['review_response']['reviewer_user_id'], 1)
        self.assertEqual(data['review_response']['response_id'], 1)
        self.assertEqual(data['review_response']['scores'][0]['value'], 'answer1')
        self.assertEqual(data['review_response']['scores'][1]['value'], 'answer2')

    def test_prevent_saving_review_response_reviewer_was_not_assigned_to_response(self):
        self.seed_static_data()
        params = json.dumps({'review_form_id': 1, 'response_id': 1, 'scores': [{'review_question_id': 1, 'value': 'test_answer'}], 'language': 'en', 'is_submitted': False})
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.post('/api/v1/reviewresponse', headers=header, data=params, content_type='application/json')

        self.assertEqual(response.status_code, FORBIDDEN[1])

    def test_can_still_submit_inactive_response_reviewer(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates()
        params = json.dumps({'review_form_id': 1, 'response_id': 2, 'scores': [{'review_question_id': 1, 'value': 'test_answer'}], 'language': 'en', 'is_submitted': True})
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.post('/api/v1/reviewresponse', headers=header, data=params, content_type='application/json')

        self.assertEqual(response.status_code, 201)

    def setup_response_reviewer(self):
        self.add_response(1, 5, is_submitted=True)

        response_reviewer = ResponseReviewer(1, 1)
        db.session.add(response_reviewer)
        db.session.commit()

    def test_saving_review_response(self):
        self.seed_static_data()
        self.setup_response_reviewer()
        params = json.dumps({'review_form_id': 1, 'response_id': 1, 'scores': [{'review_question_id': 1, 'value': 'test_answer'}], 'language': 'en', 'is_submitted': False})
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.post('/api/v1/reviewresponse', headers=header, data=params, content_type='application/json')

        review_scores = db.session.query(ReviewScore).filter_by(review_response_id=1, is_active=True).all()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(review_scores), 1)
        self.assertEqual(review_scores[0].value, 'test_answer')

    def setup_existing_review_response(self):
        self.add_response(1, 5, is_submitted=True)

        response_reviewer = ResponseReviewer(1, 1)
        db.session.add(response_reviewer)
        db.session.commit()

        review_response = ReviewResponse(1, 1, 1, 'en')
        review_response.submit()
        review_response.review_scores = [ReviewScore(1, 'test_answer1'), ReviewScore(2, 'test_answer2')]
        db.session.add(review_response)
        db.session.commit()

    def test_updating_review_response(self):
        self.seed_static_data()
        self.setup_existing_review_response()
        params = json.dumps({'review_form_id': 1, 'response_id': 1, 'scores': [{'review_question_id': 1, 'value': 'test_answer3'}, {'review_question_id': 2, 'value': 'test_answer4'}], 'language': 'en', 'is_submitted': True})
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.put('/api/v1/reviewresponse', headers=header, data=params, content_type='application/json')

        review_scores = db.session.query(ReviewScore).filter_by(review_response_id=1, is_active=True).order_by(ReviewScore.review_question_id).all()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(review_scores), 2)
        self.assertEqual(review_scores[0].value, 'test_answer3')
        self.assertEqual(review_scores[1].value, 'test_answer4')

    def test_user_cant_assign_responsesreviewer_without_system_or_event_admin_role(self):
        self.seed_static_data()
        params = {'event_id': 1, 'reviewer_user_email': 'r2@r.com', 'num_reviews': 10}
        header = self.get_auth_header_for('c1@c.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

        self.assertEqual(response.status_code, FORBIDDEN[1])

    def test_reviewer_not_found(self):
        self.seed_static_data()
        params = {'event_id': 1, 'reviewer_user_email': 'non_existent@user.com', 'num_reviews': 10}
        header = self.get_auth_header_for('sa@sa.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

        self.assertEqual(response.status_code, USER_NOT_FOUND[1])

    def test_add_reviewer_with_no_roles(self):
        self.seed_static_data()
        params = {'event_id': 1, 'reviewer_user_email': 'r1@r.com', 'num_reviews': 10}
        header = self.get_auth_header_for('ea@ea.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

        event_roles = db.session.query(EventRole).filter_by(user_id=1, event_id=1).all()
        self.assertEqual(len(event_roles), 1)
        self.assertEqual(event_roles[0].role, 'reviewer')

    def test_add_reviewer_with_a_role(self):
        self.seed_static_data()
        params = {'event_id': 1, 'reviewer_user_email': 'ea@ea.com', 'num_reviews': 10}
        header = self.get_auth_header_for('sa@sa.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

        event_roles = db.session.query(EventRole).filter_by(user_id=10, event_id=1).order_by(EventRole.id).all()
        self.assertEqual(len(event_roles), 2)
        self.assertEqual(event_roles[0].role, 'admin')
        self.assertEqual(event_roles[1].role, 'reviewer')

    def setup_responses_without_reviewers(self):
        self.add_response(1, 5, is_submitted=True)
        self.add_response(1, 6, is_submitted=True)
        self.add_response(1, 7, is_submitted=True)
        self.add_response(1, 8, is_submitted=True)

    def test_adding_first_reviewer(self):
        self.seed_static_data()
        self.setup_responses_without_reviewers()
        params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 4}
        header = self.get_auth_header_for('ea@ea.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)
        response_reviewers = db.session.query(ResponseReviewer).filter_by(reviewer_user_id=3).all()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response_reviewers), 4)

    def test_limit_of_num_reviews(self):
        self.seed_static_data()
        self.setup_responses_without_reviewers()
        params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
        header = self.get_auth_header_for('ea@ea.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

        response_reviewers = db.session.query(ResponseReviewer).filter_by(reviewer_user_id=3).all()
        self.assertEqual(len(response_reviewers), 3)

    def setup_reviewer_with_own_response(self):
        self.add_response(1, 3, is_submitted=True) # reviewer
        self.add_response(1, 5, is_submitted=True) # someone else

    def test_reviewer_does_not_get_assigned_to_own_response(self):
        self.seed_static_data()
        self.setup_reviewer_with_own_response()
        params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
        header = self.get_auth_header_for('ea@ea.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

        response_reviewers = db.session.query(ResponseReviewer).filter_by(reviewer_user_id=3).all()
        self.assertEqual(len(response_reviewers), 1)
        self.assertEqual(response_reviewers[0].response_id, 2)

    def setup_withdrawn_and_unsubmitted_responses(self):
        self.add_response(1, 5)
        self.add_response(1, 6, is_withdrawn=True)
        self.add_response(1, 7, is_submitted=True)

    def test_withdrawn_and_unsubmitted_responses_are_not_assigned_reviewers(self):
        self.seed_static_data()
        self.setup_withdrawn_and_unsubmitted_responses()
        params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
        header = self.get_auth_header_for('ea@ea.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

        response_reviewers = db.session.query(ResponseReviewer).filter_by(reviewer_user_id=3).all()
        self.assertEqual(len(response_reviewers), 1)
        self.assertEqual(response_reviewers[0].response_id, 3)

    def setup_response_with_three_reviewers(self):
        response = self.add_response(1, 5, is_submitted=True)

        response_reviewers = [
            ResponseReviewer(1, 1),
            ResponseReviewer(1, 2),
            ResponseReviewer(1, 4)
        ]
        db.session.add_all(response_reviewers)
        db.session.commit()

    def test_response_with_three_reviewers_does_not_get_assigned_another_reviewer(self):
        self.seed_static_data()
        self.setup_response_with_three_reviewers()
        params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
        header = self.get_auth_header_for('ea@ea.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

        response_reviewers = db.session.query(ResponseReviewer).filter_by(reviewer_user_id=3).all()
        self.assertEqual(len(response_reviewers), 0)

    def setup_responsereview_with_different_reviewer(self):
        self.add_response(1, 5, is_submitted=True)

        response_reviewer = ResponseReviewer(1, 1)
        db.session.add(response_reviewer)
        db.session.commit()

    def test_response_will_get_multiple_reviewers_assigned(self):
        self.seed_static_data()
        self.setup_responsereview_with_different_reviewer()
        params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
        header = self.get_auth_header_for('ea@ea.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)
        response_reviewers = db.session.query(ResponseReviewer).order_by(ResponseReviewer.reviewer_user_id).all()

        self.assertEqual(len(response_reviewers), 2)
        self.assertEqual(response_reviewers[0].reviewer_user_id, 1)
        self.assertEqual(response_reviewers[1].reviewer_user_id, 3)

    def setup_reviewer_is_not_assigned_to_response_more_than_once(self):
        self.add_response(1, 5, is_submitted=True)

    def setup_count_reviews_allocated_and_completed(self):
        db.session.add_all([
            EventRole('reviewer', 1, 1),
            EventRole('reviewer', 2, 1),
            EventRole('reviewer', 3, 1),
            EventRole('reviewer', 4, 1)
        ])

        self.add_response(1, 5, is_submitted=True) #1
        self.add_response(1, 6, is_submitted=True) #2
        self.add_response(1, 7, is_submitted=True) #3
        self.add_response(1, 8, is_submitted=True) #4
        self.add_response(2, 5, is_submitted=True) #5
        self.add_response(2, 6, is_submitted=True)  #6

        response_reviewers = [
            ResponseReviewer(1, 2),
            ResponseReviewer(2, 2),
            ResponseReviewer(3, 2),
            ResponseReviewer(4, 2),
            ResponseReviewer(6, 2),

            ResponseReviewer(2, 3),
            ResponseReviewer(4, 3),

            ResponseReviewer(3, 4),

            ResponseReviewer(5, 1),

        ]


        db.session.add_all(response_reviewers)
        # review form, review_user_id, response_id
        review_responses = [
            ReviewResponse(1, 3, 2, 'en', False),
            ReviewResponse(1, 3, 4, 'en', False),
            ReviewResponse(1, 2, 1, 'en', False),
            ReviewResponse(1, 2, 3, 'en', False),
            ReviewResponse(1, 2, 4, 'en', False),
            ReviewResponse(2, 1, 5, 'en', False),
            ReviewResponse(2, 2, 6, 'en', False)
        ]
        db.session.add_all(review_responses)

        db.session.commit()

        # response 1 - 1 review assigned - 1 complete
        # response 2 - 2 reviews - 1 complete
        # response 3 - 2 reviews - 1 complete
        # response 4 - 2 reviews - 1 complete
        # response 5 - 1 review - 1 complete
        # response 6 - 1 review - 1 complete

        # reviewer 1 - 1 review assigned (1 from event 2) - 1 complete
        # reviewer 2 - 5 reviews assigned (1 from event 2)- 3 complete
        # reviewer 3 - 2 reviews assigned - 2 complete
        # reviewer 4 - 1 review assigned - none complete

        # total assigned reviews: 9
        # total required review = 6*3 = 18
        # total unallocated: 18 - 9 = 9
        # total completed reviews: 6

    @SkipTest
    def test_count_reviews_allocated_and_completed(self):
        self.seed_static_data()
        self.setup_count_reviews_allocated_and_completed()
        header = self.get_auth_header_for('ea@ea.com')
        params = {'event_id': 1}

        response = self.app.get('/api/v1/reviewassignment', headers=header, data=params)

        data = json.loads(response.data)
        data = sorted(data, key=lambda k: k['email'])
        LOGGER.debug(data)
        self.assertEqual(len(data),3)
        self.assertEqual(data[0]['email'], 'r2@r.com')
        self.assertEqual(data[0]['reviews_allocated'], 4)
        self.assertEqual(data[0]['reviews_completed'], 3)
        self.assertEqual(data[1]['email'], 'r3@r.com')
        self.assertEqual(data[1]['reviews_allocated'], 2)
        self.assertEqual(data[1]['reviews_completed'], 2)
        self.assertEqual(data[2]['email'], 'r4@r.com')
        self.assertEqual(data[2]['reviews_allocated'], 1)
        self.assertEqual(data[2]['reviews_completed'], 0)

    def test_reviewer_is_not_assigned_to_response_more_than_once(self):
        self.seed_static_data()
        self.setup_reviewer_is_not_assigned_to_response_more_than_once()
        params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
        header = self.get_auth_header_for('ea@ea.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)
        response2 = self.app.post('/api/v1/reviewassignment', headers=header, data=params)
        response_reviewers = db.session.query(ResponseReviewer).all()

        self.assertEqual(len(response_reviewers), 1)

    def setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores(self):
        second_reviewer = EventRole('reviewer', 2, 1)
        db.session.add(second_reviewer)
        db.session.commit()

        users_id = [5,6,7]
        self.add_response(application_form_id=1, user_id=users_id[0], is_submitted=True)
        self.add_response(application_form_id=1, user_id=users_id[1], is_submitted=True)
        self.add_response(application_form_id=1, user_id=users_id[2], is_submitted=True)

        final_verdict_options = [
            {'label': 'Yes', 'value': 2},
            {'label': 'No', 'value': 0},
            {'label': 'Maybe', 'value': 1},
        ]
        verdict_question = ReviewQuestion(1, None, 'multi-choice', True, 3, 0)
        db.session.add(verdict_question)
        db.session.commit()
        verdict_question_translation = ReviewQuestionTranslation(verdict_question.id, 'en', headline='Final Verdict', options=final_verdict_options)
        db.session.add(verdict_question_translation)
        db.session.commit()

        review_responses = [
            ReviewResponse(1,3,1, 'en', False),
            ReviewResponse(1,3,2, 'en', False),
            ReviewResponse(1,2,1, 'en', False),
            ReviewResponse(1,2,2, 'en', False),
            ReviewResponse(1,3,3, 'en', False)
        ]
        review_responses[0].review_scores = [ReviewScore(1, '23'), ReviewScore(5, '1')]
        review_responses[1].review_scores = [ReviewScore(1, '55'), ReviewScore(5, '2')]
        review_responses[2].review_scores = [ReviewScore(1, '45'), ReviewScore(2, '67'), ReviewScore(5, 'No')]
        review_responses[3].review_scores = [ReviewScore(1, '220'), ReviewScore(5, '2')]
        review_responses[4].review_scores = [ReviewScore(1, '221'), ReviewScore(5, '1')]
        db.session.add_all(review_responses)
        db.session.commit()

        return users_id


    def test_review_history_returned(self):
        self.seed_static_data()
        users_id = self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(len(data['reviews']), 3)
        self.assertEqual(data['num_entries'], 3)

        self.assertEqual(data['reviews'][0]['review_response_id'], 1)
        self.assertEqual(data['reviews'][0]['reviewed_user_id'], str(users_id[0]))

        self.assertEqual(data['reviews'][1]['review_response_id'], 2)
        self.assertEqual(data['reviews'][1]['reviewed_user_id'], str(users_id[1]))

        self.assertEqual(data['reviews'][2]['review_response_id'], 5)
        self.assertEqual(data['reviews'][2]['reviewed_user_id'], str(users_id[2]))

    def test_brings_back_only_logged_in_reviewer_reviewresponses(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r2@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(len(data['reviews']), 2)
        self.assertEqual(data['reviews'][0]['review_response_id'], 3)
        self.assertEqual(data['reviews'][1]['review_response_id'], 4)

    def test_logged_in_user_not_reviewer(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('c1@c.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)

        self.assertEqual(response.status_code, FORBIDDEN[1])

    def setup_reviewer_with_no_reviewresponses(self):
        reviewer = EventRole('reviewer', 1, 1)
        db.session.add(reviewer)
        db.session.commit()

    def test_reviewer_with_no_reviewresponses(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()
        self.setup_reviewer_with_no_reviewresponses()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['num_entries'], 0)
        self.assertEqual(data['reviews'], [])

    def test_order_by_reviewresponseid(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews'][0]['review_response_id'], 1)
        self.assertEqual(data['reviews'][1]['review_response_id'], 2)
        self.assertEqual(data['reviews'][2]['review_response_id'], 5)

    def setup_reviewresponses_with_unordered_timestamps(self):
        final_verdict_options = [
            {'label': 'Yes', 'value': 2},
            {'label': 'No', 'value': 0},
            {'label': 'Maybe', 'value': 1},
        ]

        verdict_question = ReviewQuestion(1, None, 'multi-choice', True, 3, 0)
        db.session.add(verdict_question)
        db.session.commit()
        verdict_question_translation = ReviewQuestionTranslation(verdict_question.id, 'en', headline='Final Verdict', options=final_verdict_options)
        db.session.add(verdict_question_translation)
        db.session.commit()

        self.add_response(1, 5, is_submitted=True)
        self.add_response(1, 6, is_submitted=True)
        self.add_response(1, 7, is_submitted=True)

        review_response_1 = ReviewResponse(1,3,1, 'en', False)
        review_response_2 = ReviewResponse(1,3,2, 'en', False)
        review_response_3 = ReviewResponse(1,3,3, 'en', False)
        review_response_1.submitted_timestamp = datetime(2019, 1, 1)
        review_response_2.submitted_timestamp = datetime(2018, 1, 1)
        review_response_3.submitted_timestamp = datetime(2018, 6, 6)
        review_responses = [review_response_1, review_response_2, review_response_3]
        review_responses[0].review_scores = [ReviewScore(1, '67'), ReviewScore(5, 'Yes')]
        review_responses[1].review_scores = [ReviewScore(1, '23'), ReviewScore(5, 'Yes')]
        review_responses[2].review_scores = [ReviewScore(1, '53'), ReviewScore(5, 'Yes')]
        db.session.add_all(review_responses)
        db.session.commit()

    def test_order_by_submittedtimestamp(self):
        self.seed_static_data()
        self.setup_reviewresponses_with_unordered_timestamps()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'submitted_timestamp'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)
        LOGGER.debug(data)
        self.assertEqual(data['reviews'][0]['submitted_timestamp'], '2018-01-01T00:00:00')
        self.assertEqual(data['reviews'][1]['submitted_timestamp'], '2018-06-06T00:00:00')
        self.assertEqual(data['reviews'][2]['submitted_timestamp'], '2019-01-01T00:00:00')

    # TODO re-add these tests once we can get the info outside of AppUser
    @SkipTest
    def test_order_by_nationalitycountry(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'nationality_country'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews'][0]['nationality_country'], 'Botswana')
        self.assertEqual(data['reviews'][1]['nationality_country'], 'South Africa')
        self.assertEqual(data['reviews'][2]['nationality_country'], 'Zimbabwe')

    # TODO re-add these tests once we can get the info outside of AppUser
    @SkipTest
    def test_order_by_residencecountry(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'residence_country'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews'][0]['residence_country'], 'Egypt')
        self.assertEqual(data['reviews'][1]['residence_country'], 'Mozambique')
        self.assertEqual(data['reviews'][2]['residence_country'], 'Namibia')

    # TODO re-add these tests once we can get the info outside of AppUser
    @SkipTest
    def test_order_by_affiliation(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'affiliation'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews'][0]['affiliation'], 'RU')
        self.assertEqual(data['reviews'][1]['affiliation'], 'UFH')
        self.assertEqual(data['reviews'][2]['affiliation'], 'UWC')

    # TODO re-add these tests once we can get the info outside of AppUser
    @SkipTest
    def test_order_by_department(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'department'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews'][0]['department'], 'CS') # ascii ordering orders capital letters before lowercase
        self.assertEqual(data['reviews'][1]['department'], 'Chem')
        self.assertEqual(data['reviews'][2]['department'], 'Phys')

    @SkipTest
    def test_order_by_usercategory(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'user_category'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews'][0]['user_category'], 'Honours')
        self.assertEqual(data['reviews'][1]['user_category'], 'MSc')
        self.assertEqual(data['reviews'][2]['user_category'], 'Student')

    def setup_two_extra_responses_for_reviewer3(self):
        self.add_response(1, 8, is_submitted=True)
        self.add_response(1, 1, is_submitted=True)

        review_responses = [
            ReviewResponse(1,3,4, 'en', False),
            ReviewResponse(1,3,5, 'en', False)
        ]
        review_responses[0].review_scores = [ReviewScore(1, '89'), ReviewScore(5, 'Maybe')]
        review_responses[1].review_scores = [ReviewScore(1, '75'), ReviewScore(5, 'Yes')]
        db.session.add_all(review_responses)
        db.session.commit()

    def test_first_page_in_pagination(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()
        self.setup_two_extra_responses_for_reviewer3()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 2, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(len(data['reviews']), 2)
        self.assertEqual(data['num_entries'], 5)

        self.assertEqual(data['reviews'][0]['review_response_id'], 1)
        self.assertEqual(data['reviews'][1]['review_response_id'], 2)

    def test_middle_page_in_pagination(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()
        self.setup_two_extra_responses_for_reviewer3()

        params ={'event_id' : 1, 'page_number' : 1, 'limit' : 2, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(len(data['reviews']), 2)
        self.assertEqual(data['num_entries'], 5)

        self.assertEqual(data['reviews'][0]['review_response_id'], 5)
        self.assertEqual(data['reviews'][1]['review_response_id'], 6)

    def test_last_page_in_pagination(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()
        self.setup_two_extra_responses_for_reviewer3()

        params ={'event_id' : 1, 'page_number' : 2, 'limit' : 2, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(len(data['reviews']), 1)
        self.assertEqual(data['num_entries'], 5)
        self.assertEqual(data['reviews'][0]['review_response_id'], 7)

    def test_total_number_of_pages_greater_than_zero(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()
        self.setup_two_extra_responses_for_reviewer3()

        params ={'event_id' : 1, 'page_number' : 2, 'limit' : 2, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['total_pages'], 3)

    def test_total_number_of_pages_when_zero(self):
        self.seed_static_data()
        self.setup_reviewer_with_no_reviewresponses()

        params ={'event_id' : 1, 'page_number' : 2, 'limit' : 2, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['total_pages'], 0)


    def test_review_form_language(self):
        """Test that the review form questions are returned in the correct language."""
        self.seed_static_data()
        params ={'event_id' : 1, 'language': 'en'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        print(data['review_form']['review_sections'])

        self.assertEqual(data['review_form']['review_sections'][0]['headline'], 'Review Section 1 English')
        self.assertEqual(data['review_form']['review_sections'][0]['description'], 'Review Section 1 Description English')

        self.assertEqual(len(data['review_form']['review_sections'][0]['review_questions']), 2)

        self.assertEqual(data['review_form']['review_sections'][0]['review_questions'][1]['description'], 'English Description')
        self.assertEqual(data['review_form']['review_sections'][0]['review_questions'][1]['headline'], 'English Headline')
        self.assertEqual(data['review_form']['review_sections'][0]['review_questions'][1]['placeholder'], 'English Placeholder')
        self.assertDictEqual(data['review_form']['review_sections'][0]['review_questions'][1]['options'][0], {'label': 'en1', 'value': 'en'})
        self.assertEqual(data['review_form']['review_sections'][0]['review_questions'][1]['validation_regex'], 'EN Regex')
        self.assertEqual(data['review_form']['review_sections'][0]['review_questions'][1]['validation_text'], 'EN Validation Message')

        params ={'event_id' : 1, 'language': 'fr'}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['review_form']['review_sections'][0]['headline'], 'Review Section 1 French')
        self.assertEqual(data['review_form']['review_sections'][0]['description'], 'Review Section 1 Description French')

        self.assertEqual(len(data['review_form']['review_sections'][0]['review_questions']), 2)

        self.assertEqual(data['review_form']['review_sections'][0]['review_questions'][1]['description'], 'French Description')
        self.assertEqual(data['review_form']['review_sections'][0]['review_questions'][1]['headline'], 'French Headline')
        self.assertEqual(data['review_form']['review_sections'][0]['review_questions'][1]['placeholder'], 'French Placeholder')
        self.assertDictEqual(data['review_form']['review_sections'][0]['review_questions'][1]['options'][0], {'label': 'fr1', 'value': 'fr'})
        self.assertEqual(data['review_form']['review_sections'][0]['review_questions'][1]['validation_regex'], 'FR Regex')
        self.assertEqual(data['review_form']['review_sections'][0]['review_questions'][1]['validation_text'], 'FR Validation Message')


class ReviewListAPITest(ApiTestCase):

    def seed_static_data(self):
        self.event1 = self.add_event(key='event1')
        self.event2 = self.add_event(key='event2')

        self.reviewer1 = self.add_user('reviewer1@mail.com')
        self.reviewer2 = self.add_user('reviewer2@mail.com')
        self.event1.add_event_role('reviewer', self.reviewer1.id)
        self.event2.add_event_role('reviewer', self.reviewer1.id)
        self.event1.add_event_role('reviewer', self.reviewer2.id)
        self.event2.add_event_role('reviewer', self.reviewer2.id)

        self.user1 = self.add_user('user1@mail.com')
        user2 = self.add_user('user2@mail.com')
        user3 = self.add_user('user3@mail.com')
        user4 = self.add_user('user4@mail.com')

        application_form1 = self.create_application_form(self.event1.id)
        section1 = self.add_section(application_form1.id)
        question1 = self.add_question(application_form1.id, section1.id)
        question1.key = 'review-identifier'
        self.add_question_translation(question1.id, 'en', 'Headline 1 EN')
        self.add_question_translation(question1.id, 'fr', 'Headline 1 FR')
        question2 = self.add_question(application_form1.id, section1.id)
        question2.key = 'review-identifier'
        self.add_question_translation(question2.id, 'en', 'Headline 2 EN')
        self.add_question_translation(question2.id, 'fr', 'Headline 2 FR')
        question3 = self.add_question(application_form1.id, section1.id)
        self.add_question_translation(question3.id, 'en', 'Headline 3 EN')
        self.add_question_translation(question3.id, 'fr', 'Headline 3 FR')

        review_form1 = self.add_review_form(application_form1.id)

        review_form1_section1 = self.add_review_section(review_form1.id)
        self.add_review_section_translation(review_form1_section1.id, 'en', 'Review Section 1 en', 'Review Section 1 en')
        self.add_review_section_translation(review_form1_section1.id, 'fr', 'Review Section 1 fr', 'Review Section 1 fr')
        review_form1_section2 = self.add_review_section(review_form1.id)
        self.add_review_section_translation(review_form1_section2.id, 'en', 'Review Section 2 en', 'Review Section 2 en')
        self.add_review_section_translation(review_form1_section2.id, 'fr', 'Review Section 2 fr', 'Review Section 2 fr')

        review_form1_section2 = self.add_review_section(review_form1.id)
        review_q1 = self.add_review_question(review_form1_section1.id, weight=1)
        review_q1_translation_en = self.add_review_question_translation(review_q1.id, 'en', headline='Heading En')
        review_q1_translation_fr = self.add_review_question_translation(review_q1.id, 'fr', headline='Heading Fr')
        review_q2 = self.add_review_question(review_form1_section1.id, weight=0)
        review_q2_translation_en = self.add_review_question_translation(review_q2.id, 'en', headline='Heading En')
        review_q2_translation_fr = self.add_review_question_translation(review_q2.id, 'fr', headline='Heading Fr')
        review_q3 = self.add_review_question(review_form1_section2.id, weight=1)
        review_q3_translation_en = self.add_review_question_translation(review_q3.id, 'en', headline='Heading En')
        review_q3_translation_fr = self.add_review_question_translation(review_q3.id, 'fr', headline='Heading Fr')

        application_form2 = self.create_application_form(self.event2.id)
        review_form2 = self.add_review_form(application_form2.id)

        event1_response1 = self.add_response(application_form1.id, self.user1.id, is_submitted=True)
        self.add_answer(event1_response1.id, question1.id, 'First answer')
        self.add_answer(event1_response1.id, question2.id, 'Second answer')
        self.add_answer(event1_response1.id, question3.id, 'Third answer')

        event1_response2 = self.add_response(application_form1.id, user2.id, is_submitted=True, language='fr')
        self.add_answer(event1_response2.id, question1.id, 'Forth answer')
        self.add_answer(event1_response2.id, question2.id, 'Fifth answer')
        self.add_answer(event1_response2.id, question3.id, 'Sixth answer')

        event1_response3 = self.add_response(application_form1.id, user3.id, is_submitted=True)
        self.add_answer(event1_response3.id, question1.id, 'Seventh answer')
        self.add_answer(event1_response3.id, question2.id, 'Eigth answer')
        self.add_answer(event1_response3.id, question3.id, 'Ninth answer')

        event1_response4 = self.add_response(application_form1.id, user4.id, is_submitted=True, language='zu')
        self.add_answer(event1_response4.id, question1.id, 'Tenth answer')
        self.add_answer(event1_response4.id, question2.id, 'Eleventh answer')
        self.add_answer(event1_response4.id, question3.id, 'Twelfth answer')

        event2_response1 = self.add_response(application_form2.id, self.user1.id, is_submitted=True)
        event2_response2 = self.add_response(application_form2.id, user2.id, is_submitted=True, language='fr')
        event2_response3 = self.add_response(application_form2.id, user3.id, is_submitted=True)

        # Review 1 completed review
        self.add_response_reviewer(event1_response1.id, self.reviewer1.id)
        review_response1 = self.add_review_response(self.reviewer1.id, event1_response1.id, review_form1.id)
        review_response1.submit()
        self.add_review_score(review_response1.id, review_q1.id, 10.5)
        self.add_review_score(review_response1.id, review_q2.id, 100)
        self.add_review_score(review_response1.id, review_q3.id, 'Hello world')

        # Reviewer 1 incomplete review
        self.review_response1_submitted = review_response1.submitted_timestamp.isoformat()
        self.add_response_reviewer(event1_response2.id, self.reviewer1.id)
        review_response2 = self.add_review_response(self.reviewer1.id, event1_response2.id, review_form1.id)
        self.add_review_score(review_response2.id, review_q1.id, 13)

        # Reviewer 1 not started review
        self.add_response_reviewer(event1_response3.id, self.reviewer1.id)

        # Confounders
        self.add_response_reviewer(event1_response2.id, self.reviewer2.id)
        self.add_response_reviewer(event1_response3.id, self.reviewer2.id)
        self.add_response_reviewer(event2_response1.id, self.reviewer1.id)
        self.add_response_reviewer(event2_response2.id, self.reviewer2.id)

    def test_review_list(self):
        self.seed_static_data()
        params ={'event_id' : 1, 'language': 'en'}

        response = self.app.get(
            '/api/v1/reviewlist',
            headers=self.get_auth_header_for('reviewer1@mail.com'),
            data=params)

        data = json.loads(response.data)

        self.assertEqual(len(data), 3)

        self.assertEqual(data[0]['response_id'], 1)
        self.assertEqual(data[0]['language'], 'en')
        self.assertEqual(len(data[0]['information']), 2)
        self.assertEqual(data[0]['information'][0]['headline'], 'Headline 1 EN')
        self.assertEqual(data[0]['information'][0]['value'], 'First answer')
        self.assertEqual(data[0]['information'][1]['headline'], 'Headline 2 EN')
        self.assertEqual(data[0]['information'][1]['value'], 'Second answer')
        self.assertTrue(data[0]['started'])
        self.assertEqual(data[0]['submitted'], self.review_response1_submitted)
        self.assertEqual(data[0]['total_score'], 10.5)

        self.assertEqual(data[1]['response_id'], 2)
        self.assertEqual(data[1]['language'], 'fr')
        self.assertEqual(len(data[1]['information']), 2)
        self.assertEqual(data[1]['information'][0]['headline'], 'Headline 1 EN')
        self.assertEqual(data[1]['information'][0]['value'], 'Forth answer')
        self.assertEqual(data[1]['information'][1]['headline'], 'Headline 2 EN')
        self.assertEqual(data[1]['information'][1]['value'], 'Fifth answer')
        self.assertTrue(data[1]['started'])
        self.assertIsNone(data[1]['submitted'])
        self.assertEqual(data[1]['total_score'], 13)

        self.assertEqual(data[2]['response_id'], 3)
        self.assertEqual(data[2]['language'], 'en')
        self.assertEqual(len(data[2]['information']), 2)
        self.assertEqual(data[2]['information'][0]['headline'], 'Headline 1 EN')
        self.assertEqual(data[2]['information'][0]['value'], 'Seventh answer')
        self.assertEqual(data[2]['information'][1]['headline'], 'Headline 2 EN')
        self.assertEqual(data[2]['information'][1]['value'], 'Eigth answer')
        self.assertFalse(data[2]['started'])
        self.assertIsNone(data[2]['submitted'])
        self.assertEqual(data[2]['total_score'], 0.0)

class ResponseReviewerAssignmentApiTest(ApiTestCase):
    def seed_static_data(self):
        self.event = self.add_event(key='event1')
        self.event2 = self.add_event(key='event2')
        self.event_admin = self.add_user('eventadmin@mail.com')
        self.reviewer = self.add_user('reviewer@mail.com')
        self.reviewer_user_id = self.reviewer.id

        self.user1 = self.add_user('user1@mail.com')
        self.user2 = self.add_user('user2@mail.com')
        self.user3 = self.add_user('user3@mail.com')

        self.event.add_event_role('admin', self.event_admin.id)

        application_form = self.create_application_form(self.event.id)
        application_form2 = self.create_application_form(self.event2.id)
        self.response1 = self.add_response(application_form.id, self.user1.id, is_submitted=True)
        self.response2 = self.add_response(application_form.id, self.user2.id, is_submitted=True)
        self.response3 = self.add_response(application_form.id, self.user3.id, is_submitted=True)

        self.add_review_form(application_form.id)
        self.add_review_form(application_form2.id)

        self.event2_response_id = self.add_response(application_form2.id, self.user1.id, is_submitted=True).id

        self.add_email_template('reviews-assigned')

    def test_responses_assigned(self):
        self.seed_static_data()

        params = {'event_id' : 1, 'response_ids': [1, 2], 'reviewer_email': 'reviewer@mail.com'}

        response = self.app.post(
            '/api/v1/assignresponsereviewer',
            headers=self.get_auth_header_for('eventadmin@mail.com'),
            data=params)

        self.assertEqual(response.status_code, 201)

        response_reviewers = (db.session.query(ResponseReviewer)
                   .join(Response, ResponseReviewer.response_id == Response.id)
                   .filter_by(application_form_id=1).all())

        self.assertEqual(len(response_reviewers), 2)

        for rr in response_reviewers:
            self.assertEqual(rr.reviewer_user_id, self.reviewer_user_id)

    def test_response_for_different_event_forbidden(self):
        self.seed_static_data()

        params = {'event_id' : 1, 'response_ids': [1, 2, self.event2_response_id], 'reviewer_email': 'reviewer@mail.com'}

        response = self.app.post(
            '/api/v1/assignresponsereviewer',
            headers=self.get_auth_header_for('eventadmin@mail.com'),
            data=params)

        self.assertEqual(response.status_code, 403)

    def test_delete(self):
        """Test that a review assignment can be deleted."""
        self.seed_static_data()

        # Assign a reviewer
        response_id = self.response1.id
        self.add_response_reviewer(response_id, self.reviewer_user_id)

        params = {'event_id' : 1, 'response_id': self.response1.id, 'reviewer_user_id': self.reviewer_user_id}

        response = self.app.delete(
            '/api/v1/assignresponsereviewer',
            headers=self.get_auth_header_for('eventadmin@mail.com'),
            data=params)

        self.assertEqual(response.status_code, 200)

        # Check that it was actually deleted
        response_reviewer = db.session.query(ResponseReviewer).filter_by(response_id=response_id, reviewer_user_id=self.reviewer_user_id).first()
        self.assertIsNone(response_reviewer)

    def test_delete_not_allowed_if_completed(self):
        """Test that a review assignment can't be deleted if the review has been completed."""
        self.seed_static_data()

        # Assign a reviewer and create a review resposne
        response_id = self.response1.id
        self.add_response_reviewer(response_id, self.reviewer_user_id)
        self.add_review_response(self.reviewer_user_id, response_id)

        params = {'event_id' : 1, 'response_id': self.response1.id, 'reviewer_user_id': self.reviewer_user_id}

        response = self.app.delete(
            '/api/v1/assignresponsereviewer',
            headers=self.get_auth_header_for('eventadmin@mail.com'),
            data=params)

        self.assertEqual(response.status_code, 400)


class ReferenceReviewRequest(ApiTestCase):
    def static_seed_data(self):
        # User, country and organisation is set up by ApiTestCase
        self.first_user = self.add_user('firstuser@mail.com', 'First', 'User', 'Mx')

        self.event = self.add_event()

        self.system_admin = self.add_user('sa@sa.com', is_admin=True)
        non_admin_users = self.add_n_users(3)
        users = non_admin_users.append(self.system_admin)
        self.event.add_event_role('admin', 4),
        self.event.add_event_role('reviewer', 1),

        db.session.commit()

        application_form = [
            self.create_application_form(1, True, False),
        ]

        closed_review = ReviewForm(1, datetime(2018, 4, 30), 1, True)
        inactive_review = ReviewForm(1, datetime(2018, 4, 30), 2, False)
        closed_review.close()
        review_forms = [
            ReviewForm(1, datetime(2019, 4, 30), 1, True),
            ReviewForm(1, datetime(2019, 4, 30), 2, False),
            closed_review,
            inactive_review
        ]
        db.session.add_all(review_forms)
        db.session.commit()

        self.test_response = self.add_response(1, self.first_user.id, language='en', is_submitted=True)

        self.response_review = self.add_response_reviewer(self.test_response.id, self.first_user.id)

        self.first_headers = self.get_auth_header_for("firstuser@mail.com")

        db.session.flush()

    def test_get_reference_request_by_event_id(self):
        self.static_seed_data()
        reference_req = ReferenceRequest(1, 'Mr', 'John', 'Snow', 'Supervisor', 'common@email.com')
        reference_request_repository.create(reference_req)
        REFERENCE_DETAIL = {
            'token': reference_req.token,
            'uploaded_document': 'DOCT-UPLOAD-78999',
        }

        response = self.app.post(
            '/api/v1/reference', data=REFERENCE_DETAIL, headers=self.first_headers)
        self.assertEqual(response.status_code, 201)

        params = {'event_id': 1, 'language': 'en'}
        response = self.app.get('/api/v1/review', headers=self.get_auth_header_for('firstuser@mail.com'), data=params)

        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 8)
        self.assertEqual(len(data['references']), 1)
        self.assertDictEqual(data['references'][0], {
            u'title': u'Mr',
            u'firstname': u'John',
            u'lastname': u'Snow',
            u'relation': u'Supervisor',
            u'uploaded_document': u'DOCT-UPLOAD-78999',
        })

    def test_get_reference_request_with_two_references(self):
        """
        In this test, there are two references requested and submitted
        """
        self.static_seed_data()
        reference_req = ReferenceRequest(1, 'Mr', 'John', 'Snow', 'Supervisor', 'common@email.com')
        reference_req2 = ReferenceRequest(1, 'Mrs', 'Jane', 'Jones', 'Manager', 'jane@email.com')
        reference_request_repository.create(reference_req)
        reference_request_repository.create(reference_req2)

        REFERENCE_DETAIL = {
            'token': reference_req.token,
            'uploaded_document': 'DOCT-UPLOAD-78999',
        }
        REFERENCE_DETAIL_2 = {
            'token': reference_req2.token,
            'uploaded_document': 'DOCT-UPLOAD-78979',
        }
        response = self.app.post(
            '/api/v1/reference', data=REFERENCE_DETAIL, headers=self.first_headers)
        self.assertEqual(response.status_code, 201)

        response = self.app.post(
            '/api/v1/reference', data=REFERENCE_DETAIL_2, headers=self.first_headers)
        self.assertEqual(response.status_code, 201)

        params = {'event_id': 1, 'language': 'en'}
        response = self.app.get('/api/v1/review', headers=self.get_auth_header_for('firstuser@mail.com'), data=params)

        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 8)
        self.assertEqual(len(data['references']), 2)
        self.assertDictEqual(data['references'][0], {
            u'title': u'Mr',
            u'firstname': u'John',
            u'lastname': u'Snow',
            u'relation': u'Supervisor',
            u'uploaded_document': u'DOCT-UPLOAD-78999',
        })

        self.assertDictEqual(data['references'][1], {
            u'title': u'Mrs',
            u'firstname': u'Jane',
            u'lastname': u'Jones',
            u'relation': u'Manager',
            u'uploaded_document': u'DOCT-UPLOAD-78979',
        })

    def test_get_reference_not_yet_submitted(self):
        """
        In this test, a reference has been requested, but not yet submitted by the referee (id exists, but no reference yet)
        """
        self.static_seed_data()
        reference_req = ReferenceRequest(1, 'Mr', 'John', 'Snow', 'Supervisor', 'common@email.com')
        reference_request_repository.create(reference_req)

        params = {'event_id': 1, 'language': 'en'}
        response = self.app.get('/api/v1/review', headers=self.get_auth_header_for('firstuser@mail.com'), data=params)

        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 8)
        self.assertEqual(data.get('references', None), None)

    def test_get_reference_submitted_later(self):
        """
        In this test, a reference has been requested, but the reference is only submitted after the second check
        """
        self.static_seed_data()
        reference_req = ReferenceRequest(1, 'Mr', 'John', 'Snow', 'Supervisor', 'common@email.com')
        reference_request_repository.create(reference_req)

        params = {'event_id': 1, 'language': 'en'}

        REFERENCE_DETAIL = {
            'token': reference_req.token,
            'uploaded_document': 'DOCT-UPLOAD-78999',
        }

        response = self.app.get('/api/v1/review', headers=self.get_auth_header_for('firstuser@mail.com'),
                                data=params)

        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 8)
        self.assertEqual(data.get('references', None), None)

        response = self.app.post(
            '/api/v1/reference', data=REFERENCE_DETAIL, headers=self.first_headers)
        self.assertEqual(response.status_code, 201)

        params = {'event_id': 1, 'language': 'en'}
        response = self.app.get('/api/v1/review', headers=self.get_auth_header_for('firstuser@mail.com'), data=params)

        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 8)
        self.assertEqual(len(data['references']), 1)
        self.assertDictEqual(data['references'][0], {
            u'title': u'Mr',
            u'firstname': u'John',
            u'lastname': u'Snow',
            u'relation': u'Supervisor',
            u'uploaded_document': u'DOCT-UPLOAD-78999',
        })

    def test_two_references_only_one_submitted(self):
        """
        In this test, two references have been requested, but only one submitted (two ids exists, one reference submitted)
        """
        self.static_seed_data()
        reference_req = ReferenceRequest(1, 'Mr', 'John', 'Snow', 'Supervisor', 'common@email.com')
        reference_req2 = ReferenceRequest(1, 'Mrs', 'Jane', 'Jones', 'Manager', 'jane@email.com')
        reference_request_repository.create(reference_req)
        reference_request_repository.create(reference_req2)

        REFERENCE_DETAIL_2 = {
            'token': reference_req2.token,
            'uploaded_document': 'DOCT-UPLOAD-78979',
        }

        response = self.app.post(
            '/api/v1/reference', data=REFERENCE_DETAIL_2, headers=self.first_headers)
        self.assertEqual(response.status_code, 201)

        params = {'event_id': 1, 'language': 'en'}
        response = self.app.get('/api/v1/review', headers=self.get_auth_header_for('firstuser@mail.com'), data=params)

        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 8)
        self.assertEqual(len(data['references']), 1)

        self.assertDictEqual(data['references'][0], {
            u'title': u'Mrs',
            u'firstname': u'Jane',
            u'lastname': u'Jones',
            u'relation': u'Manager',
            u'uploaded_document': u'DOCT-UPLOAD-78979',
        })

    def test_get_review_no_reference(self):
        """
        In this test, there is no reference attached to the application at all for review (i.e. no reference request)
        """
        self.static_seed_data()

        params = {'event_id': 1, 'language': 'en'}
        response = self.app.get('/api/v1/review', headers=self.get_auth_header_for('firstuser@mail.com'), data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 8)
        self.assertEqual(data.get('references', None), None)


class ReviewResponseDetailListApiTest(ApiTestCase):
    def seed_static_data(self):
        self.user1 = self.add_user('user1@mail.com', 'Jane', 'Bloggs', 'Ms')
        self.user2 = self.add_user('user2@mail.com', 'Alex', 'Person', 'Dr')
        self.reviewer = self.add_user('reviewer@mail.com', 'Joe', 'Soap', 'Mr')
        self.reviewer2 = self.add_user('reviewer2@mail.com', 'Jenny', 'Sharp', 'Ms')
        self.event_admin = self.add_user('event_admin@mail.com')

        self.event = self.add_event()
        self.event2 = self.add_event(key='Empty')
        self.event.add_event_role('admin', self.event_admin.id)
        self.event2.add_event_role('admin', self.event_admin.id)

        self.application_form = self.create_application_form(self.event.id)
        self.section = self.add_section(self.application_form.id)
        self.question1 = self.add_question(
            self.application_form.id,
            self.section.id,
            order=1,
            key='review-identifier')
        self.question_translation1 = self.add_question_translation(
            self.question1.id,
            'en',
            'Organisation')
        self.question2 = self.add_question(
            self.application_form.id,
            self.section.id,
            order=2,
            key='review-identifier')
        self.question_translation2 = self.add_question_translation(
            self.question2.id,
            'en',
            'Country')
        self.question3 = self.add_question(
            self.application_form.id,
            self.section.id,
            order=3,
        )
        self.question_translation3 = self.add_question_translation(
            self.question3.id,
            'en',
            'Non-review question'
        )

        self.response1 = self.add_response(
            self.application_form.id,
            self.user1.id,
            is_submitted=True)
        self.answer1 = self.add_answer(self.response1.id, self.question1.id, 'Pets R Us')
        self.answer2 = self.add_answer(self.response1.id, self.question2.id, 'Nigeria')
        self.answer3 = self.add_answer(self.response1.id, self.question3.id, 'Non-review answer')

        self.response2 = self.add_response(
            self.application_form.id,
            self.user2.id,
            is_submitted=True)
        self.answer4 = self.add_answer(self.response2.id, self.question1.id, 'Nokia')
        self.answer5 = self.add_answer(self.response2.id, self.question2.id, 'South Africa')
        self.answer6 = self.add_answer(self.response2.id, self.question3.id, 'Non-review answer 2')

        self.review_form = self.add_review_form(self.application_form.id)
        self.review_section1 = self.add_review_section(self.review_form.id)
        self.review_section1_translation1 = self.add_review_section_translation(
            self.review_section1.id,
            'en')
        self.review_section2 = self.add_review_section(self.review_form.id)
        self.review_section2_translation1 = self.add_review_section_translation(
            self.review_section2.id,
            'en'
            'Review Section 2',
            'Review Section 2 Description')
        self.review_question1 = self.add_review_question(self.review_section1.id, type='short-text', weight=1)
        self.review_question_translation1 = self.add_review_question_translation(
            self.review_question1.id,
            'en',
            headline='Ethical Considerations',
            description="How ethical is the candidate's proposal from 1 to 5?")
        self.review_question2 = self.add_review_question(self.review_section1.id, type='long-text', weight=0)
        self.review_question_translation2 = self.add_review_question_translation(
            self.review_question2.id,
            'en',
            headline=None,
            description='Comments for the candidate'
        )
        self.review_question3 = self.add_review_question(self.review_section2.id, type='multi-choice', weight=2)
        self.review_question_translation3 = self.add_review_question_translation(
            self.review_question3.id,
            'en',
            headline=None,
            description='What is your overall rating?'
        )
        self.review_question4 = self.add_review_question(self.review_section2.id, type='checkbox', weight=0)
        self.review_question_translation4 = self.add_review_question_translation(
            self.review_question4.id,
            'en',
            headline='Yes/No Question'
        )

        self.review_response1 = self.add_review_response(
            self.reviewer.id,
            self.response1.id,
            self.review_form.id,
            is_submitted=True)
        self.review_score1 = self.add_review_score(self.review_response1.id, self.review_question1.id, '4')
        self.review_score2 = self.add_review_score(self.review_response1.id, self.review_question2.id, 'This is a very good proposal')
        self.review_score3 = self.add_review_score(self.review_response1.id, self.review_question3.id, '5')
        self.review_score4 = self.add_review_score(self.review_response1.id, self.review_question4.id, 'Yes')

        self.review_response2 = self.add_review_response(
            self.reviewer2.id,
            self.response2.id,
            self.review_form.id,
            is_submitted=True)
        self.review_score5 = self.add_review_score(self.review_response2.id, self.review_question1.id, '3')
        self.review_score6 = self.add_review_score(self.review_response2.id, self.review_question2.id, 'Not bad!')
        self.review_score7 = self.add_review_score(self.review_response2.id, self.review_question3.id, '3')
        self.review_score8 = self.add_review_score(self.review_response2.id, self.review_question4.id, 'No')

    def test_not_authed(self):
        response = self.app.get('/api/v1/reviewresponsedetaillist')
        self.assertEqual(response.status_code, 401)

    def test_not_event_admin(self):
        self.seed_static_data()

        response = self.app.get(
            '/api/v1/reviewresponsedetaillist',
            headers=self.get_auth_header_for('user1@mail.com'),
            data={'event_id': 1}
        )

        self.assertEqual(response.status_code, 403)

    def test_no_review_responses(self):
        self.seed_static_data()

        response = self.app.get(
            '/api/v1/reviewresponsedetaillist',
            headers=self.get_auth_header_for('event_admin@mail.com'),
            data={'event_id': 2, 'language': 'en'}
        )
        data = json.loads(response.data)

        print(data)

        self.assertEqual(data, [])

    def test_review_responses_for_event(self):
        self.seed_static_data()

        response = self.app.get(
            '/api/v1/reviewresponsedetaillist',
            headers=self.get_auth_header_for('event_admin@mail.com'),
            data={'event_id': 1, 'language': 'en'}
        )

        data = json.loads(response.data)

        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['review_response_id'], 1)
        self.assertEqual(data[0]['response_id'], 1)

        self.assertEqual(data[0]['reviewer_user_title'], 'Mr')
        self.assertEqual(data[0]['reviewer_user_firstname'], 'Joe')
        self.assertEqual(data[0]['reviewer_user_lastname'], 'Soap')

        self.assertEqual(data[0]['response_user_title'], 'Ms')
        self.assertEqual(data[0]['response_user_firstname'], 'Jane')
        self.assertEqual(data[0]['response_user_lastname'], 'Bloggs')

        self.assertEqual(len(data[0]['identifiers']), 2)
        self.assertEqual(data[0]['identifiers'][0]['headline'], 'Organisation')
        self.assertEqual(data[0]['identifiers'][0]['value'], 'Pets R Us')
        self.assertEqual(data[0]['identifiers'][1]['headline'], 'Country')
        self.assertEqual(data[0]['identifiers'][1]['value'], 'Nigeria')

        self.assertEqual(len(data[0]['scores']), 3)
        self.assertEqual(data[0]['scores'][0]['headline'], 'Ethical Considerations')
        self.assertEqual(data[0]['scores'][0]['description'], "How ethical is the candidate's proposal from 1 to 5?")
        self.assertEqual(data[0]['scores'][0]['type'], 'short-text')
        self.assertEqual(data[0]['scores'][0]['value'], '4')
        self.assertEqual(data[0]['scores'][0]['weight'], 1)

        self.assertEqual(data[0]['scores'][1]['headline'], None)
        self.assertEqual(data[0]['scores'][1]['description'], 'Comments for the candidate')
        self.assertEqual(data[0]['scores'][1]['type'], 'long-text')
        self.assertEqual(data[0]['scores'][1]['value'], 'This is a very good proposal')
        self.assertEqual(data[0]['scores'][1]['weight'], 0)

        self.assertEqual(data[0]['scores'][2]['headline'], None)
        self.assertEqual(data[0]['scores'][2]['description'], 'What is your overall rating?')
        self.assertEqual(data[0]['scores'][2]['type'], 'multi-choice')
        self.assertEqual(data[0]['scores'][2]['value'], '5')
        self.assertEqual(data[0]['scores'][2]['weight'], 2)

        self.assertEqual(data[0]['total'], 14)


        self.assertEqual(data[1]['review_response_id'], 2)
        self.assertEqual(data[1]['response_id'], 2)

        self.assertEqual(data[1]['reviewer_user_title'], 'Ms')
        self.assertEqual(data[1]['reviewer_user_firstname'], 'Jenny')
        self.assertEqual(data[1]['reviewer_user_lastname'], 'Sharp')

        self.assertEqual(data[1]['response_user_title'], 'Dr')
        self.assertEqual(data[1]['response_user_firstname'], 'Alex')
        self.assertEqual(data[1]['response_user_lastname'], 'Person')

        self.assertEqual(len(data[1]['identifiers']), 2)
        self.assertEqual(data[1]['identifiers'][0]['headline'], 'Organisation')
        self.assertEqual(data[1]['identifiers'][0]['value'], 'Nokia')
        self.assertEqual(data[1]['identifiers'][1]['headline'], 'Country')
        self.assertEqual(data[1]['identifiers'][1]['value'], 'South Africa')

        self.assertEqual(len(data[1]['scores']), 3)
        self.assertEqual(data[1]['scores'][0]['headline'], 'Ethical Considerations')
        self.assertEqual(data[1]['scores'][0]['description'], "How ethical is the candidate's proposal from 1 to 5?")
        self.assertEqual(data[1]['scores'][0]['type'], 'short-text')
        self.assertEqual(data[1]['scores'][0]['value'], '3')
        self.assertEqual(data[1]['scores'][0]['weight'], 1)

        self.assertEqual(data[1]['scores'][1]['headline'], None)
        self.assertEqual(data[1]['scores'][1]['description'], 'Comments for the candidate')
        self.assertEqual(data[1]['scores'][1]['type'], 'long-text')
        self.assertEqual(data[1]['scores'][1]['value'], 'Not bad!')
        self.assertEqual(data[1]['scores'][1]['weight'], 0)

        self.assertEqual(data[1]['scores'][2]['headline'], None)
        self.assertEqual(data[1]['scores'][2]['description'], 'What is your overall rating?')
        self.assertEqual(data[1]['scores'][2]['type'], 'multi-choice')
        self.assertEqual(data[1]['scores'][2]['value'], '3')
        self.assertEqual(data[1]['scores'][2]['weight'], 2)

        self.assertEqual(data[1]['total'], 9)


class ReviewResponseSummaryListApiTest(ApiTestCase):
    def seed_static_data(self):
        self.user1 = self.add_user('user1@mail.com', 'Jane', 'Bloggs', 'Ms')
        self.user2 = self.add_user('user2@mail.com', 'Alex', 'Person', 'Dr')
        self.reviewer = self.add_user('reviewer@mail.com', 'Joe', 'Soap', 'Mr')
        self.reviewer2 = self.add_user('reviewer2@mail.com', 'Jenny', 'Sharp', 'Ms')
        self.event_admin = self.add_user('event_admin@mail.com')

        self.event = self.add_event()
        self.event2 = self.add_event(key='Empty')
        self.event.add_event_role('admin', self.event_admin.id)
        self.event2.add_event_role('admin', self.event_admin.id)

        self.application_form = self.create_application_form(self.event.id)
        self.section = self.add_section(self.application_form.id)
        self.question1 = self.add_question(
            self.application_form.id,
            self.section.id,
            order=1,
            key='review-identifier')
        self.question_translation1 = self.add_question_translation(
            self.question1.id,
            'en',
            'Organisation')
        self.question2 = self.add_question(
            self.application_form.id,
            self.section.id,
            order=2,
            key='review-identifier')
        self.question_translation2 = self.add_question_translation(
            self.question2.id,
            'en',
            'Country')
        self.question3 = self.add_question(
            self.application_form.id,
            self.section.id,
            order=3,
        )
        self.question_translation3 = self.add_question_translation(
            self.question3.id,
            'en',
            'Non-review question'
        )

        self.response1 = self.add_response(
            self.application_form.id,
            self.user1.id,
            is_submitted=True)
        self.answer1 = self.add_answer(self.response1.id, self.question1.id, 'Pets R Us')
        self.answer2 = self.add_answer(self.response1.id, self.question2.id, 'Nigeria')
        self.answer3 = self.add_answer(self.response1.id, self.question3.id, 'Non-review answer')

        self.response2 = self.add_response(
            self.application_form.id,
            self.user2.id,
            is_submitted=True)
        self.answer4 = self.add_answer(self.response2.id, self.question1.id, 'Nokia')
        self.answer5 = self.add_answer(self.response2.id, self.question2.id, 'South Africa')
        self.answer6 = self.add_answer(self.response2.id, self.question3.id, 'Non-review answer 2')

        self.review_form = self.add_review_form(self.application_form.id)
        self.review_section1 = self.add_review_section(self.review_form.id)
        self.review_section1_translation1 = self.add_review_section_translation(
            self.review_section1.id,
            'en')
        self.review_section2 = self.add_review_section(self.review_form.id)
        self.review_section2_translation1 = self.add_review_section_translation(
            self.review_section2.id,
            'en'
            'Review Section 2',
            'Review Section 2 Description')
        self.review_question1 = self.add_review_question(self.review_section1.id, type='short-text', weight=1)
        self.review_question_translation1 = self.add_review_question_translation(
            self.review_question1.id,
            'en',
            headline='Ethical Considerations',
            description="How ethical is the candidate's proposal from 1 to 5?")
        self.review_question2 = self.add_review_question(self.review_section1.id, type='long-text', weight=0)
        self.review_question_translation2 = self.add_review_question_translation(
            self.review_question2.id,
            'en',
            headline=None,
            description='Comments for the candidate'
        )
        self.review_question3 = self.add_review_question(self.review_section2.id, type='multi-choice', weight=2)
        self.review_question_translation3 = self.add_review_question_translation(
            self.review_question3.id,
            'en',
            headline=None,
            description='What is your overall rating?'
        )
        self.review_question4 = self.add_review_question(self.review_section2.id, type='checkbox', weight=0)
        self.review_question_translation4 = self.add_review_question_translation(
            self.review_question4.id,
            'en',
            headline='Yes/No Question'
        )

        # reviewer 1 for first response
        self.review_response1 = self.add_review_response(
            self.reviewer.id,
            self.response1.id,
            self.review_form.id,
            is_submitted=True)
        self.review_score1 = self.add_review_score(self.review_response1.id, self.review_question1.id, '4')
        self.review_score2 = self.add_review_score(self.review_response1.id, self.review_question2.id, 'This is a very good proposal')
        self.review_score3 = self.add_review_score(self.review_response1.id, self.review_question3.id, '5')
        self.review_score4 = self.add_review_score(self.review_response1.id, self.review_question4.id, 'Yes')

        # reviewer 2 for first response
        self.review_response3 = self.add_review_response(
            self.reviewer2.id,
            self.response1.id,
            self.review_form.id,
            is_submitted=True)
        self.review_score9 = self.add_review_score(self.review_response3.id, self.review_question1.id, '3')
        self.review_score10 = self.add_review_score(self.review_response3.id, self.review_question2.id, 'This is a good proposal')
        self.review_score11 = self.add_review_score(self.review_response3.id, self.review_question3.id, '4')
        self.review_score12 = self.add_review_score(self.review_response3.id, self.review_question4.id, 'Yes')

        # reviewer 2 for second response
        self.review_response2 = self.add_review_response(
            self.reviewer2.id,
            self.response2.id,
            self.review_form.id,
            is_submitted=True)
        self.review_score5 = self.add_review_score(self.review_response2.id, self.review_question1.id, '3')
        self.review_score6 = self.add_review_score(self.review_response2.id, self.review_question2.id, 'Close to bad!')
        self.review_score7 = self.add_review_score(self.review_response2.id, self.review_question3.id, '2')
        self.review_score8 = self.add_review_score(self.review_response2.id, self.review_question4.id, 'No')

        # reviewer 1 for second response
        self.review_response4 = self.add_review_response(
            self.reviewer.id,
            self.response2.id,
            self.review_form.id,
            is_submitted=True)
        self.review_score13 = self.add_review_score(self.review_response4.id, self.review_question1.id, '2')
        self.review_score14 = self.add_review_score(self.review_response4.id, self.review_question2.id, 'Bad!')
        self.review_score15 = self.add_review_score(self.review_response4.id, self.review_question3.id, '1')
        self.review_score16 = self.add_review_score(self.review_response4.id, self.review_question4.id, 'No')

    def test_not_authed(self):
        response = self.app.get('/api/v1/reviewresponsesummarylist')
        self.assertEqual(response.status_code, 401)

    def test_not_event_admin(self):
        self.seed_static_data()

        response = self.app.get(
            '/api/v1/reviewresponsesummarylist',
            headers=self.get_auth_header_for('user1@mail.com'),
            data={'event_id': 1}
        )

        self.assertEqual(response.status_code, 403)

    def test_review_response_summary_for_event(self):
        self.seed_static_data()

        response = self.app.get(
            '/api/v1/reviewresponsesummarylist',
            headers=self.get_auth_header_for('event_admin@mail.com'),
            data={'event_id': 1, 'language': 'en'}
        )

        data = json.loads(response.data)

        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['response_id'], 1)
        self.assertEqual(data[0]['response_user_title'], 'Ms')
        self.assertEqual(data[0]['response_user_firstname'], 'Jane')
        self.assertEqual(data[0]['response_user_lastname'], 'Bloggs')

        self.assertEqual(len(data[0]['identifiers']), 2)
        self.assertEqual(data[0]['identifiers'][0]['headline'], 'Organisation')
        self.assertEqual(data[0]['identifiers'][0]['value'], 'Pets R Us')
        self.assertEqual(data[0]['identifiers'][1]['headline'], 'Country')
        self.assertEqual(data[0]['identifiers'][1]['value'], 'Nigeria')

        self.assertEqual(len(data[0]['scores']), 2)
        self.assertEqual(data[0]['scores'][0]['headline'], 'Ethical Considerations')
        self.assertEqual(data[0]['scores'][0]['description'], "How ethical is the candidate's proposal from 1 to 5?")
        self.assertEqual(data[0]['scores'][0]['type'], 'short-text')
        self.assertEqual(data[0]['scores'][0]['score'], 3.5)
        self.assertEqual(data[0]['scores'][0]['weight'], 1)

        self.assertEqual(data[0]['scores'][1]['headline'], None)
        self.assertEqual(data[0]['scores'][1]['description'], 'What is your overall rating?')
        self.assertEqual(data[0]['scores'][1]['type'], 'multi-choice')
        self.assertEqual(data[0]['scores'][1]['score'], 4.5)
        self.assertEqual(data[0]['scores'][1]['weight'], 2)

        self.assertEqual(data[0]['total'], 12.5)


        self.assertEqual(data[1]['response_id'], 2)
        self.assertEqual(data[1]['response_user_title'], 'Dr')
        self.assertEqual(data[1]['response_user_firstname'], 'Alex')
        self.assertEqual(data[1]['response_user_lastname'], 'Person')

        self.assertEqual(len(data[1]['identifiers']), 2)
        self.assertEqual(data[1]['identifiers'][0]['headline'], 'Organisation')
        self.assertEqual(data[1]['identifiers'][0]['value'], 'Nokia')
        self.assertEqual(data[1]['identifiers'][1]['headline'], 'Country')
        self.assertEqual(data[1]['identifiers'][1]['value'], 'South Africa')

        self.assertEqual(len(data[1]['scores']), 2)
        self.assertEqual(data[1]['scores'][0]['headline'], 'Ethical Considerations')
        self.assertEqual(data[1]['scores'][0]['description'], "How ethical is the candidate's proposal from 1 to 5?")
        self.assertEqual(data[1]['scores'][0]['type'], 'short-text')
        self.assertEqual(data[1]['scores'][0]['score'], 2.5)
        self.assertEqual(data[1]['scores'][0]['weight'], 1)

        self.assertEqual(data[1]['scores'][1]['headline'], None)
        self.assertEqual(data[1]['scores'][1]['description'], 'What is your overall rating?')
        self.assertEqual(data[1]['scores'][1]['type'], 'multi-choice')
        self.assertEqual(data[1]['scores'][1]['score'], 1.5)
        self.assertEqual(data[1]['scores'][1]['weight'], 2)

        self.assertEqual(data[1]['total'], 5.5)


class ReviewStageAPITest(ApiTestCase):
    def seed_static_data(self, activate_second_stage=True):
        first_event = self.add_event()
        self.create_application_form()

        event_admin = self.add_user("event@admin.com")
        first_event.add_event_role('admin', event_admin.id)

        self.add_review_form(stage=1, active=False)
        self.add_review_form(stage=2, active=activate_second_stage)
        self.add_review_form(stage=3, active=False)

        # An event with no review form
        no_form_event = self.add_event(key="no_form_event")
        self.no_form_event_id = no_form_event.id
        no_form_event.add_event_role('admin', event_admin.id)

        db.session.commit()
        self.event_admin_headers = self.get_auth_header_for("event@admin.com")

    def test_get(self):
        """Test that the get method returns the correct current stage and number of stages."""
        self.seed_static_data()

        response = self.app.get(
            '/api/v1/reviewstage',
            headers=self.event_admin_headers,
            data={'event_id': 1}
        )

        data = json.loads(response.data)

        self.assertEqual(data['current_stage'], 2)
        self.assertEqual(data['total_stages'], 3)

    def test_get_no_active(self):
        """Test that the get method returns a 404 when ther is no active review form."""
        self.seed_static_data(activate_second_stage=False)

        response = self.app.get(
            '/api/v1/reviewstage',
            headers=self.event_admin_headers,
            data={'event_id': 1}
        )

        self.assertEqual(response.status_code, 404)

    def test_get_no_form(self):
        """Test that the get method returns a 404 when there are no review forms for the event."""
        self.seed_static_data()

        response = self.app.get(
            '/api/v1/reviewstage',
            headers=self.event_admin_headers,
            data={'event_id': self.no_form_event_id}
        )

        self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Test that the review stage can be updated."""
        self.seed_static_data()

        response = self.app.post(
            '/api/v1/reviewstage',
            headers=self.event_admin_headers,
            data={'event_id': 1, 'stage': 3}
        )

        self.assertEqual(response.status_code, 201)

        response = self.app.get(
            '/api/v1/reviewstage',
            headers=self.event_admin_headers,
            data={'event_id': 1}
        )

        data = json.loads(response.data)

        self.assertEqual(data['current_stage'], 3)
        self.assertEqual(data['total_stages'], 3)

    def test_post_no_form(self):
        """Test that the post method returns a 404 when there are no review forms for the event."""
        self.seed_static_data()

        response = self.app.post(
            '/api/v1/reviewstage',
            headers=self.event_admin_headers,
            data={'event_id': self.no_form_event_id, 'stage': 1}
        )

        self.assertEqual(response.status_code, 404)

    def test_post_no_form(self):
        """Test that the post method returns a 404 when trying to activate a stage that doesn't exist."""
        self.seed_static_data()

        response = self.app.post(
            '/api/v1/reviewstage',
            headers=self.event_admin_headers,
            data={'event_id': 1, 'stage': 4}
        )

        self.assertEqual(response.status_code, 404)
    

REVIEW_FORM_POST = {
  "event_id": 1,
  "application_form_id": 1,  
  "stage": 2,
  "is_open": True,   
  "deadline": datetime(2024, 6, 1).strftime('%Y-%m-%dT%H:%M:%S'),  
  "active": True,     
  "sections": [
      {
          "order": 1,
          "name": {
             "en": "Section 1",
             "fr": "Section 1"
          },
          "description": {
             "en": "This is the first section",
             "fr": "Ceci est la première section"
          },
          "questions": [
              {
                 "type": "short-text",
                 "is_required": False,
                 "order": 1,
                 "weight": 0.0,
                 "question_id": 0,
                 "headline": {
                     "en": "Question 1",
                     "fr": "Question 1"
                 },
                 "description": {
                     "en": "This is the first question",
                     "fr": "C'est la première question"
                 },
                 "placeholder": {
                     "en": "Enter something interesting",
                     "fr": "Entrez quelque chose d'intéressant"
                 },
                 "options": {
                     "en": None,
                     "fr": None
                 },
                 "validation_regex": {
                     "en": "(a|b|c|d)",
                     "fr": "(a|b|c|d)"
                 },
                 "validation_text": {
                     "en": "You must enter a, b, c or d",
                     "fr": "Vous devez entrer a, b, c ou d"
                 }
              },   
              {
                 "type": "radio",
                 "is_required": True,
                 "order": 2,
                 "weight": 1.5,
                 "question_id": 0,
                 "headline": {
                     "en": "Question 2",
                     "fr": "Question 2"
                 },
                 "description": {
                     "en": "This is the second question",
                     "fr": "C'est la deuxième question"
                 },
                 "placeholder": {
                     "en": None,
                     "fr": None
                 },
                 "options": {
                     "en": [
                          {"value": "0", "label": "Bad"}, 
                          {"value": "1", "label": "Average"}, 
                          {"value": "2", "label": "Good"}, 
                      ],
                     "fr": [
                          {"value": "0", "label": "Mal"}, 
                          {"value": "1", "label": "Moyenne"}, 
                          {"value": "2", "label": "Bien"}, 
                      ],
                 },
                 "validation_regex": {
                     "en": None,
                     "fr": None
                 },
                 "validation_text": {
                     "en": None,
                     "fr": None
                 }
              } 
          ]
      },  
      {
          "order": 2,
          "name": {
             "en": "Section 2",
             "fr": "Section 2"
          },
          "description": {
             "en": "This is the first section",
             "fr": "Ceci est la deuxième section"
          },
          "questions": [
              {
                 "type": "information",
                 "is_required": False,
                 "order": 1,
                 "weight": 0.0,
                 "question_id": 1,    
                 "headline": {
                     "en": "Question 1 from application form",
                     "fr": "Question 1 from application form"
                 },
                 "description": {
                     "en": "This is the first question from the application form",
                     "fr": "C'est la première question du formulaire de candidature"
                 },
                 "placeholder": {
                     "en": None,
                     "fr": None
                 },
                 "options": {
                     "en": None,
                     "fr": None
                 },
                 "validation_regex": {
                     "en": None,
                     "fr": None
                 },
                 "validation_text": {
                     "en": None,
                     "fr": None
                 }
              }
          ]
      } 
  ]
}


REVIEW_FORM_PUT = {
  "id": 1,
  "event_id": 1,
  "application_form_id": 1,  
  "stage": 3,  # Updated
  "is_open": True,   
  "deadline": datetime(2023, 2, 2).strftime('%Y-%m-%dT%H:%M:%S'),  # Updated
  "active": True,     
  "sections": [
      {  # Updated first section
          "id": 1,  
          "order": 2,  # Updated
          "name": { 
             "en": "Section 1 Updated",
             "fr": "Section 1 Updated"
          },
          "description": {
             "en": "This is the first section updated",
             "fr": "Ceci est la première section updated"
          },
          "questions": [
              {
                 "id": 1,  # Updated
                 "type": "long-text",  # Updated
                 "is_required": True,
                 "order": 10,
                 "weight": 1.0,
                 "question_id": 0,
                 "headline": {
                     "en": "Question 1 Updated",
                     "fr": "Question 1 Updated"
                 },
                 "description": {
                     "en": "This is the first question Updated",
                     "fr": "C'est la première question Updated"
                 },
                 "placeholder": {
                     "en": "Enter something interesting updated",
                     "fr": "Entrez quelque chose d'intéressant updated"
                 },
                 "options": {
                     "en": {"blah": "blah"},
                     "fr": {"blah": "blah"}
                 },
                 "validation_regex": {
                     "en": "(a|b|c|d|e)",
                     "fr": "(a|b|c|d|e)"
                 },
                 "validation_text": {
                     "en": "You must enter a, b, c or d, or e",
                     "fr": "Vous devez entrer a, b, c, d, ou e"
                 }
              },   
              # Deleted question 2
              {  # New question
                 "type": "radio",
                 "is_required": True,
                 "order": 20,
                 "weight": 2.5,
                 "question_id": 0,
                 "headline": {
                     "en": "Question 3",
                     "fr": "Question 3"
                 },
                 "description": {
                     "en": "This is the third question",
                     "fr": "C'est la deuxième question"
                 },
                 "placeholder": {
                     "en": "hello",
                     "fr": "world"
                 },
                 "options": {
                     "en": [
                          {"value": "0", "label": "Bad"}, 
                          {"value": "1", "label": "Average"}, 
                          {"value": "2", "label": "Good"}, 
                      ],
                     "fr": [
                          {"value": "0", "label": "Mal"}, 
                          {"value": "1", "label": "Moyenne"}, 
                          {"value": "2", "label": "Bien"}, 
                      ],
                 },
                 "validation_regex": {
                     "en": None,
                     "fr": None
                 },
                 "validation_text": {
                     "en": None,
                     "fr": None
                 }
              } 
          ]
      },  
      # Deleted section 2
      {  # New section
          "order": 3,
          "name": {
             "en": "Section 2 New",
             "fr": "Section 2 New"
          },
          "description": {
             "en": "This is the new second section",
             "fr": "Ceci est la neue deuxième section"
          },
          "questions": [
              {
                 "type": "information",
                 "is_required": False,
                 "order": 1,
                 "weight": 0.0,
                 "question_id": 1,    
                 "headline": {
                     "en": "Question 1 from application form",
                     "fr": "Question 1 from application form"
                 },
                 "description": {
                     "en": "This is the first question from the application form",
                     "fr": "C'est la première question du formulaire de candidature"
                 },
                 "placeholder": {
                     "en": None,
                     "fr": None
                 },
                 "options": {
                     "en": None,
                     "fr": None
                 },
                 "validation_regex": {
                     "en": None,
                     "fr": None
                 },
                 "validation_text": {
                     "en": None,
                     "fr": None
                 }
              }
          ]
      } 
  ]
}

class ReviewFormDetailAPITest(ApiTestCase):

    def seed_static_data(self):
        first_event = self.add_event()
        self.first_event_id = first_event.id

        second_event = self.add_event(key="event2")
        self.no_form_event_id = second_event.id

        app_form = self.create_application_form()
        section = self.add_section(app_form.id)
        self.question = self.add_question(app_form.id, section.id)

        event_admin = self.add_user("event@admin.com")
        first_event.add_event_role('admin', event_admin.id)
        second_event.add_event_role('admin', event_admin.id)
        db.session.commit()

    def add_review_forms(self):
        # First stage review form
        form1 = self.add_review_form(stage=1, active=False, deadline=datetime(2021, 6, 1))
        form1_section1 = self.add_review_section(form1.id)
        self.add_review_section_translation(form1_section1.id, 'en', 'Form 1 Section 1 EN', 'Form 1 Section 1 Description EN')
        self.add_review_section_translation(form1_section1.id, 'fr', 'Form 1 Section 1 FR', 'Form 1 Section 1 Description FR')

        form1_section1_question1 = self.add_review_question(form1_section1.id, weight=1, type='numeric-text')
        self.add_review_question_translation(
            form1_section1_question1.id,
            language='en',
            headline='Review Question 1 EN',
            description='Review Question 1 Description EN',
            placeholder='Placeholder Question 1 EN',
            validation_regex='(a|b|c|d)',
            validation_text='Validation text question 1 EN')
        self.add_review_question_translation(
            form1_section1_question1.id,
            language='fr',
            headline='Review Question 1 FR',
            description='Review Question 1 Description FR',
            placeholder='Placeholder Question 1 FR',
            validation_regex='(a|b|c|d)',
            validation_text='Validation text question 1 FR')

        form1_section1_question2 = self.add_review_question(form1_section1.id, type='information', order=2, question_id=self.question.id)
        self.add_review_question_translation(
            form1_section1_question2.id,
            language='en',
            headline='Review Question 2 EN',
            description='Review Question 2 Description EN')
        self.add_review_question_translation(
            form1_section1_question2.id,
            language='fr',
            headline='Review Question 2 FR',
            description='Review Question 2 Description FR')

        form1_section2 = self.add_review_section(form1.id, order=2)
        self.add_review_section_translation(form1_section2.id, 'en', 'Form 1 Section 2 EN', 'Form 1 Section 2 Description EN')
        self.add_review_section_translation(form1_section2.id, 'fr', 'Form 1 Section 2 FR', 'Form 1 Section 2 Description FR')

        form1_section2_question1 = self.add_review_question(form1_section2.id, weight=1, type='radio')
        self.add_review_question_translation(
            form1_section2_question1.id,
            language='en',
            headline='Review Question 3 EN',
            description='Review Question 3 Description EN',
            options=[
                {'value': '0', 'label': 'Bad EN'},
                {'value': '1', 'label': 'Average EN'},
                {'value': '2', 'label': 'Good EN'}
            ])
        self.add_review_question_translation(
            form1_section2_question1.id,
            language='fr',
            headline='Review Question 3 FR',
            description='Review Question 3 Description FR',
            options=[
                {'value': '0', 'label': 'Bad FR'},
                {'value': '1', 'label': 'Average FR'},
                {'value': '2', 'label': 'Good FR'}
            ])

        # Second stage review form
        form2 = self.add_review_form(stage=2, active=True, deadline=datetime(2021, 8, 1))

        form2_section1 = self.add_review_section(form2.id)
        self.add_review_section_translation(form2_section1.id, 'en', 'Form 2 Section 1 EN', 'Form 2 Section 1 Description EN')
        self.add_review_section_translation(form2_section1.id, 'fr', 'Form 2 Section 1 FR', 'Form 2 Section 1 Description FR')

        form2_section1_question1 = self.add_review_question(form2_section1.id, type='information', question_id=self.question.id)
        self.add_review_question_translation(
            form2_section1_question1.id,
            language='en',
            headline='Stage 2 Review Question 1 EN',
            description='Stage 2 Review Question 1 Description EN')
        self.add_review_question_translation(
            form2_section1_question1.id,
            language='fr',
            headline='Stage 2 Review Question 1 FR',
            description='Stage 2 Review Question 1 Description FR')

        db.session.commit()
        
    def test_get_without_stage(self):
        """Test that the get method returns the correct stage when a stage parameter isn't provided."""
        self.seed_static_data()
        self.add_review_forms()

        response = self.app.get(
            '/api/v1/review-form-detail',
            headers=self.get_auth_header_for("event@admin.com"),
            data={'event_id': self.first_event_id}
        )

        data = json.loads(response.data)

        self.assertEqual(data['stage'], 2)

    def test_get_first_stage(self):
        """Check that the get method returns the form for stage 1."""
        self.seed_static_data()
        self.add_review_forms()

        response = self.app.get(
            '/api/v1/review-form-detail',
            headers=self.get_auth_header_for("event@admin.com"),
            data={'event_id': self.first_event_id, 'stage': 1}
        )

        data = json.loads(response.data)

        self.assertEqual(data['id'], 1)
        self.assertEqual(data['event_id'], self.first_event_id)
        self.assertEqual(data['application_form_id'], 1)
        self.assertEqual(data['is_open'], True)
        self.assertEqual(data['deadline'], "2021-06-01T00:00:00")
        self.assertEqual(data['active'], False)
        self.assertEqual(data['stage'], 1)
        self.assertEqual(len(data['sections']), 2)

        section1 = data['sections'][0]
        self.assertEqual(section1['order'], 1)
        self.assertEqual(section1['name']['en'], 'Form 1 Section 1 EN')
        self.assertEqual(section1['name']['fr'], 'Form 1 Section 1 FR')
        self.assertEqual(section1['description']['en'], 'Form 1 Section 1 Description EN')
        self.assertEqual(section1['description']['fr'], 'Form 1 Section 1 Description FR')
        self.assertEqual(len(section1['questions']), 2)

        question1 = section1['questions'][0]
        self.assertEqual(question1['order'], 1)
        self.assertEqual(question1['weight'], 1)
        self.assertEqual(question1['type'], 'numeric-text')
        self.assertEqual(question1['question_id'], 0)
        self.assertEqual(question1['headline']['en'], 'Review Question 1 EN')
        self.assertEqual(question1['headline']['fr'], 'Review Question 1 FR')
        self.assertEqual(question1['description']['en'], 'Review Question 1 Description EN')
        self.assertEqual(question1['description']['fr'], 'Review Question 1 Description FR')
        self.assertEqual(question1['placeholder']['en'], 'Placeholder Question 1 EN')
        self.assertEqual(question1['placeholder']['fr'], 'Placeholder Question 1 FR')
        self.assertEqual(question1['validation_regex']['en'], '(a|b|c|d)')
        self.assertEqual(question1['validation_regex']['fr'], '(a|b|c|d)')
        self.assertEqual(question1['validation_text']['en'], 'Validation text question 1 EN')
        self.assertEqual(question1['validation_text']['fr'], 'Validation text question 1 FR')
        self.assertEqual(question1['options']['en'], None)
        self.assertEqual(question1['options']['fr'], None)

        question2 = section1['questions'][1]
        self.assertEqual(question2['order'], 2)
        self.assertEqual(question2['weight'], 0)
        self.assertEqual(question2['type'], 'information')
        self.assertEqual(question2['question_id'], 1)
        self.assertEqual(question2['headline']['en'], 'Review Question 2 EN')
        self.assertEqual(question2['headline']['fr'], 'Review Question 2 FR')
        self.assertEqual(question2['description']['en'], 'Review Question 2 Description EN')
        self.assertEqual(question2['description']['fr'], 'Review Question 2 Description FR')
        self.assertEqual(question2['placeholder']['en'], None)
        self.assertEqual(question2['placeholder']['fr'], None)
        self.assertEqual(question2['validation_regex']['en'], None)
        self.assertEqual(question2['validation_regex']['fr'], None)
        self.assertEqual(question2['validation_text']['en'], None)
        self.assertEqual(question2['validation_text']['fr'], None)
        self.assertEqual(question2['options']['en'], None)
        self.assertEqual(question2['options']['fr'], None)

        section2 = data['sections'][1]
        self.assertEqual(section2['order'], 2)
        self.assertEqual(section2['name']['en'], 'Form 1 Section 2 EN')
        self.assertEqual(section2['name']['fr'], 'Form 1 Section 2 FR')
        self.assertEqual(section2['description']['en'], 'Form 1 Section 2 Description EN')
        self.assertEqual(section2['description']['fr'], 'Form 1 Section 2 Description FR')
        self.assertEqual(len(section2['questions']), 1)

        question3 = section2['questions'][0]
        self.assertEqual(question3['order'], 1)
        self.assertEqual(question3['weight'], 1)
        self.assertEqual(question3['type'], 'radio')
        self.assertEqual(question3['question_id'], 0)
        self.assertEqual(question3['headline']['en'], 'Review Question 3 EN')
        self.assertEqual(question3['headline']['fr'], 'Review Question 3 FR')
        self.assertEqual(question3['description']['en'], 'Review Question 3 Description EN')
        self.assertEqual(question3['description']['fr'], 'Review Question 3 Description FR')
        self.assertEqual(question3['placeholder']['en'], None)
        self.assertEqual(question3['placeholder']['fr'], None)
        self.assertEqual(question3['validation_regex']['en'], None)
        self.assertEqual(question3['validation_regex']['fr'], None)
        self.assertEqual(question3['validation_text']['en'], None)
        self.assertEqual(question3['validation_text']['fr'], None)
        self.assertEqual(len(question3['options']['en']), 3)
        self.assertEqual(len(question3['options']['fr']), 3)

    def test_get_second_stage(self):
        """Check that the get method returns the form for stage 2."""
        self.seed_static_data()
        self.add_review_forms()

        response = self.app.get(
            '/api/v1/review-form-detail',
            headers=self.get_auth_header_for("event@admin.com"),
            data={'event_id': self.first_event_id, 'stage': 2}
        )

        data = json.loads(response.data)

        self.assertEqual(data['id'], 2)
        self.assertEqual(data['event_id'], self.first_event_id)
        self.assertEqual(data['application_form_id'], 1)
        self.assertEqual(data['is_open'], True)
        self.assertEqual(data['deadline'], "2021-08-01T00:00:00")
        self.assertEqual(data['active'], True)
        self.assertEqual(data['stage'], 2)
        self.assertEqual(len(data['sections']), 1)

        section1 = data['sections'][0]
        self.assertEqual(section1['order'], 1)
        self.assertEqual(section1['name']['en'], 'Form 2 Section 1 EN')
        self.assertEqual(section1['name']['fr'], 'Form 2 Section 1 FR')
        self.assertEqual(section1['description']['en'], 'Form 2 Section 1 Description EN')
        self.assertEqual(section1['description']['fr'], 'Form 2 Section 1 Description FR')
        self.assertEqual(len(section1['questions']), 1)

        question1 = section1['questions'][0]
        self.assertEqual(question1['order'], 1)
        self.assertEqual(question1['weight'], 0)
        self.assertEqual(question1['type'], 'information')
        self.assertEqual(question1['question_id'], 1)
        self.assertEqual(question1['headline']['en'], 'Stage 2 Review Question 1 EN')
        self.assertEqual(question1['headline']['fr'], 'Stage 2 Review Question 1 FR')
        self.assertEqual(question1['description']['en'], 'Stage 2 Review Question 1 Description EN')
        self.assertEqual(question1['description']['fr'], 'Stage 2 Review Question 1 Description FR')
        self.assertEqual(question1['placeholder']['en'], None)
        self.assertEqual(question1['placeholder']['fr'], None)
        self.assertEqual(question1['validation_regex']['en'], None)
        self.assertEqual(question1['validation_regex']['fr'], None)
        self.assertEqual(question1['validation_text']['en'], None)
        self.assertEqual(question1['validation_text']['fr'], None)
        self.assertEqual(question1['options']['en'], None)
        self.assertEqual(question1['options']['fr'], None)

    def test_get_new_stage(self):
        """Check that the get method returns not found for a stage that doesn't exist."""
        self.seed_static_data()
        self.add_review_forms()

        response = self.app.get(
            '/api/v1/review-form-detail',
            headers=self.get_auth_header_for("event@admin.com"),
            data={'event_id': self.first_event_id, 'stage': 3}
        )

        self.assertEqual(response.status_code, 404)

    def test_get_no_form(self):
        """Check that the get method returns not found for an event that has no review form."""
        self.seed_static_data()
        self.add_review_forms()

        response = self.app.get(
            '/api/v1/review-form-detail',
            headers=self.get_auth_header_for("event@admin.com"),
            data={'event_id': self.no_form_event_id, 'stage': 1}
        )

        self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Check that the post method works."""
        self.seed_static_data()

        response = self.app.post(
            '/api/v1/review-form-detail',
            headers=self.get_auth_header_for("event@admin.com"),
            data=json.dumps(REVIEW_FORM_POST),
            content_type='application/json',)

        self.assertEqual(response.status_code, 201)

        response = self.app.get(
            '/api/v1/review-form-detail',
            headers=self.get_auth_header_for("event@admin.com"),
            data={'event_id': REVIEW_FORM_POST["event_id"], 'stage': REVIEW_FORM_POST["stage"]}
        )

        data = json.loads(response.data)

        self.assertTrue("id" in data and data["id"] is not None)
        del data["id"]

        self.assertTrue("id" in data["sections"][0] and data["sections"][0]["id"] is not None)
        del data["sections"][0]["id"]

        self.assertTrue("id" in data["sections"][1] and data["sections"][1]["id"] is not None)
        del data["sections"][1]["id"]

        self.assertTrue("id" in data["sections"][0]["questions"][0] and data["sections"][0]["questions"][0]["id"] is not None)
        del data["sections"][0]["questions"][0]["id"]

        self.assertTrue("id" in data["sections"][0]["questions"][1] and data["sections"][0]["questions"][1]["id"] is not None)
        del data["sections"][0]["questions"][1]["id"]

        self.assertTrue("id" in data["sections"][1]["questions"][0] and data["sections"][1]["questions"][0]["id"] is not None)
        del data["sections"][1]["questions"][0]["id"]
        
        self.maxDiff = 6000
        self.assertEqual(data, REVIEW_FORM_POST)

    def test_put(self):
        self.seed_static_data()

        # First create the review form
        response = self.app.post(
            '/api/v1/review-form-detail',
            headers=self.get_auth_header_for("event@admin.com"),
            data=json.dumps(REVIEW_FORM_POST),
            content_type='application/json',)

        self.assertEqual(response.status_code, 201)

        # Now update it 
        response = self.app.put(
            '/api/v1/review-form-detail',
            headers=self.get_auth_header_for("event@admin.com"),
            data=json.dumps(REVIEW_FORM_PUT),
            content_type='application/json'   
        )

        data = json.loads(response.data)

        del data["sections"][1]["id"]
        del data["sections"][0]["questions"][1]["id"]
        del data["sections"][1]["questions"][0]["id"]
        self.maxDiff = None
        self.assertEqual(data, REVIEW_FORM_PUT)
