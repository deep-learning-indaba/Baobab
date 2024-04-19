
from datetime import datetime

from app import db
from enum import Enum

class EventType(Enum):
    EVENT = 'event'
    AWARD = 'award'
    CALL = 'call'
    PROGRAMME = 'programme'
    JOURNAL = 'journal'

def check_open(open, close):
    now = datetime.now()
    if open and close:
        return now >= open and now < close
    elif open:
        return now >= open
    elif close:
        return now < close
    return True

def check_opening(open):
    now = datetime.now()
    if open:
        return now < open
    return True
class Event(db.Model):

    __tablename__ = "event"

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
    event_type = db.Column(db.Enum(EventType, name="event_type"), nullable=False)
    travel_grant = db.Column(db.Boolean(), nullable=False)
    miniconf_url = db.Column(db.String(100), nullable=True)

    organisation = db.relationship('Organisation', foreign_keys=[organisation_id])
    application_forms = db.relationship('ApplicationForm')
    email_templates = db.relationship('EmailTemplate')
    event_roles = db.relationship('EventRole')
    event_translations = db.relationship('EventTranslation', lazy='dynamic')
    event_fees = db.relationship('EventFee')

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

        self.add_event_translations(names, descriptions)

    def set_miniconf_url(self, new_miniconf_url):
        self.miniconf_url = new_miniconf_url

    def set_start_date(self, new_start_date):
        self.start_date = new_start_date

    def set_end_date(self, new_end_date):
        self.end_date = new_end_date

    def set_application_open(self, new_application_open):
        self.application_open = new_application_open

    def set_application_close(self, new_application_close):
        self.application_close = new_application_close

    def set_review_open(self, new_review_open):
        self.review_open = new_review_open

    def set_review_close(self, new_review_close):
        self.review_close = new_review_close

    def set_selection_open(self, new_selection_open):
        self.selection_open = new_selection_open

    def set_selection_close(self, new_selection_close):
        self.selection_close = new_selection_close

    def set_offer_open(self, new_offer_open):
        self.offer_open = new_offer_open

    def set_offer_close(self, new_offer_close):
        self.offer_close = new_offer_close

    def set_registration_open(self, new_registration_open):
        self.registration_open = new_registration_open

    def set_registration_close(self, new_registration_close):
        self.registration_close = new_registration_close

    def get_application_form(self):
        return self.application_forms[0]

    def has_application_form(self):
        return len(self.application_forms) > 0

    def add_event_role(self, role, user_id):
        event_role = EventRole(role, user_id, self.id)
        self.event_roles.append(event_role)

    def get_name(self, language):
        event_translation = self.event_translations.filter_by(language=language).first()
        if event_translation is not None:
            return event_translation.name
        return None

    def get_description(self, language):
        event_translation = self.event_translations.filter_by(language=language).first()
        if event_translation is not None:
            return event_translation.description
        return None
    
    def get_all_name_translations(self):
        name_translation_map = {}
        for event_translation in self.event_translations.all():
            name_translation_map[event_translation.language] = event_translation.name
        return name_translation_map

    def get_all_description_translations(self):
        description_translation_map = {}
        for event_translation in self.event_translations.all():
            description_translation_map[event_translation.language] = event_translation.description
        return description_translation_map

    def add_event_translations(self, names, descriptions):
        for language in names:
            name = names[language]
            description = descriptions[language]
            event_translation = EventTranslation(name, description, language)
            self.event_translations.append(event_translation)
    
    def add_event_fee(self, name, amount, user_id, description=None):
        event_fee = EventFee(
            name,
            self.organisation.iso_currency_code,
            amount,
            user_id,
            description)
        self.event_fees.append(event_fee)
        return event_fee

    def has_specific_translation(self, language):
        return self.event_translations.filter_by(language=language).count() == 1

    def update(self,
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
               miniconf_url=None):
        self.start_date = start_date
        self.end_date = end_date
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
        self.event_type = event_type
        self.travel_grant = travel_grant
        self.miniconf_url = miniconf_url

        self.event_translations.delete()
        self.add_event_translations(names, descriptions)

    @property
    def is_application_open(self):
        return check_open(self.application_open, self.application_close)

    @property
    def is_application_opening(self):  
        return check_opening(self.application_open)

    @property
    def is_review_open(self):
        return check_open(self.review_open, self.review_close)

    @property
    def is_review_opening(self): 
        return check_opening(self.review_open)

    @property
    def is_selection_open(self):
        return check_open(self.selection_open, self.selection_close)

    @property
    def is_selection_opening(self):
        return check_opening(self.selection_open)

    @property
    def is_offer_open(self):
        return check_open(self.offer_open, self.offer_close)

    @property
    def is_offer_opening(self):
        return check_opening(self.offer_open)

    @property
    def is_registration_open(self):
        return check_open(self.registration_open, self.registration_close)

    @property
    def is_registration_opening(self):
        return check_opening(self.registration_open)

    @property
    def is_event_open(self):
        return check_open(self.start_date, self.end_date)

    @property
    def is_event_opening(self):
        return check_opening(self.start_date)


class EventTranslation(db.Model):

    __tablename__ = "event_translation"
    __table_args__ = tuple([db.UniqueConstraint('event_id', 'language', name='uq_event_id_language')])

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey("event.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    language = db.Column(db.String(2))

    event = db.relationship('Event', foreign_keys=[event_id])

    def __init__(self, name, description, language):
        self.name = name
        self.description = description
        self.language = language

class EventRole(db.Model):

    __tablename__ = "event_role"

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey(
        "event.id"), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey(
        "app_user.id"), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    user = db.relationship('AppUser', foreign_keys=[user_id])
    event = db.relationship('Event', foreign_keys=[event_id])

    def __init__(self, role, user_id, event_id):
        self.role = role
        self.user_id = user_id
        self.event_id = event_id

    def set_user(self, new_user_id):
        self.user_id = new_user_id

    def set_event(self, new_event_id):
        self.event_id = new_event_id

    def set_role(self, new_role):
        self.role = new_role

class EventFee(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=True)
    iso_currency_code = db.Column(db.String(3), nullable=False)
    amount = db.Column(db.Numeric(scale=2), nullable=False)
    is_active = db.Column(db.Boolean(), nullable=False)
    created_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False)
    updated_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=True)
    updated_at = db.Column(db.DateTime(), nullable=True)

    event = db.relationship('Event', foreign_keys=[event_id])
    created_by = db.relationship('AppUser', foreign_keys=[created_by_user_id])
    updated_by = db.relationship('AppUser', foreign_keys=[updated_by_user_id])

    def __init__(
        self,
        name,
        iso_currency_code,
        amount,
        created_by,
        description=None
    ):
        self.name = name
        self.description = description
        self.iso_currency_code = iso_currency_code
        self.amount = round(amount, 2)
        self.created_by_user_id = created_by
        self.is_active = True
        self.created_at = datetime.now()

    def deactivate(self, updated_by_user_id):
        self.is_active = False
        self.updated_at = datetime.now()
        self.updated_by_user_id = updated_by_user_id
