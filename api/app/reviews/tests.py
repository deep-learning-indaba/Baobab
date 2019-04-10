from datetime import datetime
import json

from app import db, LOGGER
from app.utils.testing import ApiTestCase
from app.events.models import Event, EventRole
from app.users.models import AppUser, UserCategory, Country
from app.applicationModel.models import ApplicationForm, Question, Section
from app.responses.models import Response, Answer, ResponseReviewer
from app.reviews.models import ReviewForm, ReviewQuestion, ReviewResponse, ReviewScore
from app.utils.errors import REVIEW_RESPONSE_NOT_FOUND, FORBIDDEN, USER_NOT_FOUND

class ReviewsApiTest(ApiTestCase):
    
    def seed_static_data(self):
        user_categories = [
            UserCategory('Honours'),
            UserCategory('Student'),
            UserCategory('MSc'),
            UserCategory('PhD')
        ]
        db.session.add_all(user_categories)
        db.session.commit()

        countries = [
            Country('South Africa'),
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
        
        reviewer1 = AppUser('r1@r.com', 'reviewer', '1', 'Mr', 1, 1, 'M', 'Wits', 'CS', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc')
        reviewer2 = AppUser('r2@r.com', 'reviewer', '2', 'Ms', 1, 1, 'F', 'UCT', 'Chem', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc')
        reviewer3 = AppUser('r3@r.com', 'reviewer', '3', 'Mr', 1, 1, 'M', 'UKZN', 'Phys', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc')
        reviewer4 = AppUser('r4@r.com', 'reviewer', '4', 'Ms', 1, 1, 'F', 'RU', 'Math', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc')
        candidate1 = AppUser('c1@c.com', 'candidate', '1', 'Mr', 1, 2, 'M', 'UWC', 'CS', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc')
        candidate2 = AppUser('c2@c.com', 'candidate', '2', 'Ms', 3, 4, 'F', 'RU', 'Chem', 'NA', 2, datetime(1984, 12, 12), 'Eng', 'abc')
        candidate3 = AppUser('c3@c.com', 'candidate', '3', 'Mr', 5, 6, 'M', 'UFH', 'Phys', 'NA', 3, datetime(1984, 12, 12), 'Eng', 'abc')
        candidate4 = AppUser('c4@c.com', 'candidate', '4', 'Ms', 7, 8, 'F', 'NWU', 'Math', 'NA', 4, datetime(1984, 12, 12), 'Eng', 'abc')
        system_admin = AppUser('sa@sa.com', 'system_admin', '1', 'Ms', 7, 8, 'F', 'NWU', 'Math', 'NA', 4, datetime(1984, 12, 12), 'Eng', 'abc', True)
        event_admin = AppUser('ea@ea.com', 'event_admin', '1', 'Ms', 7, 8, 'F', 'NWU', 'Math', 'NA', 4, datetime(1984, 12, 12), 'Eng', 'abc')
        reviewer1.verify()
        reviewer2.verify()
        reviewer3.verify()
        reviewer4.verify()
        candidate1.verify()
        candidate2.verify()
        candidate3.verify()
        candidate4.verify()
        system_admin.verify()
        event_admin.verify()
        users = [reviewer1, reviewer2, reviewer3, reviewer4, candidate1, candidate2, candidate3, candidate4, system_admin, event_admin]
        db.session.add_all(users)
        db.session.commit()

        events = [
            Event('indaba 2019', 'The Deep Learning Indaba 2019, Kenyatta University, Nairobi, Kenya ', datetime(2019, 8, 25), datetime(2019, 8, 31)),
            Event('indaba 2020', 'The Deep Learning Indaba 2018, Stellenbosch University, South Africa', datetime(2018, 9, 9), datetime(2018, 9, 15))
        ]
        db.session.add_all(events)
        db.session.commit()

        event_roles = [
            EventRole('admin', 10, 1),
            EventRole('reviewer', 3, 1)
        ]
        db.session.add_all(event_roles)
        db.session.commit()

        application_forms = [
            ApplicationForm(1, True, datetime(2019, 4, 30)),
            ApplicationForm(2, False, datetime(2018, 4, 30))
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

    def setup_one_reviewer_one_candidate(self):
        responses = [
            Response(1, 5, True)
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
        db.session.add_all(response_reviewers)
        db.session.commit()

    # def test_one_reviewer_one_candidate(self):
    #     self.seed_static_data()
    #     self.setup_one_reviewer_one_candidate()
    #     header = self.get_auth_header_for('r1@r.com')
    #     params = {'event_id': 1}

    #     response = self.app.get('/api/v1/review', headers=header, data=params)
    #     data = json.loads(response.data)

    #     self.assertEqual(data['reviews_remaining_count'], 1)

    # def setup_responses_and_no_reviewers(self):
    #     responses = [
    #         Response(1, 5, True)
    #     ]
    #     db.session.add_all(responses)
    #     db.session.commit()

    #     answers = [
    #         Answer(1, 1, 'I will learn alot.'),
    #         Answer(1, 2, 'I will share by doing talks.')
    #     ]
    #     db.session.add_all(answers)
    #     db.session.commit()

    # def test_no_response_reviewers(self):
    #     self.seed_static_data()
    #     self.setup_responses_and_no_reviewers()
    #     header = self.get_auth_header_for('r1@r.com')
    #     params = {'event_id': 1}

    #     response = self.app.get('/api/v1/review', headers=header, data=params)
    #     data = json.loads(response.data)

    #     self.assertEqual(data['reviews_remaining_count'], 0)
    
    # def setup_one_reviewer_three_candidates(self):
    #     responses = [
    #         Response(1, 5, True),
    #         Response(1, 6, True),
    #         Response(1, 7, True)
    #     ]
    #     db.session.add_all(responses)
    #     db.session.commit()

    #     answers = [
    #         Answer(1, 1, 'I will learn alot.'),
    #         Answer(1, 2, 'I will share by doing talks.'),
    #         Answer(2, 1, 'I want to do a PhD.'),
    #         Answer(2, 2, 'I will share by writing a blog.'),
    #         Answer(3, 1, 'I want to solve new problems.'),
    #         Answer(3, 2, 'I will share by tutoring.'),
    #     ]
    #     db.session.add_all(answers)
    #     db.session.commit()

    #     response_reviewers = [
    #         ResponseReviewer(1, 1),
    #         ResponseReviewer(2, 1),
    #         ResponseReviewer(3, 1)
    #     ]
    #     db.session.add_all(response_reviewers)
    #     db.session.commit()

    # def test_one_reviewer_three_candidates(self):
    #     self.seed_static_data()
    #     self.setup_one_reviewer_three_candidates()
    #     header = self.get_auth_header_for('r1@r.com')
    #     params = {'event_id': 1}

    #     response = self.app.get('/api/v1/review', headers=header, data=params)
    #     data = json.loads(response.data)

    #     self.assertEqual(data['reviews_remaining_count'], 3)

    # def setup_one_reviewer_three_candidates_and_one_completed_review(self):
    #     responses = [
    #         Response(1, 5, True),
    #         Response(1, 6, True),
    #         Response(1, 7, True)
    #     ]
    #     db.session.add_all(responses)
    #     db.session.commit()

    #     answers = [
    #         Answer(1, 1, 'I will learn alot.'),
    #         Answer(1, 2, 'I will share by doing talks.'),
    #         Answer(2, 1, 'I want to do a PhD.'),
    #         Answer(2, 2, 'I will share by writing a blog.'),
    #         Answer(3, 1, 'I want to solve new problems.'),
    #         Answer(3, 2, 'I will share by tutoring.')
    #     ]
    #     db.session.add_all(answers)
    #     db.session.commit()

    #     response_reviewers = [
    #         ResponseReviewer(1, 1),
    #         ResponseReviewer(2, 1),
    #         ResponseReviewer(3, 1)
    #     ]
    #     db.session.add_all(response_reviewers)
    #     db.session.commit()

    #     review_response = ReviewResponse(1, 1, 1)
    #     db.session.add(review_response)
    #     db.session.commit()

    # def test_one_reviewer_three_candidates_and_one_completed_review(self):
    #     self.seed_static_data()
    #     self.setup_one_reviewer_three_candidates_and_one_completed_review()
    #     header = self.get_auth_header_for('r1@r.com')
    #     params = {'event_id': 1}

    #     response = self.app.get('/api/v1/review', headers=header, data=params)
    #     data = json.loads(response.data)

    #     self.assertEqual(data['reviews_remaining_count'], 2)

    # def setup_one_reviewer_three_candidates_with_one_withdrawn_response_and_one_unsubmitted_response(self):
    #     withdrawn_response = Response(1, 5, True)
    #     withdrawn_response.withdraw_response()
    #     responses = [
    #         withdrawn_response,
    #         Response(1, 6, False),
    #         Response(1, 7, True)
    #     ]
    #     db.session.add_all(responses)
    #     db.session.commit()

    #     answers = [
    #         Answer(1, 1, 'I will learn alot.'),
    #         Answer(1, 2, 'I will share by doing talks.'),
    #         Answer(2, 1, 'I want to do a PhD.'),
    #         Answer(2, 2, 'I will share by writing a blog.'),
    #         Answer(3, 1, 'I want to solve new problems.'),
    #         Answer(3, 2, 'I will share by tutoring.')
    #     ]
    #     db.session.add_all(answers)
    #     db.session.commit()

    #     response_reviewers = [
    #         ResponseReviewer(1, 1),
    #         ResponseReviewer(2, 1),
    #         ResponseReviewer(3, 1)
    #     ]
    #     db.session.add_all(response_reviewers)
    #     db.session.commit()

    # def test_one_reviewer_three_candidates_with_one_withdrawn_response_and_one_unsubmitted_response(self):
    #     self.seed_static_data()
    #     self.setup_one_reviewer_three_candidates_with_one_withdrawn_response_and_one_unsubmitted_response()
    #     header = self.get_auth_header_for('r1@r.com')
    #     params = {'event_id': 1}

    #     response = self.app.get('/api/v1/review', headers=header, data=params)
    #     data = json.loads(response.data)

    #     self.assertEqual(data['reviews_remaining_count'], 1)

    # def setup_multiple_reviewers_with_different_subsets_of_candidates_and_reviews_completed(self):
    #     responses = [
    #         Response(1, 5, True),
    #         Response(1, 6, True),
    #         Response(1, 7, True),
    #         Response(1, 8, True)
    #     ]
    #     db.session.add_all(responses)
    #     db.session.commit()

    #     answers = [
    #         Answer(1, 1, 'I will learn alot.'),
    #         Answer(1, 2, 'I will share by doing talks.'),
    #         Answer(2, 1, 'I want to do a PhD.'),
    #         Answer(2, 2, 'I will share by writing a blog.'),
    #         Answer(3, 1, 'I want to solve new problems.'),
    #         Answer(3, 2, 'I will share by tutoring.'),
    #         Answer(4, 1, 'I want to exchange ideas with like minded people'),
    #         Answer(4, 2, 'I will mentor people interested in ML.')
    #     ]
    #     db.session.add_all(answers)
    #     db.session.commit()

    #     response_reviewers = [
    #         ResponseReviewer(1, 1),
    #         ResponseReviewer(2, 1),
    #         ResponseReviewer(3, 1),

    #         ResponseReviewer(2, 2),
    #         ResponseReviewer(3, 2),

    #         ResponseReviewer(1, 3),
    #         ResponseReviewer(2, 3),
    #         ResponseReviewer(3, 3),
    #         ResponseReviewer(4, 3),

    #         ResponseReviewer(1, 4)
    #     ]
    #     db.session.add_all(response_reviewers)
    #     db.session.commit()

    #     review_responses = [
    #         ReviewResponse(1, 2, 2),
    #         ReviewResponse(1, 3, 1),
    #         ReviewResponse(1, 3, 2),
    #         ReviewResponse(1, 4, 1)
    #     ]
    #     db.session.add_all(review_responses)
    #     db.session.commit()
    
    # def test_multiple_reviewers_with_different_subsets_of_candidates_and_reviews_completed(self):
    #     self.seed_static_data()
    #     self.setup_multiple_reviewers_with_different_subsets_of_candidates_and_reviews_completed()
    #     params = {'event_id': 1}

    #     header = self.get_auth_header_for('r1@r.com')
    #     response1 = self.app.get('/api/v1/review', headers=header, data=params)
    #     data1 = json.loads(response1.data)
    #     header = self.get_auth_header_for('r2@r.com')
    #     response2 = self.app.get('/api/v1/review', headers=header, data=params)
    #     data2 = json.loads(response2.data)
    #     header = self.get_auth_header_for('r3@r.com')
    #     response3 = self.app.get('/api/v1/review', headers=header, data=params)
    #     data3 = json.loads(response3.data)
    #     header = self.get_auth_header_for('r4@r.com')
    #     response4 = self.app.get('/api/v1/review', headers=header, data=params)
    #     data4 = json.loads(response4.data)

    #     self.assertEqual(data1['reviews_remaining_count'], 3)
    #     self.assertEqual(data2['reviews_remaining_count'], 1)
    #     self.assertEqual(data3['reviews_remaining_count'], 2)
    #     self.assertEqual(data4['reviews_remaining_count'], 0)

    # def test_skipping(self):
    #     self.seed_static_data()
    #     self.setup_one_reviewer_three_candidates()
    #     params = {'event_id': 1, 'skip': 1}
    #     header = self.get_auth_header_for('r1@r.com')

    #     response = self.app.get('/api/v1/review', headers=header, data=params)
    #     data = json.loads(response.data)

    #     self.assertEqual(data['response']['user_id'], 6)
    #     self.assertEqual(data['response']['answers'][0]['value'], 'I want to do a PhD.')
    #     self.assertEqual(data['user']['affiliation'], 'RU')
    #     self.assertEqual(data['user']['department'], 'Chem')
    #     self.assertEqual(data['user']['nationality_country'], 'Botswana')
    #     self.assertEqual(data['user']['residence_country'], 'Namibia')
    #     self.assertEqual(data['user']['user_category'], 'Student')
        
    # def test_high_skip_defaults_to_last_review(self):
    #     self.seed_static_data()
    #     self.setup_one_reviewer_three_candidates()
    #     params = {'event_id': 1, 'skip': 5}
    #     header = self.get_auth_header_for('r1@r.com')

    #     response = self.app.get('/api/v1/review', headers=header, data=params)
    #     data = json.loads(response.data)

    #     self.assertEqual(data['response']['user_id'], 7)
    #     self.assertEqual(data['response']['answers'][1]['value'], 'I will share by tutoring.')
    #     self.assertEqual(data['user']['affiliation'], 'UFH')
    #     self.assertEqual(data['user']['department'], 'Phys')
    #     self.assertEqual(data['user']['nationality_country'], 'Zimbabwe')
    #     self.assertEqual(data['user']['residence_country'], 'Mozambique')
    #     self.assertEqual(data['user']['user_category'], 'MSc')

    # def setup_candidate_who_has_applied_to_multiple_events(self):
    #     responses = [
    #         Response(1, 5, True),
    #         Response(2, 5, True)
    #     ]
    #     db.session.add_all(responses)
    #     db.session.commit()

    #     answers = [
    #         Answer(1, 1, 'I will learn alot.'),
    #         Answer(1, 2, 'I will share by doing talks.'),
    #         Answer(2, 3, 'Yes I worked on a vision task.'),
    #         Answer(2, 4, 'Yes I want the travel award.')
    #     ]
    #     db.session.add_all(answers)
    #     db.session.commit()

    #     response_reviewers = [
    #         ResponseReviewer(1, 1),
    #         ResponseReviewer(2, 1)
    #     ]
    #     db.session.add_all(response_reviewers)
    #     db.session.commit()

    # def test_filtering_on_event_when_candidate_has_applied_to_more_than(self):
    #     self.seed_static_data()
    #     self.setup_candidate_who_has_applied_to_multiple_events()
    #     params = {'event_id': 2}
    #     header = self.get_auth_header_for('r1@r.com')

    #     response = self.app.get('/api/v1/review', headers=header, data=params)
    #     data = json.loads(response.data)

    #     self.assertEqual(data['reviews_remaining_count'], 1)
    #     self.assertEqual(data['response']['user_id'], 5)
    #     self.assertEqual(data['response']['answers'][0]['value'], 'Yes I worked on a vision task.')
    #     self.assertEqual(data['user']['affiliation'], 'UWC')
    #     self.assertEqual(data['user']['department'], 'CS')
    #     self.assertEqual(data['user']['nationality_country'], 'South Africa')
    #     self.assertEqual(data['user']['residence_country'], 'Egypt')
    #     self.assertEqual(data['user']['user_category'], 'Honours')

    # def setup_multi_choice_answer(self):
    #     response = Response(1, 5, True)
    #     db.session.add(response)
    #     db.session.commit()

    #     answer = Answer(1, 5, 'indaba-2017')
    #     db.session.add(answer)
    #     db.session.commit()

    #     response_reviewer = ResponseReviewer(1, 1)
    #     db.session.add(response_reviewer)
    #     db.session.commit()
    
    # def test_multi_choice_answers_use_label_instead_of_value(self):
    #     self.seed_static_data()
    #     self.setup_multi_choice_answer()
    #     params = {'event_id': 1}
    #     header = self.get_auth_header_for('r1@r.com')

    #     response = self.app.get('/api/v1/review', headers=header, data=params)
    #     data = json.loads(response.data)

    #     self.assertEqual(data['response']['answers'][0]['value'], 'Yes, I attended the 2017 Indaba')

    # def test_review_response_not_found(self):
    #     self.seed_static_data()
    #     params = {'review_form_id': 55, 'response_id': 432}
    #     header = self.get_auth_header_for('r1@r.com')

    #     response = self.app.get('/api/v1/reviewresponse', headers=header, data=params)
    #     data = json.loads(response.data)

    #     self.assertEqual(response.status_code, REVIEW_RESPONSE_NOT_FOUND[1])

    # def setup_review_response(self):
    #     response = Response(1, 5, True)
    #     db.session.add(response)
    #     db.session.commit()

    #     answer = Answer(1, 1, 'To learn alot')
    #     db.session.add(answer)
    #     db.session.commit()

    #     review_response = ReviewResponse(1, 1, 1)
    #     review_response.review_scores.append(ReviewScore(1, 'answer1'))
    #     review_response.review_scores.append(ReviewScore(2, 'answer2'))
    #     db.session.add(review_response)
    #     db.session.commit()
        

    # def test_review_response(self):
    #     self.seed_static_data()
    #     self.setup_review_response()
    #     params = {'review_form_id': 1, 'response_id': 1}
    #     header = self.get_auth_header_for('r1@r.com')

    #     response = self.app.get('/api/v1/reviewresponse', headers=header, data=params)
    #     data = json.loads(response.data)

    #     self.assertEqual(data['id'], 1)
    #     self.assertEqual(data['response_id'], 1)
    #     self.assertEqual(data['review_form_id'], 1)
    #     self.assertEqual(data['reviewer_user_id'], 1)
    #     self.assertEqual(data['scores'][0]['value'], 'answer1')
    #     self.assertEqual(data['scores'][1]['value'], 'answer2')

    # def test_prevent_saving_review_response_reviewer_was_not_assigned_to_response(self):
    #     self.seed_static_data()
    #     params = json.dumps({'review_form_id': 1, 'response_id': 1, 'scores': [{'review_question_id': 1, 'value': 'test_answer'}]})
    #     header = self.get_auth_header_for('r1@r.com')

    #     response = self.app.post('/api/v1/reviewresponse', headers=header, data=params, content_type='application/json')

    #     self.assertEqual(response.status_code, FORBIDDEN[1])

    # def setup_response_reviewer(self):
    #     response = Response(1, 5, True)
    #     db.session.add(response)
    #     db.session.commit()

    #     response_reviewer = ResponseReviewer(1, 1)
    #     db.session.add(response_reviewer)
    #     db.session.commit()

    # def test_saving_review_response(self):
    #     self.seed_static_data()
    #     self.setup_response_reviewer()
    #     params = json.dumps({'review_form_id': 1, 'response_id': 1, 'scores': [{'review_question_id': 1, 'value': 'test_answer'}]})
    #     header = self.get_auth_header_for('r1@r.com')

    #     response = self.app.post('/api/v1/reviewresponse', headers=header, data=params, content_type='application/json')

    #     review_scores = db.session.query(ReviewScore).filter_by(review_response_id=1).all()
    #     self.assertEqual(response.status_code, 201)
    #     self.assertEqual(len(review_scores), 1)
    #     self.assertEqual(review_scores[0].value, 'test_answer')

    # def setup_existing_review_response(self):
    #     response = Response(1, 5, True)
    #     db.session.add(response)
    #     db.session.commit()

    #     response_reviewer = ResponseReviewer(1, 1)
    #     db.session.add(response_reviewer)
    #     db.session.commit()

    #     review_response = ReviewResponse(1, 1, 1)
    #     review_response.review_scores = [ReviewScore(1, 'test_answer1'), ReviewScore(2, 'test_answer2')]
    #     db.session.add(review_response)
    #     db.session.commit()

    # def test_updating_review_response(self):
    #     self.seed_static_data()
    #     self.setup_existing_review_response()
    #     params = json.dumps({'review_form_id': 1, 'response_id': 1, 'scores': [{'review_question_id': 1, 'value': 'test_answer3'}, {'review_question_id': 2, 'value': 'test_answer4'}]})
    #     header = self.get_auth_header_for('r1@r.com')

    #     response = self.app.put('/api/v1/reviewresponse', headers=header, data=params, content_type='application/json')

    #     review_scores = db.session.query(ReviewScore).filter_by(review_response_id=1).order_by(ReviewScore.review_question_id).all()
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(len(review_scores), 2)
    #     self.assertEqual(review_scores[0].value, 'test_answer3')
    #     self.assertEqual(review_scores[1].value, 'test_answer4')

    # def test_user_cant_assign_responsesreviewer_without_system_or_event_admin_role(self):
    #     self.seed_static_data()
    #     params = {'event_id': 1, 'reviewer_user_email': 'r2@r.com', 'num_reviews': 10}
    #     header = self.get_auth_header_for('c1@c.com')

    #     response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

    #     self.assertEqual(response.status_code, FORBIDDEN[1])

    # def test_reviewer_not_found(self):
    #     self.seed_static_data()
    #     params = {'event_id': 1, 'reviewer_user_email': 'non_existent@user.com', 'num_reviews': 10}
    #     header = self.get_auth_header_for('sa@sa.com')

    #     response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

    #     self.assertEqual(response.status_code, USER_NOT_FOUND[1])

    # def test_add_reviewer_with_no_roles(self):
    #     self.seed_static_data()
    #     params = {'event_id': 1, 'reviewer_user_email': 'r1@r.com', 'num_reviews': 10}
    #     header = self.get_auth_header_for('ea@ea.com')

    #     response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

    #     event_roles = db.session.query(EventRole).filter_by(user_id=1, event_id=1).all()
    #     self.assertEqual(len(event_roles), 1)
    #     self.assertEqual(event_roles[0].role, 'reviewer')

    # def test_add_reviewer_with_a_role(self):
    #     self.seed_static_data()
    #     params = {'event_id': 1, 'reviewer_user_email': 'ea@ea.com', 'num_reviews': 10}
    #     header = self.get_auth_header_for('sa@sa.com')

    #     response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

    #     event_roles = db.session.query(EventRole).filter_by(user_id=10, event_id=1).order_by(EventRole.id).all()
    #     self.assertEqual(len(event_roles), 2)
    #     self.assertEqual(event_roles[0].role, 'admin')
    #     self.assertEqual(event_roles[1].role, 'reviewer')

    # def setup_responses_without_reviewers(self):
    #     responses = [
    #         Response(1, 5, True),
    #         Response(1, 6, True),
    #         Response(1, 7, True),
    #         Response(1, 8, True)
    #     ]
    #     db.session.add_all(responses)
    #     db.session.commit()

    # def test_adding_first_reviewer(self):
    #     self.seed_static_data()
    #     self.setup_responses_without_reviewers()
    #     params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 4}
    #     header = self.get_auth_header_for('ea@ea.com')

    #     response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)
    #     response_reviewers = db.session.query(ResponseReviewer).filter_by(reviewer_user_id=3).all()
    #     self.assertEqual(response.status_code, 201)
    #     self.assertEqual(len(response_reviewers), 4)
    
    # def test_limit_of_num_reviews(self):
    #     self.seed_static_data()
    #     self.setup_responses_without_reviewers()
    #     params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
    #     header = self.get_auth_header_for('ea@ea.com')

    #     response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

    #     response_reviewers = db.session.query(ResponseReviewer).filter_by(reviewer_user_id=3).all()
    #     self.assertEqual(len(response_reviewers), 3)

    # def setup_reviewer_with_own_response(self):
    #     responses = [
    #         Response(1, 3, True), # reviewer
    #         Response(1, 5, True) # someone else
    #     ]
    #     db.session.add_all(responses)
    #     db.session.commit()

    # def test_reviewer_does_not_get_assigned_to_own_response(self):
    #     self.seed_static_data()
    #     self.setup_reviewer_with_own_response()
    #     params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
    #     header = self.get_auth_header_for('ea@ea.com')

    #     response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

    #     response_reviewers = db.session.query(ResponseReviewer).filter_by(reviewer_user_id=3).all()
    #     self.assertEqual(len(response_reviewers), 1)
    #     self.assertEqual(response_reviewers[0].response_id, 2)

    # def setup_withdrawn_and_unsubmitted_responses(self):
    #     responses = [
    #         Response(1, 5, is_submitted=False, is_withdrawn=False),
    #         Response(1, 6, is_submitted=True, is_withdrawn=True),
    #         Response(1, 7, is_submitted=True, is_withdrawn=False)
    #     ]
    #     db.session.add_all(responses)
    #     db.session.commit()

    # def test_withdrawn_and_unsubmitted_responses_are_not_assigned_reviewers(self):
    #     self.seed_static_data()
    #     self.setup_withdrawn_and_unsubmitted_responses()
    #     params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
    #     header = self.get_auth_header_for('ea@ea.com')

    #     response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

    #     response_reviewers = db.session.query(ResponseReviewer).filter_by(reviewer_user_id=3).all()
    #     self.assertEqual(len(response_reviewers), 1)
    #     self.assertEqual(response_reviewers[0].response_id, 3)

    # def setup_response_with_three_reviewers(self):
    #     response = Response(1, 5, True)
    #     db.session.add(response)
    #     db.session.commit()

    #     response_reviewers = [
    #         ResponseReviewer(1, 1),
    #         ResponseReviewer(1, 2),
    #         ResponseReviewer(1, 4)
    #     ]
    #     db.session.add_all(response_reviewers)
    #     db.session.commit()

    # def test_response_with_three_reviewers_does_not_get_assigned_another_reviewer(self):
    #     self.seed_static_data()
    #     self.setup_response_with_three_reviewers()
    #     params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
    #     header = self.get_auth_header_for('ea@ea.com')

    #     response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

    #     response_reviewers = db.session.query(ResponseReviewer).filter_by(reviewer_user_id=3).all()
    #     self.assertEqual(len(response_reviewers), 0)   

    # def setup_responsereview_with_different_reviewer(self):
    #     response = Response(1, 5, is_submitted=True)
    #     db.session.add(response)
    #     db.session.commit()

    #     response_reviewer = ResponseReviewer(1, 1)
    #     db.session.add(response_reviewer)
    #     db.session.commit()
        
    # def test_response_will_get_multiple_reviewers_assigned(self):
    #     self.seed_static_data()
    #     self.setup_responsereview_with_different_reviewer()
    #     params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
    #     header = self.get_auth_header_for('ea@ea.com')

    #     response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)
    #     response_reviewers = db.session.query(ResponseReviewer).order_by(ResponseReviewer.reviewer_user_id).all()

    #     self.assertEqual(len(response_reviewers), 2)
    #     self.assertEqual(response_reviewers[0].reviewer_user_id, 1)
    #     self.assertEqual(response_reviewers[1].reviewer_user_id, 3)
    
    # def setup_reviewer_is_not_assigned_to_response_more_than_once(self):
    #     response = Response(1,5,is_submitted=True)
    #     db.session.add(response)
    #     db.session.commit()
    
    # def test_reviewer_is_not_assigned_to_response_more_than_once(self):
    #     self.seed_static_data()
    #     self.setup_reviewer_is_not_assigned_to_response_more_than_once()
    #     params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
    #     header = self.get_auth_header_for('ea@ea.com')

    #     response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)
    #     response2 = self.app.post('/api/v1/reviewassignment', headers=header, data=params)
    #     response_reviewers = db.session.query(ResponseReviewer).all()

    #     self.assertEqual(len(response_reviewers), 1)

    def setup_review_responses_and_score(self):
        responses = [
            Response(1, 5, is_submitted=True),
            Response(1, 6, is_submitted=True),
            Response(1, 7, is_submitted=True)
        ]
        
        db.session.add_all(responses)
        db.session.commit()

        verdict_question = ReviewQuestion(1, None, None, 'Final Verdict', 'multi-choice', None, None, True, 3, None, None, 0)
        db.session.add(verdict_question)
        db.session.commit()

        review_responses = [
            ReviewResponse(1,3,1), 
            ReviewResponse(1,3,2),
            ReviewResponse(1,3,3)
        ]

        review_responses[0].review_scores = [ReviewScore(1, '23'), ReviewScore(5, 'Maybe')]
        review_responses[1].review_scores = [ReviewScore(1, '55'), ReviewScore(5, 'Yes')]
        
        db.session.add_all(review_responses)
        db.session.commit()


    def test_review_history_returned(self):
        self.seed_static_data()
        self.setup_review_responses_and_score()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r3@r.com')

        scores = db.session.query(ReviewScore).all()
        LOGGER.debug([scores[0].id, scores[0].review_response_id, scores[0].review_question_id, scores[0].value])
        LOGGER.debug([scores[1].id, scores[1].review_response_id, scores[1].review_question_id, scores[1].value])

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        LOGGER.debug(data)