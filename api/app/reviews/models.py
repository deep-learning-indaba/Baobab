from datetime import datetime
from typing import Any, Callable, Mapping

from app import db
from app.utils import misc


class ReviewForm(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(
        db.Integer(), db.ForeignKey("application_form.id"), nullable=False
    )
    is_open = db.Column(db.Boolean(), nullable=False)
    deadline = db.Column(db.DateTime(), nullable=False)
    stage = db.Column(db.Integer(), nullable=False)
    active = db.Column(db.Boolean(), nullable=False)

    application_form = db.relationship(
        "ApplicationForm", foreign_keys=[application_form_id]
    )
    review_sections = db.relationship("ReviewSection", order_by="ReviewSection.order")

    def __init__(self, application_form_id, deadline, stage, active):
        self.application_form_id = application_form_id
        self.is_open = True
        self.deadline = deadline
        self.stage = stage
        self.active = active

    def close(self):
        self.is_open = False

    def deactivate(self):
        self.active = False

    def activate(self):
        self.active = True


class ReviewSection(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    review_form_id = db.Column(
        db.Integer(), db.ForeignKey("review_form.id"), nullable=False
    )
    order = db.Column(db.Integer(), nullable=False)

    translations = db.relationship("ReviewSectionTranslation", lazy="dynamic")
    review_questions = db.relationship(
        "ReviewQuestion", order_by="ReviewQuestion.order"
    )
    review_form = db.relationship("ReviewForm", foreign_keys=[review_form_id])

    def __init__(self, review_form_id, order):
        self.review_form_id = review_form_id
        self.order = order

    def get_translation(self, language):
        translation = self.translations.filter_by(language=language).first()
        return translation

    def _translations_for_field(
        self, accessor_fn: Callable[["ReviewSectionTranslation"], Any]
    ) -> Mapping[str, Any]:
        translations = {}
        for translation in self.translations:
            translations[translation.language] = accessor_fn(translation)
        return translations

    @property
    def headline_translations(self):
        return self._translations_for_field(lambda t: t.headline)

    @property
    def description_translations(self):
        return self._translations_for_field(lambda t: t.description)


class ReviewSectionTranslation(db.Model):
    __tablename__ = "review_section_translation"
    __table_args__ = tuple(
        [
            db.UniqueConstraint(
                "review_section_id", "language", name="uq_review_section_id_language"
            )
        ]
    )

    id = db.Column(db.Integer(), primary_key=True)
    review_section_id = db.Column(
        db.Integer(), db.ForeignKey("review_section.id"), nullable=False
    )
    language = db.Column(db.String(2), nullable=False)

    headline = db.Column(db.String(), nullable=True)
    description = db.Column(db.String(), nullable=True)

    review_section = db.relationship("ReviewSection", foreign_keys=[review_section_id])

    def __init__(self, review_section_id, language, headline=None, description=None):
        self.review_section_id = review_section_id
        self.language = language
        self.headline = headline
        self.description = description


class ReviewQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    review_section_id = db.Column(
        db.Integer(), db.ForeignKey("review_section.id"), nullable=False
    )
    question_id = db.Column(db.Integer(), db.ForeignKey("question.id"), nullable=True)

    type = db.Column(db.String(), nullable=False)

    is_required = db.Column(db.Boolean(), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    weight = db.Column(db.Float(), nullable=False)
    review_section = db.relationship("ReviewSection", foreign_keys=[review_section_id])
    question = db.relationship("Question", foreign_keys=[question_id])

    translations = db.relationship("ReviewQuestionTranslation", lazy="dynamic")

    def __init__(
        self, review_section_id, question_id, type, is_required, order, weight
    ):
        self.review_section_id = review_section_id
        self.question_id = question_id
        self.type = type
        self.is_required = is_required
        self.order = order
        self.weight = weight

    def get_translation(self, language):
        translation = self.translations.filter_by(language=language).first()
        return translation

    def _translations_for_field(
        self, accessor_fn: Callable[["ReviewQuestionTranslation"], Any]
    ) -> Mapping[str, Any]:
        translations = {}
        for translation in self.translations:
            translations[translation.language] = accessor_fn(translation)
        return translations

    @property
    def headline_translations(self):
        return self._translations_for_field(lambda t: t.headline)

    @property
    def description_translations(self):
        return self._translations_for_field(lambda t: t.description)

    @property
    def placeholder_translations(self):
        return self._translations_for_field(lambda t: t.placeholder)

    @property
    def options_translations(self):
        return self._translations_for_field(lambda t: t.options)

    @property
    def validation_regex_translations(self):
        return self._translations_for_field(lambda t: t.validation_regex)

    @property
    def validation_text_translations(self):
        return self._translations_for_field(lambda t: t.validation_text)


class ReviewQuestionTranslation(db.Model):
    __tablename__ = "review_question_translation"
    __table_args__ = tuple(
        [
            db.UniqueConstraint(
                "review_question_id", "language", name="uq_review_question_id_language"
            )
        ]
    )

    id = db.Column(db.Integer(), primary_key=True)
    review_question_id = db.Column(
        db.Integer(), db.ForeignKey("review_question.id"), nullable=False
    )
    language = db.Column(db.String(2), nullable=False)

    description = db.Column(db.String(), nullable=True)
    headline = db.Column(db.String(), nullable=True)
    placeholder = db.Column(db.String(), nullable=True)
    options = db.Column(db.JSON(), nullable=True)
    validation_regex = db.Column(db.String(), nullable=True)
    validation_text = db.Column(db.String(), nullable=True)

    def __init__(
        self,
        review_question_id,
        language,
        description=None,
        headline=None,
        placeholder=None,
        options=None,
        validation_regex=None,
        validation_text=None,
    ):
        self.review_question_id = review_question_id
        self.language = language
        self.description = description
        self.headline = headline
        self.placeholder = placeholder
        self.options = options
        self.validation_regex = validation_regex
        self.validation_text = validation_text


class ReviewResponse(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    review_form_id = db.Column(
        db.Integer(), db.ForeignKey("review_form.id"), nullable=False
    )
    reviewer_user_id = db.Column(
        db.Integer(), db.ForeignKey("app_user.id"), nullable=False
    )
    response_id = db.Column(db.Integer(), db.ForeignKey("response.id"), nullable=False)
    submitted_timestamp = db.Column(db.DateTime(), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    is_submitted = db.Column(db.Boolean(), nullable=False)
    submitted_timestamp = db.Column(db.DateTime(), nullable=True)

    review_form = db.relationship("ReviewForm", foreign_keys=[review_form_id])
    reviewer_user = db.relationship("AppUser", foreign_keys=[reviewer_user_id])
    response = db.relationship("Response", foreign_keys=[response_id])
    review_scores = db.relationship(
        "ReviewScore",
        primaryjoin="and_(ReviewResponse.id==ReviewScore.review_response_id,"
        "ReviewScore.is_active==True)",
    )

    def __init__(self, review_form_id, reviewer_user_id, response_id, language):
        self.review_form_id = review_form_id
        self.reviewer_user_id = reviewer_user_id
        self.response_id = response_id
        self.language = language
        self.is_submitted = False

    def submit(self):
        self.is_submitted = True
        self.submitted_timestamp = datetime.now()

    def calculate_score(self):
        return sum(
            [
                misc.try_parse_float(score.value) * score.review_question.weight
                for score in self.review_scores
                if score.review_question.weight > 0
            ]
        )


class ReviewScore(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    review_response_id = db.Column(
        db.Integer(), db.ForeignKey("review_response.id"), nullable=False
    )
    review_question_id = db.Column(
        db.Integer(), db.ForeignKey("review_question.id"), nullable=False
    )
    value = db.Column(db.String(), nullable=False)
    is_active = db.Column(db.Boolean(), nullable=False)
    created_on = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    review_response = db.relationship(
        "ReviewResponse", foreign_keys=[review_response_id]
    )
    review_question = db.relationship(
        "ReviewQuestion", foreign_keys=[review_question_id]
    )

    def __init__(self, review_question_id, value):
        self.review_question_id = review_question_id
        self.value = value
        self.is_active = True
        created_on = datetime.now()


class ReviewConfiguration(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    review_form_id = db.Column(
        db.Integer(), db.ForeignKey("review_form.id"), nullable=False
    )
    num_reviews_required = db.Column(db.Integer(), nullable=False)
    num_optional_reviews = db.Column(db.Integer(), nullable=False)
    drop_optional_question_id = db.Column(
        db.Integer(), db.ForeignKey("review_question.id"), nullable=True
    )
    drop_optional_agreement_values = db.Column(db.String(), nullable=True)

    review_form = db.relationship("ReviewForm", foreign_keys=[review_form_id])
    review_question = db.relationship(
        "ReviewQuestion", foreign_keys=[drop_optional_question_id]
    )
