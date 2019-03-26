from datetime import datetime
import json

from app import db
from app.utils.testing import ApiTestCase
from app.events.models import Event
from app.users.models import AppUser, UserCategory, Country
from app.applicationModel.models import ApplicationForm, Question, Section
from app.responses.models import Response, Answer, ResponseReviewer
from app.reviews.models import ReviewForm, ReviewQuestion, ReviewResponse

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
        reviewer1.verify()
        reviewer2.verify()
        reviewer3.verify()
        reviewer4.verify()
        candidate1.verify()
        candidate2.verify()
        candidate3.verify()
        candidate4.verify()
        users = [reviewer1, reviewer2, reviewer3, reviewer4, candidate1, candidate2, candidate3, candidate4]
        db.session.add_all(users)
        db.session.commit()

        events = [
            Event('indaba 2019', 'The Deep Learning Indaba 2019, Kenyatta University, Nairobi, Kenya ', datetime(2019, 8, 25), datetime(2019, 8, 31)),
            Event('indaba 2020', 'The Deep Learning Indaba 2018, Stellenbosch University, South Africa', datetime(2018, 9, 9), datetime(2018, 9, 15))
        ]
        db.session.add_all(events)
        db.session.commit()

        application_forms = [
            ApplicationForm(1, True, datetime(2019, 4, 30)),
            ApplicationForm(2, False, datetime(2018, 4, 30))
        ]
        db.session.add_all(application_forms)
        db.session.commit()

        sections = [
            Section(1, 'Tell Us a Bit About You', '', 1),
            Section(2, 'Tell Us a Bit About You2', '', 2)
        ]
        db.session.add_all(sections)
        db.session.commit()

        questions = [
            Question(1, 1, 'Why is attending the Deep Learning Indaba 2019 important to you?', 'Enter 50 to 150 words', 1, 'long_text', ''),
            Question(1, 1, 'How will you share what you have learnt after the Indaba?', 'Enter 50 to 150 words', 2, 'long_text', ''),
            Question(2, 2, 'Have you worked on a project that uses machine learning?', 'Enter 50 to 150 words', 1, 'long_text', ''),
            Question(2, 2, 'Would you like to be considered for a travel award?', 'Enter 50 to 150 words', 2, 'long_text', '')
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

    def test_one_reviewer_one_candidate(self):
        self.seed_static_data()
        self.setup_one_reviewer_one_candidate()
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 1)

    def setup_responses_and_no_reviewers(self):
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

    def test_no_response_reviewers(self):
        self.seed_static_data()
        self.setup_responses_and_no_reviewers()
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 0)
    
    def setup_one_reviewer_three_candidates(self):
        responses = [
            Response(1, 5, True),
            Response(1, 6, True),
            Response(1, 7, True)
        ]
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
        db.session.add_all(response_reviewers)
        db.session.commit()

    def test_one_reviewer_three_candidates(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates()
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 3)

    def setup_one_reviewer_three_candidates_and_one_completed_review(self):
        responses = [
            Response(1, 5, True),
            Response(1, 6, True),
            Response(1, 7, True)
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
        withdrawn_response = Response(1, 5, True)
        withdrawn_response.withdraw_response()
        responses = [
            withdrawn_response,
            Response(1, 6, False),
            Response(1, 7, True)
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
            Response(1, 5, True),
            Response(1, 6, True),
            Response(1, 7, True),
            Response(1, 8, True)
        ]
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

            ResponseReviewer(1, 4)
        ]
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

        self.assertEqual(data['response']['user_id'], 6)
        self.assertEqual(data['response']['answers'][0]['value'], 'I want to do a PhD.')
        self.assertEqual(data['user']['affiliation'], 'RU')
        self.assertEqual(data['user']['department'], 'Chem')
        self.assertEqual(data['user']['nationality_country'], 'Botswana')
        self.assertEqual(data['user']['residence_country'], 'Namibia')
        self.assertEqual(data['user']['user_category'], 'Student')
        
    def test_high_skip_defaults_to_last_review(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates()
        params = {'event_id': 1, 'skip': 5}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['response']['user_id'], 7)
        self.assertEqual(data['response']['answers'][1]['value'], 'I will share by tutoring.')
        self.assertEqual(data['user']['affiliation'], 'UFH')
        self.assertEqual(data['user']['department'], 'Phys')
        self.assertEqual(data['user']['nationality_country'], 'Zimbabwe')
        self.assertEqual(data['user']['residence_country'], 'Mozambique')
        self.assertEqual(data['user']['user_category'], 'MSc')

    def setup_candidate_who_has_applied_to_multiple_events(self):
        responses = [
            Response(1, 5, True),
            Response(2, 5, True)
        ]
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
        self.assertEqual(data['user']['affiliation'], 'UWC')
        self.assertEqual(data['user']['department'], 'CS')
        self.assertEqual(data['user']['nationality_country'], 'South Africa')
        self.assertEqual(data['user']['residence_country'], 'Egypt')
        self.assertEqual(data['user']['user_category'], 'Honours')