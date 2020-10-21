from datetime import datetime

from app import db

class ReviewForm(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(db.Integer(), db.ForeignKey('application_form.id'), nullable=False)
    is_open = db.Column(db.Boolean(), nullable=False)
    deadline = db.Column(db.DateTime(), nullable=False)

    application_form = db.relationship('ApplicationForm', foreign_keys=[application_form_id])
    review_questions = db.relationship('ReviewQuestion')

    def __init__(self, application_form_id, deadline):
        self.application_form_id = application_form_id
        self.is_open = True
        self.deadline = deadline

    def close(self):
        self.is_open = False


class ReviewQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    review_form_id = db.Column(db.Integer(), db.ForeignKey('review_form.id'), nullable=False)
    question_id = db.Column(db.Integer(), db.ForeignKey('question.id'), nullable=True)
    
    type = db.Column(db.String(), nullable=False)
    
    is_required = db.Column(db.Boolean(), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    weight = db.Column(db.Float(), nullable=False)
    review_form = db.relationship('ReviewForm', foreign_keys=[review_form_id])
    question = db.relationship('Question', foreign_keys=[question_id])

    translations = db.relationship('ReviewQuestionTranslation', lazy='dynamic')

    def __init__(self,
                 review_form_id,
                 question_id,
                 type,
                 is_required,
                 order,
                 weight):
        self.review_form_id = review_form_id
        self.question_id = question_id
        self.type = type
        self.is_required = is_required
        self.order = order
        self.weight = weight

    def get_translation(self, language):
        translation = self.translations.filter_by(language=language).first()
        return translation


class ReviewQuestionTranslation(db.Model):
    __tablename__ = 'review_question_translation'
    __table_args__ = tuple([db.UniqueConstraint('review_question_id', 'language', name='uq_review_question_id_language')])

    id = db.Column(db.Integer(), primary_key=True)
    review_question_id = db.Column(db.Integer(), db.ForeignKey('review_question.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)

    description = db.Column(db.String(), nullable=True)
    headline = db.Column(db.String(), nullable=True)
    placeholder = db.Column(db.String(), nullable=True)
    options = db.Column(db.JSON(), nullable=True)
    validation_regex = db.Column(db.String(), nullable=True)
    validation_text = db.Column(db.String(), nullable=True)

    def __init__(self, language, description=None, headline=None, placeholder=None, options=None, validation_regex=None, validation_text=None)
        self.description = description
        self.headline = headline
        self.placeholder = placeholder
        self.options = options
        self.validation_regex = validation_regex
        self.validation_text = validation_text


class ReviewResponse(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    review_form_id = db.Column(db.Integer(), db.ForeignKey('review_form.id'), nullable=False)
    reviewer_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    response_id = db.Column(db.Integer(), db.ForeignKey('response.id'), nullable=False)
    submitted_timestamp = db.Column(db.DateTime(), nullable=False)

    review_form = db.relationship('ReviewForm', foreign_keys=[review_form_id])
    reviewer_user = db.relationship('AppUser', foreign_keys=[reviewer_user_id])
    response = db.relationship('Response', foreign_keys=[response_id])
    review_scores = db.relationship('ReviewScore')

    def __init__(self,
                 review_form_id,
                 reviewer_user_id,
                 response_id):
        self.review_form_id = review_form_id
        self.reviewer_user_id = reviewer_user_id
        self.response_id = response_id
        self.submitted_timestamp = datetime.now()


class ReviewScore(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    review_response_id = db.Column(db.Integer(), db.ForeignKey('review_response.id'), nullable=False)
    review_question_id = db.Column(db.Integer(), db.ForeignKey('review_question.id'), nullable=False)
    value = db.Column(db.String(), nullable=False)

    review_response = db.relationship('ReviewResponse', foreign_keys=[review_response_id])
    review_question = db.relationship('ReviewQuestion', foreign_keys=[review_question_id])

    def __init__(self,
                 review_question_id,
                 value):
        self.review_question_id = review_question_id
        self.value = value


class ReviewConfiguration(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    review_form_id = db.Column(db.Integer(), db.ForeignKey('review_form.id'), nullable=False)
    num_reviews_required = db.Column(db.Integer(), nullable=False)
    num_optional_reviews = db.Column(db.Integer(), nullable=False)
    drop_optional_question_id = db.Column(db.Integer(), db.ForeignKey('review_question.id'), nullable=True)
    drop_optional_agreement_values = db.Column(db.String(), nullable=True)

    review_form = db.relationship('ReviewForm', foreign_keys=[review_form_id])
    review_question = db.relationship('ReviewQuestion', foreign_keys=[drop_optional_question_id])
