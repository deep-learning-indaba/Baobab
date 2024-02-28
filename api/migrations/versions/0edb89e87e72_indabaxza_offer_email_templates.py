"""Add IndabaX ZA 2023 Custom Offer Email Templates

Revision ID: 0edb89e87e72
Revises: bda5cebe15fd
Create Date: 2023-06-21 18:55:38.123758

"""

# revision identifiers, used by Alembic.
revision = '0edb89e87e72'
down_revision = 'bda5cebe15fd'

from enum import Enum

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from app import db

Base = declarative_base()

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

class EmailTemplate(Base):

    __tablename__ = 'email_template'
    __table_args__ = tuple([db.UniqueConstraint('key', 'event_id', 'language', name='uq_email_template_key_event_id')])

    id = db.Column(db.Integer(), primary_key=True)
    key = db.Column(db.String(50), nullable=False)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=True)
    language = db.Column(db.String(2), nullable=False)
    template = db.Column(db.String(), nullable=False)
    subject = db.Column(db.String(), nullable=False)

    event = db.relationship('Event', foreign_keys=[event_id])

    def __init__(self, key, event_id, subject, template, language):
        self.key = key
        self.event_id = event_id
        self.subject = subject
        self.template = template
        self.language = language


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)
    event = session.query(Event).filter_by(key='indabax2023').first()

    offer_award_content = """Dear {title} {firstname} {lastname},

Congratulations! You've been selected for {event_name}!

In addition, you have been awarded a travel grant to attend the IndabaX!

Congratulations, only the very best have been awarded this. Your travel grant has been made possible by our partners at the event, so give them a personal thanks and chat about future opportunities.
{grants}

The terms and conditions are specified on our website and may be subject to change - https://indabax.co.za/register/travel-grants

Please note that breakfast and lunches are provided but dinner is not, although evening events may have snacks available.

Please follow this link to see details and accept your offer: {host}/indabax2023/offer
You have up until {expiry_date} to accept the offer, otherwise we will automatically allocate your spot to someone else.

If you are unable to accept the offer for any reason, please do let us know by visiting {host}/indabax2023/offer, clicking "Reject" and filling in the reason. 
We will read all of these and if there is anything we can do to accommodate you, we may extend you a new offer in a subsequent round.

If you have any queries, please contact us at {event_email_from}

Kind Regards,
The {event_name} organisers
"""

    offer_content = """Dear {title} {firstname} {lastname},

Congratulations! You've been selected for {event_name}!

Please note that breakfast and lunches are provided but dinner is not, although evening events may have snacks available.

Please follow the link below to see details and accept your offer: {host}/indabax2023/offer
You have up until {expiry_date} to accept the offer, otherwise we will automatically allocate your spot to someone else.

If you are unable to accept the offer for any reason, please do let us know by visiting {host}/indabax2023/offer, clicking "Reject" and filling in the reason. 
We will read all of these and if there is anything we can do to accommodate you, we may extend you a new offer in a subsequent round.

If you have any queries, please contact us at {event_email_from}

Kind Regards,
The {event_name} organisers
"""
    
    offer_grants_template = EmailTemplate('offer-grants', event.id, "{event_name} Application Status Update", offer_award_content, 'en')
    offer_template = EmailTemplate('offer', event.id, "{event_name} Application Status Update", offer_content, 'en')

    session.add_all([offer_grants_template, offer_template])
    session.commit()


def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)
    event = session.query(Event).filter_by(key='indabax2023').first()

    op.execute(f"""DELETE FROM email_template where event_id={event.id} AND language='en' AND key='offer'""")
    op.execute(f"""DELETE FROM email_template where event_id={event.id} AND language='en' AND key='offer-grants'""")

