"""Add Indaba X South Africa Registration Form

Revision ID: bda5cebe15fd
Revises: 627a96dad7e8
Create Date: 2023-06-19 19:39:30.784502

"""

# revision identifiers, used by Alembic.
revision = 'bda5cebe15fd'
down_revision = '627a96dad7e8'

from datetime import datetime
from enum import Enum

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from app import db

Base = declarative_base()

class Organisation(Base):

    __tablename__ = "organisation"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    system_name = db.Column(db.String(50), nullable=False)
    small_logo = db.Column(db.String(100), nullable=False)
    large_logo = db.Column(db.String(100), nullable=False)
    icon_logo = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(100), nullable=False)
    email_from = db.Column(db.String(100), nullable=True)
    system_url = db.Column(db.String(100), nullable=False)
    privacy_policy = db.Column(db.String(100), nullable=False)
    languages = db.Column(db.JSON(), nullable=False)
    iso_currency_code = db.Column(db.String(3), nullable=True)
    stripe_api_publishable_key = db.Column(db.String(200), nullable=True)
    stripe_api_secret_key = db.Column(db.String(200), nullable=True)
    stripe_webhook_secret_key = db.Column(db.String(200), nullable=True)
    
class EventType(Enum):
    EVENT = 'event'
    AWARD = 'award'
    CALL = 'call'
    PROGRAMME = 'programme'
    JOURNAL = 'journal'
    JOURNAL = 'JOURNAL'

class Event(Base):

    __tablename__ = "event"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    start_date = db.Column(db.DateTime(), nullable=False)
    end_date = db.Column(db.DateTime(), nullable=True)
    key = db.Column(db.String(255), nullable=False, unique=True)
    organisation_id = db.Column(db.Integer(), db.ForeignKey('organisation.id'), nullable=False)
    email_from = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    application_open = db.Column(db.DateTime(), nullable=True)
    application_close = db.Column(db.DateTime(), nullable=True)
    review_open = db.Column(db.DateTime(), nullable=True)
    review_close = db.Column(db.DateTime(), nullable=True)
    selection_open = db.Column(db.DateTime(), nullable=True)
    selection_close = db.Column(db.DateTime(), nullable=True)
    offer_open = db.Column(db.DateTime(), nullable=True)
    offer_close = db.Column(db.DateTime(), nullable=True)
    registration_open = db.Column(db.DateTime(), nullable=True)
    registration_close = db.Column(db.DateTime(), nullable=True)
    event_type = db.Column(db.Enum(EventType), nullable=False)
    travel_grant = db.Column(db.Boolean(), nullable=False)
    miniconf_url = db.Column(db.String(100), nullable=True)

    def __init__(
        self,
        names,
        descriptions,
        start_date,
        end_date,
        key,
        organisation_id,
        email_from,
        url,
        application_open,
        application_close,
        review_open,
        review_close,
        selection_open,
        selection_close,
        offer_open,
        offer_close,
        registration_open,
        registration_close,
        event_type,
        travel_grant,
        miniconf_url=None
    ):
        self.start_date = start_date
        self.end_date = None if event_type == EventType.JOURNAL else end_date
        self.key = key
        self.organisation_id = organisation_id
        self.email_from = email_from
        self.url = url
        self.application_open = application_open
        self.application_close = application_close
        self.review_open = review_open
        self.review_close = review_close
        self.selection_open = selection_open
        self.selection_close = selection_close
        self.offer_open = offer_open
        self.offer_close = offer_close
        self.registration_open = registration_open
        self.registration_close = registration_close
        self.event_roles = []
        self.event_type = event_type
        self.travel_grant = travel_grant
        self.miniconf_url = miniconf_url
        self.event_fees = []

class RegistrationForm(Base):

    __tablename__ = "registration_form"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey(
        Event.id), nullable=False)

    def __init__(self, event_id):
        self.event_id = event_id

class RegistrationSection(Base):

    __tablename__ = "registration_section"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    registration_form_id = db.Column(db.Integer(), db.ForeignKey(
        "registration_form.id"), nullable=False)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    show_for_tag_id = db.Column(db.Integer(), db.ForeignKey('tag.id'), nullable=True)
    show_for_invited_guest = db.Column(db.Boolean(), nullable=True)

    registration_questions = db.relationship('RegistrationQuestion')

    def __init__(self, registration_form_id, name, description, order, show_for_tag_id=None, show_for_invited_guest=None):
        self.registration_form_id = registration_form_id
        self.name = name
        self.description = description
        self.order = order
        self.show_for_tag_id = show_for_tag_id
        self.show_for_invited_guest = show_for_invited_guest

