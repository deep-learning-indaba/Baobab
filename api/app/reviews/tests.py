from datetime import datetime
import json
import copy

from app import db, LOGGER
from app.utils.testing import ApiTestCase
from app.events.models import Event, EventRole
from app.users.models import AppUser, UserCategory, Country
from app.applicationModel.models import ApplicationForm, Question, Section
from app.responses.models import Response, Answer, ResponseReviewer
from app.references.models import ReferenceRequest, Reference
from app.references.repository import ReferenceRequestRepository as reference_request_repository
from app.reviews.models import ReviewForm, ReviewQuestion, ReviewResponse, ReviewScore, ReviewConfiguration
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
            self.add_event('indaba 2019', 'The Deep Learning Indaba 2019, Kenyatta University, Nairobi, Kenya ', datetime(2019, 8, 25), datetime(2019, 8, 31),
            'KENYADABA2019'),
            self.add_event('indaba 2020', 'The Deep Learning Indaba 2018, Stellenbosch University, South Africa', datetime(2018, 9, 9), datetime(2018, 9, 15),
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
            Section(1, 'Tell Us a Bit About You', '', 1),
            Section(2, 'Tell Us a Bit About You', '', 1)
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
            Question(1, 1, 'Why is attending the Deep Learning Indaba 2019 important to you?', 'Enter 50 to 150 words', 1, 'long_text', ''),
            Question(1, 1, 'How will you share what you have learnt after the Indaba?', 'Enter 50 to 150 words', 2, 'long_text', ''),
            Question(2, 2, 'Have you worked on a project that uses machine learning?', 'Enter 50 to 150 words', 1, 'long_text', ''),
            Question(2, 2, 'Would you like to be considered for a travel award?', 'Enter 50 to 150 words', 2, 'long_text', ''),
            Question(1, 1, 'Did you attend the 2017 or 2018 Indaba', 'Select an option...', 3, 'multi-choice', None, None, True, None, options)
        ]
        db.session.add_all(questions)
        db.session.commit()

        closed_review = ReviewForm(2, datetime(2018, 4, 30))
        closed_review.close()
        review_forms = [
            ReviewForm(1, datetime(2019, 4, 30)),
            closed_review
        ]
        db.session.add_all(review_forms)
        db.session.commit()

        review_configs = [
            ReviewConfiguration(review_form_id=review_forms[0].id, num_reviews_required=3, num_optional_reviews=0),
            ReviewConfiguration(review_form_id=review_forms[1].id, num_reviews_required=3, num_optional_reviews=0)
        ]
        db.session.add_all(review_configs)
        db.session.commit()

        review_questions = [
            ReviewQuestion(1, 1, None, None, 'multi-choice', None, None, True, 1, None, None, 0),
            ReviewQuestion(1, 2, None, None, 'multi-choice', None, None, True, 2, None, None, 0),
            ReviewQuestion(2, 3, None, None, 'multi-choice', None, None, True, 1, None, None, 0),
            ReviewQuestion(2, 4, None, None, 'information', None, None, False, 2, None, None, 0)
        ]
        db.session.add_all(review_questions)
        db.session.commit()

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
        response = Response(1, 5)
        response.submit()
        responses = [
            response
        ]
        db.session.add_all(responses)
        db.session.commit()

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
        params = {'event_id': 1}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 1)

    def test_one_reviewer_one_candidate_inactive(self):
        self.seed_static_data()
        self.setup_one_reviewer_one_candidate(active=False)
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1}

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
        response = Response(1, 5)
        response.submit()
        responses = [
            response
        ]
        db.session.add_all(responses)
        db.session.commit()

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
        params = {'event_id': 1}

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
        responses = [
            Response(application_form_id=1, user_id=5),
            Response(application_form_id=1, user_id=6),
            Response(application_form_id=1, user_id=7)
        ]
        for response in responses:
            response.submit()
        db.session.add_all(responses)
        db.session.commit()

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
        params = {'event_id': 1}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 2)

    def setup_one_reviewer_three_candidates_and_one_completed_review(self):
        responses = [
            Response(1, 5),
            Response(1, 6),
            Response(1, 7)
        ]
        for response in responses:
            response.submit()
        db.session.add_all(responses)
        db.session.commit()

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

        review_response = ReviewResponse(1, 1, 1)
        db.session.add(review_response)
        db.session.commit()

    def test_one_reviewer_three_candidates_and_one_completed_review(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates_and_one_completed_review()
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 2)

    def setup_one_reviewer_three_candidates_with_one_withdrawn_response_and_one_unsubmitted_response(self):
        withdrawn_response = Response(1, 5)
        withdrawn_response.withdraw()
        submitted_response = Response(1, 7)
        submitted_response.submit()
        responses = [
            withdrawn_response,
            Response(1, 6),
            submitted_response
        ]
        db.session.add_all(responses)
        db.session.commit()

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
        params = {'event_id': 1}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 1)

    def setup_multiple_reviewers_with_different_subsets_of_candidates_and_reviews_completed(self):
        responses = [
            Response(1, 5),
            Response(1, 6),
            Response(1, 7),
            Response(1, 8)
        ]
        for response in responses:
            response.submit()
        db.session.add_all(responses)
        db.session.commit()

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
            ReviewResponse(1, 2, 2),
            ReviewResponse(1, 3, 1),
            ReviewResponse(1, 3, 2),
            ReviewResponse(1, 4, 1)
        ]
        db.session.add_all(review_responses)
        db.session.commit()
    
    def test_multiple_reviewers_with_different_subsets_of_candidates_and_reviews_completed(self):
        self.seed_static_data()
        self.setup_multiple_reviewers_with_different_subsets_of_candidates_and_reviews_completed()
        params = {'event_id': 1}

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
        params = {'event_id': 1, 'skip': 1}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['response']['user_id'], 7)
        self.assertEqual(data['response']['answers'][0]['value'], 'I want to solve new problems.')

    def test_high_skip_defaults_to_last_review(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates()
        params = {'event_id': 1, 'skip': 5}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['response']['user_id'], 7)
        self.assertEqual(data['response']['answers'][1]['value'], 'I will share by tutoring.')

    def setup_candidate_who_has_applied_to_multiple_events(self):
        user_id = 5
        responses = [
            Response(application_form_id=1, user_id=user_id),
            Response(application_form_id=2, user_id=user_id)
        ]
        for response in responses:
            response.submit()
        db.session.add_all(responses)
        db.session.commit()

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
        params = {'event_id': 2}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 1)
        self.assertEqual(data['response']['user_id'], 5)
        self.assertEqual(data['response']['answers'][0]['value'], 'Yes I worked on a vision task.')

    def setup_multi_choice_answer(self):
        response = Response(1, 5)
        response.submit()
        db.session.add(response)
        db.session.commit()

        answer = Answer(1, 5, 'indaba-2017')
        db.session.add(answer)
        db.session.commit()

        response_reviewer = ResponseReviewer(1, 1)
        db.session.add(response_reviewer)
        db.session.commit()
    
    def test_multi_choice_answers_use_label_instead_of_value(self):
        self.seed_static_data()
        self.setup_multi_choice_answer()
        params = {'event_id': 1}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['response']['answers'][0]['value'], 'Yes, I attended the 2017 Indaba')

    def test_review_response_not_found(self):
        self.seed_static_data()
        params = {'id': 55}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/reviewresponse', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, REVIEW_RESPONSE_NOT_FOUND[1])

    def setup_review_response(self):
        response = Response(1, 5)
        response.submit()
        db.session.add(response)
        db.session.commit()

        answer = Answer(1, 1, 'To learn alot')
        db.session.add(answer)
        db.session.commit()

        self.review_response = ReviewResponse(1, 1, 1)
        self.review_response.review_scores.append(ReviewScore(1, 'answer1'))
        self.review_response.review_scores.append(ReviewScore(2, 'answer2'))
        db.session.add(self.review_response)
        db.session.commit()

        db.session.flush()
        

    def test_review_response(self):
        self.seed_static_data()
        self.setup_review_response()
        params = {'id': self.review_response.id}
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
        params = json.dumps({'review_form_id': 1, 'response_id': 1, 'scores': [{'review_question_id': 1, 'value': 'test_answer'}]})
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.post('/api/v1/reviewresponse', headers=header, data=params, content_type='application/json')

        self.assertEqual(response.status_code, FORBIDDEN[1])

    def test_can_still_submit_inactive_response_reviewer(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates()
        params = json.dumps({'review_form_id': 1, 'response_id': 2, 'scores': [{'review_question_id': 1, 'value': 'test_answer'}]})
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.post('/api/v1/reviewresponse', headers=header, data=params, content_type='application/json')

        self.assertEqual(response.status_code, 201)

    def setup_response_reviewer(self):
        response = Response(1, 5)
        response.submit()
        db.session.add(response)
        db.session.commit()

        response_reviewer = ResponseReviewer(1, 1)
        db.session.add(response_reviewer)
        db.session.commit()

    def test_saving_review_response(self):
        self.seed_static_data()
        self.setup_response_reviewer()
        params = json.dumps({'review_form_id': 1, 'response_id': 1, 'scores': [{'review_question_id': 1, 'value': 'test_answer'}]})
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.post('/api/v1/reviewresponse', headers=header, data=params, content_type='application/json')

        review_scores = db.session.query(ReviewScore).filter_by(review_response_id=1).all()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(review_scores), 1)
        self.assertEqual(review_scores[0].value, 'test_answer')

    def setup_existing_review_response(self):
        response = Response(1, 5)
        response.submit()
        db.session.add(response)
        db.session.commit()

        response_reviewer = ResponseReviewer(1, 1)
        db.session.add(response_reviewer)
        db.session.commit()

        review_response = ReviewResponse(1, 1, 1)
        review_response.review_scores = [ReviewScore(1, 'test_answer1'), ReviewScore(2, 'test_answer2')]
        db.session.add(review_response)
        db.session.commit()

    def test_updating_review_response(self):
        self.seed_static_data()
        self.setup_existing_review_response()
        params = json.dumps({'review_form_id': 1, 'response_id': 1, 'scores': [{'review_question_id': 1, 'value': 'test_answer3'}, {'review_question_id': 2, 'value': 'test_answer4'}]})
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.put('/api/v1/reviewresponse', headers=header, data=params, content_type='application/json')

        review_scores = db.session.query(ReviewScore).filter_by(review_response_id=1).order_by(ReviewScore.review_question_id).all()
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
        responses = [
            Response(1, 5),
            Response(1, 6),
            Response(1, 7),
            Response(1, 8)
        ]
        for response in responses:
            response.submit()
        db.session.add_all(responses)
        db.session.commit()

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
        responses = [
            Response(1, 3), # reviewer
            Response(1, 5) # someone else
        ]
        for response in responses:
            response.submit()
        db.session.add_all(responses)
        db.session.commit()

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
        unsubmitted_response = Response(1, 5)
        withdrawn_response = Response(1, 6)
        withdrawn_response.withdraw()
        submitted_response = Response(1, 7)
        submitted_response.submit()
        responses = [
            unsubmitted_response,
            withdrawn_response,
            submitted_response
        ]
        db.session.add_all(responses)
        db.session.commit()

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
        response = Response(1, 5)
        response.submit()
        db.session.add(response)
        db.session.commit()

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
        response = Response(1, 5)
        response.submit()
        db.session.add(response)
        db.session.commit()

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
        response = Response(1,5)
        response.submit()
        db.session.add(response)
        db.session.commit()

    def setup_count_reviews_allocated_and_completed(self):
        db.session.add_all([ 
            EventRole('reviewer', 1, 1),
            EventRole('reviewer', 2, 1),
            EventRole('reviewer', 3, 1),
            EventRole('reviewer', 4, 1)
        ])
        
        responses = [
            Response(1, 5), #1
            Response(1, 6), #2
            Response(1, 7), #3
            Response(1, 8), #4
            Response(2, 5), #5
            Response(2, 6)  #6
        ]
        for response in responses:
            response.submit()
        db.session.add_all(responses)

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
            ReviewResponse(1, 3, 2), 
            ReviewResponse(1, 3, 4),
            ReviewResponse(1, 2, 1),
            ReviewResponse(1, 2, 3),
            ReviewResponse(1, 2, 4),
            ReviewResponse(2, 1, 5),
            ReviewResponse(2, 2, 6)
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
        responses = [
            Response(application_form_id=1, user_id=users_id[0]),
            Response(application_form_id=1, user_id=users_id[1]),
            Response(application_form_id=1, user_id=users_id[2])
        ]
        for response in responses:
            response.submit()
        db.session.add_all(responses)
        db.session.commit()

        final_verdict_options = [
            {'label': 'Yes', 'value': 2},
            {'label': 'No', 'value': 0},
            {'label': 'Maybe', 'value': 1},
        ]
        verdict_question = ReviewQuestion(1, None, None, 'Final Verdict', 'multi-choice', None, final_verdict_options, True, 3, None, None, 0)
        db.session.add(verdict_question)
        db.session.commit()

        review_responses = [
            ReviewResponse(1,3,1), 
            ReviewResponse(1,3,2),
            ReviewResponse(1,2,1), 
            ReviewResponse(1,2,2),
            ReviewResponse(1,3,3)
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

        verdict_question = ReviewQuestion(1, None, None, 'Final Verdict', 'multi-choice', None, final_verdict_options, True, 3, None, None, 0)
        db.session.add(verdict_question)
        db.session.commit()

        responses = [
            Response(1, 5),
            Response(1, 6),
            Response(1, 7)
        ]
        for response in responses:
            response.submit()
        db.session.add_all(responses)
        db.session.commit()

        review_response_1 = ReviewResponse(1,3,1)
        review_response_2 = ReviewResponse(1,3,2)
        review_response_3 = ReviewResponse(1,3,3)
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

        responses = [
            Response(1, 8),
            Response(1, 1)
        ]
        for response in responses:
            response.submit()
        db.session.add_all(responses)
        db.session.commit()

        review_responses = [
            ReviewResponse(1,3,4),
            ReviewResponse(1,3,5)
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
    

class ReferenceReviewRequest(ApiTestCase):
    def static_seed_data(self):
        # User, country and organisation is set up by ApiTestCase
        self.first_user = self.add_user('firstuser@mail.com', 'First', 'User', 'Mx')

        reviewer1 = AppUser('r1@r.com', 'reviewer', '1', 'Mr', password='abc', organisation_id=1, )
        reviewer2 = AppUser('r2@r.com', 'reviewer', '2', 'Ms', password='abc', organisation_id=1, )
        reviewer3 = AppUser('r3@r.com', 'reviewer', '3', 'Mr', password='abc', organisation_id=1, )
        reviewer4 = AppUser('r4@r.com', 'reviewer', '4', 'Ms', password='abc', organisation_id=1, )
        candidate1 = AppUser('c1@c.com', 'candidate', '1', 'Mr', password='abc', organisation_id=1, )
        candidate2 = AppUser('c2@c.com', 'candidate', '2', 'Ms', password='abc', organisation_id=1, )
        candidate3 = AppUser('c3@c.com', 'candidate', '3', 'Mr', password='abc', organisation_id=1, )
        candidate4 = AppUser('c4@c.com', 'candidate', '4', 'Ms', password='abc', organisation_id=1, )
        system_admin = AppUser('sa@sa.com', 'system_admin', '1', 'Ms', password='abc', organisation_id=1, is_admin=True)
        event_admin = AppUser('ea@ea.com', 'event_admin', '1', 'Ms', password='abc', organisation_id=1)
        users = [reviewer1, reviewer2, reviewer3, reviewer4, candidate1, candidate2, candidate3, candidate4, system_admin,
                 event_admin]
        for user in users:
            user.verify()
        db.session.add_all(users)
        db.session.commit()

        event_roles = [
            EventRole('admin', 10, 1),
            EventRole('reviewer', 3, 1)
        ]
        db.session.add_all(event_roles)
        db.session.commit()

        event_roles = [
            EventRole('admin', 10, 1),
            EventRole('reviewer', 3, 1)
        ]
        db.session.add_all(event_roles)
        db.session.commit()

        application_form = [
            self.create_application_form(1, True, False),
        ]
        db.session.add_all(application_form)
        db.session.commit()

        sections = [
            Section(application_form.id, 'Tell Us a Bit About You', '', 1),
            Section(application_form.id, 'Reference', 'Details of referree', 2)
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
            Question(1, sections[0].id, 'Why is attending the Deep Learning Indaba 2019 important to you?', 'Enter 50 to 150 words', 1,
                     'long_text', ''),
            Question(1, sections[0].id, 'How will you share what you have learnt after the Indaba?', 'Enter 50 to 150 words', 2,
                     'long_text', ''),
            Question(1, sections[0].id, 'Have you worked on a project that uses machine learning?', 'Enter 50 to 150 words', 1,
                     'long_text', ''),
            Question(1, sections[0].id, 'Would you like to be considered for a travel award?', 'Enter 50 to 150 words', 2, 'long_text',
                     ''),
            Question(1, sections[0].id, 'Did you attend the 2017 or 2018 Indaba', 'Select an option...', 3, 'multi-choice', None, None,
                     True, None, options)
            Question(1, sections[1].id,
                     'title', 'Enter 50 to 150 words', 1, 'long_text', ''),
            Question(1, sections[1].id,
                     'firstname', 'Enter 50 to 150 words', 2, 'long_text', ''),
            Question(1, sections[1].id,
                     'lastname', 'Enter 50 to 150 words', 3, 'long_text', ''),
            Question(1, sections[1].id,
                     'email', 'Enter 50 to 150 words', 4, 'long_text', ''),
        ]

        questions[5].key = 'nomination_title'
        questions[6].key = 'nomination_firstname'
        questions[7].key = 'nomination_lastname'
        questions[8].key = 'nomination_email'
        db.session.add_all(questions)
        db.session.commit()


        closed_review = ReviewForm(2, datetime(2018, 4, 30))
        closed_review.close()
        review_forms = [
            ReviewForm(1, datetime(2019, 4, 30)),
            closed_review
        ]
        db.session.add_all(review_forms)
        db.session.commit()

        review_configs = [
            ReviewConfiguration(review_form_id=review_forms[0].id, num_reviews_required=3, num_optional_reviews=0),
            ReviewConfiguration(review_form_id=review_forms[1].id, num_reviews_required=3, num_optional_reviews=0)
        ]
        db.session.add_all(review_configs)
        db.session.commit()

        review_questions = [
            ReviewQuestion(1, 1, None, None, 'multi-choice', None, None, True, 1, None, None, 0),
            ReviewQuestion(1, 2, None, None, 'multi-choice', None, None, True, 2, None, None, 0),
            ReviewQuestion(2, 3, None, None, 'multi-choice', None, None, True, 1, None, None, 0),
            ReviewQuestion(2, 4, None, None, 'information', None, None, False, 2, None, None, 0)
        ]
        db.session.add_all(review_questions)
        db.session.commit()

        self.test_response = Response(  # Nominating other
            self.application_form.id, self.first_user.id)

        self.add_to_db(self.test_response)
        answers = [
            Answer(self.test_response.id, questions[5].id, 'Mx'),
            Answer(self.test_response.id, questions[6].id, 'Skittles'),
            Answer(self.test_response.id, questions[7].id, 'Cat'),
            Answer(self.test_response.id, questions[8].id, 'skittles@box.com'),
        ]
        db.session.add_all(answers)
        db.session.commit()

        self.first_headers = self.get_auth_header_for("firstuser@mail.com")

        db.session.flush()

    def test_get_reference_request_by_event_id(self):
        self.seed_static_data()
        reference_req = ReferenceRequest(1, 'Mr', 'John', 'Snow', 'Supervisor', 'common@email.com')
        reference_request_repository.create(reference_req)
        REFERENCE_DETAIL = {
            'token': reference_req.token,
            'uploaded_document': 'DOCT-UPLOAD-78999',
        }

        params = {'event_id': 1}
        response = self.app.get('/api/v1/review', headers=self.get_auth_header_for('r1@r.com'), data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 6) # len as counted by number of data (dict) items

        self.assertEqual(data['references'][0], REFERENCE_DETAIL)
        self.assertEqual(data['references'][0]['token'], reference_req.token)
        self.assertEqual(data['references'][0]['uploaded_document'], 'DOCT-UPLOAD-78999')

    def test_get_reference_request_with_two_references(self):

        self.seed_static_data()
        reference_req = ReferenceRequest(1, 'Mr', 'John', 'Snow', 'Supervisor', 'common@email.com')
        reference_req2 = ReferenceRequest(1, 'Mrs', 'John', 'Jones', 'Manager', 'john@email.com')
        reference_request_repository.create(reference_req)
        reference_request_repository.create(reference_req2)

        REFERENCE_DETAIL = {
            'token': reference_req.token,
            'uploaded_document': 'DOCT-UPLOAD-78999',
        }
        REFERENCE_DETAIL_2 = {
            'token': reference_req2.token,
            'uploaded_document': 'DOCT-UPLOAD-78979', #
        }
        # params = {'event_id': 1}
        response = self.app.post(
            '/api/v1/reference', data=REFERENCE_DETAIL, headers=self.first_headers)
        self.assertEqual(response.status_code, 201)

        response = self.app.put(
            '/api/v1/reference', data=REFERENCE_DETAIL_2, headers=self.first_headers)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)

        # To be confirmed once above test is correct:
        self.assertEqual(data['references'][0], REFERENCE_DETAIL)
        self.assertEqual(data['references'][0]['token'], reference_req.token)
        self.assertEqual(data['references'][0]['uploaded_document'], 'DOCT-UPLOAD-78999')

        self.assertEqual(data['references'][1], REFERENCE_DETAIL_2)
        self.assertEqual(data['references'][1]['token'], reference_req2.token)
        self.assertEqual(data['references'][1]['uploaded_document'], 'DOCT-UPLOAD-78979')


        