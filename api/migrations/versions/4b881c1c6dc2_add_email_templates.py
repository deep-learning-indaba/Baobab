"""Add email templates

Revision ID: 4b881c1c6dc2
Revises: fc82c8e54fd7
Create Date: 2020-08-09 16:06:36.372783

"""

# revision identifiers, used by Alembic.
revision = "4b881c1c6dc2"
down_revision = "fc82c8e54fd7"

import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

from app import db

Base = declarative_base()


class EmailTemplate(Base):

    __tablename__ = "email_template"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    key = db.Column(db.String(50), nullable=False)
    event_id = db.Column(db.Integer(), nullable=True)
    language = db.Column(db.String(2), nullable=False)
    template = db.Column(db.String(), nullable=False)
    subject = db.Column(db.String(), nullable=False)

    def __init__(self, key, event_id, subject, template, language):
        self.key = key
        self.event_id = event_id
        self.subject = subject
        self.template = template
        self.language = language


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    op.execute(
        """SELECT setval('email_template_id_seq', (SELECT max(id) FROM email_template));"""
    )

    template = """Dear {title} {firstname} {lastname},
    
Unfortunately, your application to {event_name} was unsuccessful. 
Please try again next year!
    
Best wishes,
{event_name} Organisers"""
    session.add(
        EmailTemplate(
            "outcome-rejected",
            None,
            "{event_name} Application Status Update",
            template,
            "en",
        )
    )

    template = """Dear {title} {firstname} {lastname},
    
This email serves to inform you that you are now on the waiting list for {event_name}. 
We will contact you should a place become available. 
    
Kind Regards,
{event_name} Organisers"""
    session.add(
        EmailTemplate(
            "outcome-waitlist",
            None,
            "{event_name} Application Status Update",
            template,
            "en",
        )
    )

    template = """Dear {title} {firstname} {lastname},

Welcome to the {event_name}! We're so excited that you made it.

If you have any questions or issues, please chat to one of the organisers.

Kind Regards,
The {event_name} Team
"""

    session.add(
        EmailTemplate(
            "attendance-confirmation", None, "Welcome to {event_name}!", template, "en"
        )
    )

    template = """Dear {title} {firstname} {lastname},

Thank you for completing your guest registration. Please find a copy of your answers below for future reference.


{summary}

Kind Regards,
The {event_name} Team
"""

    session.add(
        EmailTemplate(
            "guest-registration-confirmation",
            None,
            "{event_name} Registration Confirmation",
            template,
            "en",
        )
    )

    template = """Dear {title} {firstname} {lastname},

Kindly find your official invitation letter to {event_name} attached.

Kind Regards,
The {event_name} Team
"""

    session.add(
        EmailTemplate(
            "invitation-letter",
            None,
            "Invitation Letter to {event_name}",
            template,
            "en",
        )
    )

    template = """Dear {title} {firstname} {lastname},

We are pleased to invite you to attend {event_name} as a {role}. 

Please reply to this email should you have any questions or concerns.  

Kind Regards,
The {event_name} Organisers"""
    session.add(
        EmailTemplate(
            "guest-invitation", None, "Your invitation to {event_name}", template, "en"
        )
    )

    template = """Dear {title} {firstname} {lastname},

We are pleased to invite you to attend {event_name} as a {role}. 
To assist with our planning process, please complete our guest registration form in {system_name}, by visiting {host}/{event_key}/registration

Please reply to this email should you have any questions or concerns.  

Kind Regards,
The {event_name} Organisers"""
    session.add(
        EmailTemplate(
            "guest-invitation-with-registration",
            None,
            "Your invitation to {event_name}",
            template,
            "en",
        )
    )

    template = """Dear {title} {firstname} {lastname},

We are pleased to invite you to attend {event_name} as a {role}. 
Please follow these instructions to gain access to our event management system, {system_name}:

1. Visit {host}/resetPassword?resetToken={reset_code} to set your account password.
2. Log in using your email address (the one you received this email on!) and new password.
3. Update your details in {host}/profile

Please reply to this email should you have any questions or concerns. 

Kind Regards,
The {event_name} Organisers
"""
    session.add(
        EmailTemplate(
            "new-guest-no-registration",
            None,
            "Your invitation to {event_name}",
            template,
            "en",
        )
    )

    template = """Dear {title} {firstname} {lastname},

We are pleased to invite you to attend {event_name} as a {role}. 
Please follow these instructions to gain access to our event management system, {system_name}:

1. Visit {host}/resetPassword?resetToken={reset_code} to set your account password.
2. Log in using your email address (the one you received this email on!) and new password.
3. Visit {host}/{event_key}/registration to complete the registration form.
4. Update your details in {host}/profile

Please reply to this email should you have any questions or concerns. 

Kind Regards,
The {event_name} Organisers
"""
    session.add(
        EmailTemplate(
            "new-guest-registration",
            None,
            "Your invitation to {event_name}",
            template,
            "en",
        )
    )

    template = """Dear {title} {firstname} {lastname},

{candidate} has nominated themselves for the {event_name} ({event_url}). 
In order for their application to be considered for the award, we require a reference letter from someone who knows {candidate_firstname} in a professional capacity, and they have selected you. 
Please use the upload link below to submit your reference letter for {candidate_firstname} by {application_close_date}. 
The reference letter should describe your relationship to {candidate_firstname}, how long you've known them, and should comment on the work {candidate_firstname} has done, and its worthiness of the {event_name}. 
Their application will NOT be considered if this reference letter is not submitted by the deadline

Please visit {link} to upload your reference by {application_close_date}

Kind regards,
The {event_name} team.
"""
    session.add(
        EmailTemplate(
            "reference-request-self-nomination",
            None,
            "Reference Request for {event_name}",
            template,
            "en",
        )
    )

    template = """Dear {title} {firstname} {lastname},

{candidate} has been nominated by {nominator} for the {event_name} ({event_url}). 
In order for their application to be considered for the award, we require a reference letter from someone who knows {candidate_firstname} in a professional capacity, and they have selected you. 
Please use the upload link below to submit your reference letter for {candidate_firstname} by {application_close_date}. 
The reference letter should describe your relationship to {candidate_firstname}, how long you've known them, and should comment on the work {candidate_firstname} has done, and its worthiness of the {event_name}. 
Their application will NOT be considered if this reference letter is not submitted by the deadline

Please visit {link} to upload your reference by {application_close_date}

Kind regards,
The {event_name} team.
"""
    session.add(
        EmailTemplate(
            "reference-request",
            None,
            "Reference Request for {event_name}",
            template,
            "en",
        )
    )

    template = """Dear {title} {firstname} {lastname},

Congratulations! You've been selected for {event_name}!

Please follow the link below to see details and accept your offer: {host}/offer
You have up until {expiry_date} to accept the offer, otherwise we will automatically allocate your spot to someone else.

If you are unable to accept the offer for any reason, please do let us know by visiting {host}/offer, clicking "Reject" and filling in the reason. 
We will read all of these and if there is anything we can do to accommodate you, we may extend you a new offer in a subsequent round.

If you have any queries, please contact us at {event_email_from}

Kind Regards,
The {event_name} organisers
"""
    session.add(
        EmailTemplate(
            "offer", None, "{event_name} Application Status Update", template, "en"
        )
    )

    template = """Dear {title} {firstname} {lastname},

Thank you for completing our registration form.
Please note that your spot is pending confirmation on receipt of payment. You will receive correspondence with payment instructions in the next few days.

Here is a copy of your responses:
{summary}

Kind Regards,
The {event_name} Organisers
"""
    session.add(
        EmailTemplate(
            "registration-pending-confirmation",
            None,
            "{event_name} Registration",
            template,
            "en",
        )
    )

    template = """Dear {title} {firstname} {lastname},

Thank you for completing our registration form.
Your spot is now confirmed and we look forward to welcoming you at the event!

Here is a copy of your responses:
{summary}

Kind Regards,
The {event_name} Organisers
"""
    session.add(
        EmailTemplate(
            "registration-with-confirmation",
            None,
            "{event_name} Registration",
            template,
            "en",
        )
    )

    template = """Dear {title} {firstname} {lastname},
    
Your registration to {event_name} has been confirmed! This means that all required payment has been completed. 

We look forward to seeing you at the event!

Kind Regards,
The {event_name} Organisers
"""
    session.add(
        EmailTemplate(
            "registration-confirmed",
            None,
            "{event_name} Registration Confirmation",
            template,
            "en",
        )
    )

    template = """Dear {title} {firstname} {lastname},

You have been assigned {num_reviews} reviews on {system_name}. Please visit {baobab_host}/{event_key}/review to begin.
Note that if you were already logged in to {system_name}, you will need to log out and log in again to pick up the changes to your profile. 

Thank you for assisting us review applications for {event_name}!

Kind Regards,
The {event_name} Organisers
"""
    session.add(
        EmailTemplate(
            "reviews-assigned",
            None,
            "You have been assigned reviews for {event_name}",
            template,
            "en",
        )
    )

    template = """
Dear {title} {firstname} {lastname},

Thank you for creating a new {system} account. Please use the following link to verify your email address:

{host}/verifyEmail?token={token}

Kind Regards,
{organisation}
"""
    session.add(
        EmailTemplate(
            "verify-email", None, "{system} Email Verficiation", template, "en"
        )
    )

    template = """Dear {title} {firstname} {lastname},

You recently requested a password reset on {system}, please use the following link to reset you password:
{host}/resetPassword?resetToken={token}

If you did not request a password reset, please ignore this email and contact {organisation}.

Kind Regards,
{organisation}
"""
    session.add(
        EmailTemplate("password-reset", None, "{system} Password Reset", template, "en")
    )

    session.commit()


def downgrade():
    added_keys = [
        "outcome-rejected",
        "outcome-waitlist",
        "attendance-confirmation",
        "guest-registration-confirmation",
        "invitation-letter",
        "guest-invitation",
        "guest-invitation-with-registration",
        "new-guest-no-registration",
        "new-guest-registration",
        "reference-request-self-nomination",
        "reference-request",
        "offer",
        "registration-pending-confirmation",
        "registration-with-confirmation",
        "registration-confirmed",
        "reviews-assigned",
        "verify-email",
        "password-reset",
    ]
    op.execute(
        """DELETE FROM email_template WHERE key in ({})""".format(
            ", ".join(["'" + k + "'" for k in added_keys])
        )
    )
    op.execute(
        """SELECT setval('email_template_id_seq', (SELECT max(id) FROM email_template));"""
    )