class RegistrationQuestion(Base):

    __tablename__ = "registration_question"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    registration_form_id = db.Column(db.Integer(), db.ForeignKey(
        "registration_form.id"), nullable=False)
    section_id = db.Column(db.Integer(), db.ForeignKey(
        "registration_section.id"), nullable=False)
    type = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    headline = db.Column(db.String(), nullable=False)
    placeholder = db.Column(db.String(), nullable=False)
    validation_regex = db.Column(db.String(), nullable=True)
    validation_text = db.Column(db.String(), nullable=True)
    order = db.Column(db.Integer(), nullable=False)
    options = db.Column(db.JSON(), nullable=True)
    is_required = db.Column(db.Boolean(), nullable=False)
    required_value = db.Column(db.String(), nullable=True)
    depends_on_question_id = db.Column(db.Integer(), db.ForeignKey(
        "registration_question.id"), nullable=True)
    hide_for_dependent_value = db.Column(db.String(), nullable=True)

    def __init__(
            self,
            registration_form_id,
            section_id,
            headline,
            placeholder,
            order,
            type,
            validation_regex=None,
            validation_text=None,
            is_required=True,
            description='',
            options=None,
            required_value=None
    ):
        self.registration_form_id = registration_form_id
        self.section_id = section_id
        self.headline = headline
        self.placeholder = placeholder
        self.order = order
        self.type = type
        self.description = description
        self.options = options
        self.is_required = is_required
        self.validation_regex = validation_regex
        self.validation_text = validation_text
        self.required_value = required_value

class Country(Base):
    __tablename__ = 'country'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __init__(self, name):
        self.name = name

class TagType(Enum):
    RESPONSE = 'response'
    REGISTRATION = 'registration'
    GRANT = 'grant'

class Tag(Base):
    __tablename__ = 'tag'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    tag_type = db.Column(db.Enum(TagType), nullable=True)
    active = db.Column(db.Boolean(), nullable=False, default=True)

