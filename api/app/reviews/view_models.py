from app.utils import misc

class Identifier():
    def __init__(self, answer, language):
        question_translation = answer.question.get_translation(language)
        if question_translation is None:
            question_translation = answer.question.get_translation('en')
        
        self.headline = question_translation.headline
        self.value = answer.value


class Score():
    def __init__(self, review_score, language):
        review_question_translation = review_score.review_question.get_translation(language)
        self.headline = review_question_translation.headline
        self.description = review_question_translation.description
        self.type = review_score.review_question.type
        self.score = review_score.value
        self.weight = review_score.review_question.weight


class ReviewResponseDetail():
    def __init__(self, review_response):
        self.review_response_id = review_response.id
        self.response_id = review_response.response_id

        self.reviewer_user_title = review_response.reviewer_user.user_title
        self.reviewer_user_firstname = review_response.reviewer_user.firstname
        self.reviewer_user_lastname = review_resposne.reviewer_user.lastname
        
        self.response_user_title = review_response.response.user.user_title
        self.response_user_firstname = review_response.response.user.firstname
        self.response_user_lastname = review_response.response.user.lastname

        self.identifiers = [
            Identifier(answer, review_response.language)
            for answer in review_response.response.answers
            if answer.question.is_review_identifier()
        ]

        self.scores = [
            Score(review_score, review_response.language)
            for review_score in review_response.review_scores
            if review_score.review_question.type == 'multi-choice' or review_score.review_question.type == 'long-text' or review_score.review_question.type == 'short-text'
        ]

        self.total = self.get_total()

    
    def get_total(self):
        return sum([
            misc.try_parse_flow(score.value) * score.weight
            for score in self.scores
            if score.weight > 0
        ])