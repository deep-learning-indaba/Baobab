from datetime import datetime
import json

from app import db, LOGGER
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

        assert data['reviews_remaining_count'] == 1

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

        assert data['reviews_remaining_count'] == 0
    
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

        assert data['reviews_remaining_count'] == 3