class TagTranslation(db.Model):
    __tablename__ = 'tag_translation'
    __table_args__ = (
        db.UniqueConstraint('tag_id', 'language', name='uq_tag_id_language'),
        {'extend_existing': True}
    )
    id = db.Column(db.Integer(), primary_key=True)
    tag_id = db.Column(db.Integer(), db.ForeignKey('tag.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=True)

def get_country_list(session):
    countries = session.query(Country).all()
    country_list = []
    for country in countries:
        country_list.append({
            'label': country.name,
            'value': country.name
        })
    return country_list

def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    event = session.query(Event).filter_by(key='indabax2023').first()
    if not event:
        org = session.query(Organisation).filter_by(domain='indabax').first()
        event = Event(
            None,
            None,
            datetime(2023, 7, 12),
            datetime(2023, 7, 14),
            'indabax2023',
            org.id,
            'info@indabax.co.za',
            'https://indabax.co.za',
            datetime(2023, 5, 22),
            datetime(2023, 6, 12),
            datetime(2023, 6, 10),
            datetime(2023, 6, 18),
            datetime(2023, 6, 15),
            datetime(2023, 6, 20),
            datetime(2023, 6, 16),
            datetime(2023, 7, 23),
            datetime(2023, 6, 16),
            datetime(2023, 7, 12),
            EventType.EVENT,
            True
        )
        session.add(event)
        session.commit()

    form = RegistrationForm(event.id)
    session.add(form)
    session.commit()

    pd_candidates_description = (
"""
This is the registration form for candidates who have been accepted to attend the Deep Learning IndabaX 2023. It should take about 5 minutes to complete.

Data usage: We will use the information you provide in this form for registration and coordination purposes for the Deep Learning IndabaX 2023. This may involve sharing your contact details with third-party service providers for the purposes of event management and organisation.
"""
    )
    pd_cand_section = RegistrationSection(form.id, 'Personal details', pd_candidates_description, 1, None, False)
    session.add(pd_cand_section)
    session.commit()

    mobile_number_q = RegistrationQuestion(
        form.id,
        pd_cand_section.id,
        "Mobile number",
        "Mobile number",
        1,
        "short-text",
        description="Please include the country code."
    )

    poster_q = RegistrationQuestion(
        form.id,
        pd_cand_section.id,
        "Will you be bringing a poster?",
        "",
        2,
        "multi-choice",
        description="""Posters are a great way to learn, share, and get feedback on your work. The project does not have to be "done", in fact, it's probably more beneficial that your poster is on a work-in-progress project for something that you would like expert advice on. Take the opportunity.""" ,
        options=[
            {"value": "Yes", "label": "Yes"},
            {"value": "No", "label": "No"},
            {"value": "Maybe", "label": "Maybe"}
        ]
    )

    photographs_q = RegistrationQuestion(
        form.id,
        pd_cand_section.id,
        "Photographs and/or video taken by DLXSA, or others on behalf of DLXSA, may include your image or likeness. You agree that DLXSA may use such photographs and/or video for any purpose without compensation to you.",
        "",
        3,
        "multi-choice",
        validation_text="You must agree to the photography policy.",
        options=[{"value": "yes", "label":"Yes"}]
    )

    session.add_all([mobile_number_q, poster_q, photographs_q])
    session.commit()

    pd_ig_description = (
"""
This is the registration form for invited guests of the Deep Learning IndabaX 2023.

Data usage: We will use the information you provide in this form for registration and coordination purposes for the Deep Learning IndabaX 2023. This may involve sharing your contact details with third-party service providers for the purposes of event management and organisation.
"""
    )
    pd_ig_section = RegistrationSection(form.id, 'Personal details', pd_ig_description, 2, None, True)
    session.add(pd_ig_section)
    session.commit()

    mobile_number_ig_q = RegistrationQuestion(
        form.id,
        pd_ig_section.id,
        "Mobile number",
        "",
        1,
        "short-text",
        description="Please include the country code."
    )

    poster_ig_q = RegistrationQuestion(
        form.id,
        pd_ig_section.id,
        "Will you be bringing a poster?",
        "",
        2,
        "multi-choice",
        description="""Posters are a great way to learn, share, and get feedback on your work. The project does not have to be "done", in fact, it's probably more beneficial that your poster is on a work-in-progress project for something that you would like advice on.""" ,
        options=[
            {"value": "Yes", "label": "Yes"},
            {"value": "No", "label": "No"},
            {"value": "Maybe", "label": "Maybe"}
        ]
    )

    country = RegistrationQuestion(
        form.id,
        pd_ig_section.id,
        "Country of nationality",
        "",
        3,
        "multi-choice",
        description="For post-event reporting purposes.",
        options = get_country_list(session)
    )

    gender = RegistrationQuestion(
        form.id,
        pd_ig_section.id,
        "Gender",
        "",
        4,
        "multi-choice",
        description="For post-event reporting purposes.",
        options=[
            {"value": "female", "label": "Female"},
            {"value": "male", "label": "Male"},
            {"value": "transgender", "label": "Transgender"},
            {"value": "gender_variant_non_conforming", "label": "Gender variant / Non-conforming"},
            {"value": "prefer_not_to_say", "label": "Prefer not to say"},
            {"value": "other ", "label": "Other"}
        ]
    )

    ethnicity = RegistrationQuestion(
        form.id,
        pd_ig_section.id,
        "Ethnicity",
        "",
        5,
        "multi-choice",
        description="For post-event reporting purposes.",
        options=[
            {"value": "black", "label": "Black"},
            {"value": "coloured", "label": "Coloured"},
            {"value": "indian", "label": "Indian"},
            {"value": "white", "label": "White"},
            {"value": "prefer_not_to_say", "label": "Prefer not to say"}
        ]
    )

    affiliation = RegistrationQuestion(
        form.id,
        pd_ig_section.id,
        "Affiliation",
        "",
        6,
        "short-text"
    )

    t_shirt = RegistrationQuestion(
        form.id,
        pd_ig_section.id,
        "T-shirt size",
        "",
        7,
        "multi-choice",
        options=[
            {"value": "XS", "label": "XS"},
            {"value": "S", "label": "S"},
            {"value": "M", "label": "M"},
            {"value": "L", "label": "L"},
            {"value": "XL", "label": "XL"},
            {"value": "XXL", "label": "XXL"}
        ]
    )

    diet = RegistrationQuestion(
        form.id,
        pd_ig_section.id,
        "Dietary requirements",
        "",
        8,
        "multi-choice",
        options=[
            {"value": "vegetarian", "label": "Vegetarian"},
            {"value": "vegan", "label": "Vegan"},
            {"value": "kosher", "label": "Kosher"},
            {"value": "halal", "label": "Halal"},
            {"value": "gluten-free", "label": "Gluten-free"},
            {"value": "none", "label": "None"}
        ]
    )

    session.add_all([mobile_number_ig_q, poster_ig_q, country, gender, ethnicity, affiliation, t_shirt, diet])
    session.commit()

    coc_section = RegistrationSection(
        form.id,
        "Code of Conduct",
        """We ask that you recall a central principle of African philosophy, whether you know it as ujamaa (Swahili), umuntu (Chichewa), ubuntu (Zulu), unhu (Shona), djema'a (Arabic), or through the many other words used across our continent: the philosophy of familyhood and unity. Our duty, as we come together at the Indaba, is to create a familyhood of people and cultures and learning, built on the principles of freedom, equality and unity; and towards the aim of strengthening African machine learning.

This means that every participant is responsible for providing a safe experience for all participants, regardless of gender, gender identity and expression, sexual orientation, ability, physical appearance, body size, race, ethnicity, nationality, age, religion, or socioeconomic status. As organisers, we are committed to these responsibilities and will not tolerate harassment of IndabaX participants in any form.

Every participant of the IndabaX must fiercely defend these principles, and make it their responsibility to uphold the spirit of togetherness.

If a participant engages in behaviour that breaks this code of conduct, the organisers retain the right to take any actions needed to keep the IndabaX a welcoming environment for all participants. You can report a concern or an incident through an anonymous report, or in person.

For details of expected conduct, unacceptable behaviour, how to report an incident, how we maintain a respectful community, and how we enforce these standards, please go to https://indabax.co.za/about/code-of-conduct/ or send a message to info@indabax.co.za.""",
        3
    )

    session.add(coc_section)
    session.commit()

    coc_q = RegistrationQuestion(
        form.id,
        coc_section.id,
        "I have read, understood, and agree with the Code of Conduct",
        "",
        1,
        "multi-choice",
        validation_text="You must agree to the Code of Conduct.",
        options=[{"value": "yes", "label":"Yes"}]
    )

    session.add(coc_q)
    session.commit()

    travel_tag = (
        session
        .query(Tag)
        .filter_by(event_id=form.event_id)
        .join(TagTranslation, TagTranslation.tag_id == Tag.id)
        .filter_by(name="Travel")
        .first()
    )
    if not travel_tag:
        travel_tag = Tag(event_id=event.id, tag_type=TagType.GRANT)
        session.add(travel_tag)
        session.commit()

        travel_tag_transaction = TagTranslation(
            tag_id=travel_tag.id,
            language='en',
            name='Travel',
            description="For financial and logistic flexibility of travel arrangements, we are directly paying the amount specified below to your bank account entered in the registration form. This may take up to 10 working days to process, so confirm quickly. We realise this may not be the amount you wished, yet we hope it is enough to cover a large, if not full, portion of travelling to the event. By accepting this grant, you agree to the terms and conditions: https://indabax.co.za/register/travel-grants/"
        )
        session.add(travel_tag_transaction)
        session.commit()

    travel_tag_id = travel_tag.id

    travel_section = RegistrationSection(
        form.id,
        "Travel Information",
        "You have been awarded a travel grant, meaning that the IndabaX will fund your travel to and from Cape Town. Because costs increase significantly over time, you must provide your travel details within two weeks of accepting your offer or receiving your invitation, otherwise the Deep Learning IndabaX South Africa reserves the right to withdraw your travel grant.",
        4,
        show_for_tag_id=travel_tag_id
    )

    session.add(travel_section)
    session.commit()

    full_name = RegistrationQuestion(
        form.id,
        travel_section.id,
        "Full name [exactly as on ID document]",
        "",
        1,
        "short-text",
        description="To match for banking details and checking in at the residence"
    )

    arrival_date = RegistrationQuestion(
        form.id,
        travel_section.id,
        "Estimated arrival date",
        "",
        2,
        "date",
        description="So we know when to expect you!"
    )

    arrival_time = RegistrationQuestion(
        form.id,
        travel_section.id,
        "Estimated arrival time",
        "",
        3,
        "short-text",
        validation_regex=r"^([01][0-9]|2[0-3]):([0-5][0-9])$",
        validation_text="Time must be specified in 24 hour format HH:MM",
        description="So we know when to expect you!"
    )

    contact_consent = RegistrationQuestion(
        form.id,
        travel_section.id,
        "Do you consent to your CONTACT DETAILS being shared with other travel grant awardees?",
        "",
        4,
        type='multi-choice',
        options=[
            {"value": "Yes", "label":"Yes, I consent"},
            {"value": "No", "label": "No, I do not consent to this"}
        ]
    )

    travel_tcs = RegistrationQuestion(
        form.id,
        travel_section.id,
        "Do you agree to the terms and conditions associated with a travel grant?",
        "",
        5,
        "multi-choice",
        validation_text="You must agree to the terms and conditions associated with a travel grant.",
        description="""1. A “travel grant” totalling the amount specified in the award letter (email entitled “IndabaX Outcome of Application” with status “ACCEPTED with Travel Grant”) will be transferred to you.
2. The travel grant must be used for travel expenses to and from the Deep Learning IndabaX South Africa, hereafter referred to as “IndabaX”.
3. Any travel grant money remaining after travel expenses have been paid may be used for sustenance expenses during the IndabaX. Sustenance expenses include food and beverages.
4. The money may not be used for any other purpose whatsoever.
5. Any balance remaining after travel and sustenance expenses have been paid shall be repaid to us within a week of the final date of the event.
6. Receipts must be kept for all expenditure and copies of the receipts must be sent to travel@indabax.co.za within a week of the final date of the event.
7. If your travel grant is insufficient to cover all of your travel expenses, we will not provide further funds unless extraordinary circumstances are present, which shall be determined at our full decision
8. Accommodation is only provided for the dates specified (check-in 11th July 2023, check-out 15th July 2023). You are welcome to arrive and leave at different dates but you must organise and pay for your own accommodation outside the specified date range.
9. Once funds have been transferred to your account, should you fail to attend the event, you will be required to repay us the travel grant in full within a week.
10. If your accommodation deposit has already been paid at the time that you inform us, or we become aware, that you are no longer attending, you will further be required to reimburse us the deposit on the accommodation. We will send you an invoice for the amount.
11. Clause 10 will not be applicable if you are able to provide us with evidence of unknown and not reasonably foreseeable circumstances preventing you from attending, such as hospitalisation, and if such evidence is provided within 2 days of you becoming aware of said circumstances. Whether the circumstances are unknown, not reasonably foreseeable, and prevented you from attending, shall be at our determination.
12. The parties consent to the jurisdiction of the Gauteng Division of the High Court of South Africa for any dispute arising from or relating to this agreement.""",
        options=[{"value": "yes", "label":"Yes"}]
    )

    session.add_all([full_name, arrival_date, arrival_time, contact_consent, travel_tcs])
    session.commit()

    bank_section = RegistrationSection(
        form.id,
        "Banking Details",
        "We will send the mentioned amount in your award letter to this account.",
        5,
        show_for_tag_id=travel_tag_id
    )

    session.add(bank_section)
    session.commit()

    bank_name = RegistrationQuestion(
        form.id,
        bank_section.id,
        "Bank name",
        "",
        1,
        type="short-text",
        description="Example: Nedbank"
    )

    branch_name = RegistrationQuestion(
        form.id,
        bank_section.id,
        "Branch name",
        "",
        2,
        type="short-text",
        description="Example: Century City",
        is_required=False
    )

    branch_code = RegistrationQuestion(
        form.id,
        bank_section.id,
        "Branch code",
        "",
        3,
        type="short-text",
        description="Example: 198765"
    )

    account_number = RegistrationQuestion(
        form.id,
        bank_section.id,
        "Account number",
        "",
        4,
        type="short-text",
        description="Example: 214709709140724"
    )

    session.add_all([bank_name, branch_name, branch_code, account_number])
    session.commit()

def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)
    event = session.query(Event).filter_by(key='indabax2023').first()
    form = session.query(RegistrationForm).filter_by(event_id=event.id).first()
    if form:
        op.execute("""DELETE FROM registration_question WHERE registration_form_id={}""".format(form.id))
        op.execute("""DELETE FROM registration_section WHERE registration_form_id={}""".format(form.id))
        op.execute("""DELETE FROM registration_form WHERE id={}""".format(form.id))
        session.commit()