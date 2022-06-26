# -*- coding: utf-8 -*-

import json
import os
import random
import unicodedata
import unittest
from datetime import datetime, timedelta
from sqlite3 import Connection as SQLite3Connection

import six
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError

from app import LOGGER, app, db
from app.applicationModel.models import (ApplicationForm, Question, QuestionTranslation, Section,
                                         SectionTranslation)
from app.events.models import Event, EventType, EventRole, EventFee
from app.invitedGuest.models import InvitedGuest
from app.invoice.models import Invoice, InvoiceLineItem
from app.organisation.models import Organisation
from app.registration.models import Offer, RegistrationForm
from app.responses.models import Answer, Response, ResponseReviewer, ResponseTag
from app.users.models import AppUser, Country, UserCategory
from app.email_template.models import EmailTemplate
from app.reviews.models import ReviewConfiguration, ReviewForm, ReviewSection, ReviewSectionTranslation, ReviewResponse, ReviewQuestion, ReviewQuestionTranslation, ReviewScore
from app.tags.models import Tag, TagTranslation


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

titles = ('Mr', "Ms", 'Mrs', 'Dr', 'Prof', 'Rev', 'Mx')

def strip_accents(text):
    """
    Strip accents from input.
    Helper function to create 'clean' emails
        see https://stackoverflow.com/a/518232/5209000

    :param text: The input string.
    :type text: String.

    :returns: The processed String.
    :rtype: String.
    """
    text = six.ensure_text(text)
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    return str(text)

class ApiTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(ApiTestCase, self).__init__(*args, **kwargs)
        self.test_users = []
        self.firstnames = []
        self.lastnames = []

    def setUp(self):
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        self.app = app.test_client()
        db.reflect()
        db.drop_all()
        db.create_all()
        LOGGER.setLevel('ERROR')

        # Add dummy metadata
        self.user_category = UserCategory('Postdoc')
        db.session.add(self.user_category)
        self.country = Country('South Africa')
        db.session.add(self.country)

        # Add a dummy organisation
        dummy_org = self.add_organisation(domain='org')
        db.session.flush()
        self.dummy_org_id = dummy_org.id
        self.dummy_org_webhook_secret = dummy_org.stripe_webhook_secret_key

    def _get_names(self):
        """Retrieve a list of names from a text file for testing"""
        if len(self.firstnames):
            return self.firstnames, self.lastnames

        if os.path.exists("/code/api/app/utils/names.txt"):
            with open("/code/api/app/utils/names.txt") as file_with_names:
                names = file_with_names.readlines()
        else:
            # why yes, these are names of African Hollywood actors (according to Wikipedia)
            names = ["Mehcad Brooks", "Malcolm Barrett", "Nick Cannon", "Lamorne Morris", "Neil Brown Jr.",
                     "William Jackson Harper", "Marques Houston", "Jennifer Hudson", "Alicia Keys", "Meghan Markle",
                     "Beyonce Knowles", "Jesse Williams", "Lance Gross", "Hosea Chanchez", "Daveed Diggs",
                     "Damon Wayans Jr.", "Columbus Short", "Terrence Jenkins", "Ron Funches", "Jussie Smollett",
                     "Donald Glover", "Brian Tyree Henry", "Gabourey Sidibe", "Trai Byers", "Robert Ri'chard",
                     "Arjay Smith", "Tessa Thompson", "J.Lee", "Lauren London", "DeVaughn Nixon", "Rob Brown", ]
        for _name in names:
            split_name = _name.strip().split(" ")
            self.firstnames.append(split_name[0])
            lastname = " ".join(split_name[1:]) if len(split_name) > 1 else ""
            self.lastnames.append(lastname)
        return self.firstnames, self.lastnames

    def add_user(self, 
                 email='user@user.com', 
                 firstname='User', 
                 lastname='Lastname', 
                 user_title='Mrs',
                 password='abc',
                 organisation_id=1,
                 is_admin=False,
                 post_create_fn=lambda x: None):
        user = AppUser(email,
                 firstname,
                 lastname,
                 user_title,
                 password,
                 organisation_id,
                 is_admin)
        user.verify()

        post_create_fn(user)

        db.session.add(user)
        db.session.commit()
        self.test_users.append(user)
        return user

    def add_n_users(self, n,
                    password='abcd',
                    organisation_id=1,
                    is_admin=False,
                    post_create_fn=lambda x: None):
        firstnames, lastnames = self._get_names()

        users = []

        for i in range(n):
            title = random.choice(titles)
            firstname = random.choice(firstnames)
            lastname = random.choice(lastnames)
            email = "{firstname}.{lastname}{num}@bestemail.com".format(firstname=firstname,
                                                                       lastname=lastname if lastname != "" else "x",
                                                                       num=len(self.test_users))
            email = strip_accents(email)
            try:
                user = self.add_user(email, firstname, lastname, title, password, organisation_id, is_admin, post_create_fn)
                users.append(user)
            except ProgrammingError as err:
                LOGGER.debug("info not added for user: {} {} {} {}".format(email, firstname, lastname, title))
                db.session.rollback()

        return users

    def add_organisation(self,
        name='My Org',
        system_name='Baobab',
        small_logo='org.png', 
        large_logo='org_big.png',
        icon_logo='org_icon.png',
        domain='com',
        url='www.org.com',
        email_from='contact@org.com',
        system_url='baobab.deeplearningindaba.com',
        privacy_policy='PrivacyPolicy.pdf',
        languages=[{"code": "en", "description": "English"}],
        webhook_secret_key="webhook_secret_key"
    ):
        org = Organisation(name, system_name, small_logo, large_logo, icon_logo, domain, url, email_from, system_url, privacy_policy, languages)
        org.set_currency('usd')
        org.set_stripe_keys("not_secret", "secret_key", webhook_secret_key)
        db.session.add(org)
        db.session.commit()
        return org

    def add_country(self):
        country = Country('South Africa')
        db.session.add(country)
        db.session.commit()
        return country
    
    def add_category(self):
        category = UserCategory('Student')
        db.session.add(category)
        db.session.commit()
        return category

    def add_event(self, 
                 name ={'en': 'Test Event'}, 
                 description = {'en': 'Event Description'}, 
                 start_date = datetime.now() + timedelta(days=30), 
                 end_date = datetime.now() + timedelta(days=60),
                 key = 'INDABA2025',
                 organisation_id = 1, 
                 email_from = 'abx@indaba.deeplearning', 
                 url = 'indaba.deeplearning',
                 application_open = datetime.now(),
                 application_close = datetime.now() + timedelta(days=10),
                 review_open = datetime.now() ,
                 review_close = datetime.now() + timedelta(days=15),
                 selection_open = datetime.now(),
                 selection_close = datetime.now() + timedelta(days=15),
                 offer_open = datetime.now(),
                 offer_close = datetime.now(),
                 registration_open = datetime.now(),
                 registration_close = datetime.now() + timedelta(days=15),
                 event_type = EventType.EVENT,
                 travel_grant = False):

        event = Event(name, description, start_date,  end_date, key,  organisation_id,  email_from,  url, 
                      application_open, application_close, review_open, review_close, selection_open, 
                      selection_close, offer_open,  offer_close, registration_open, registration_close, event_type,
                      travel_grant)
        db.session.add(event)
        db.session.commit()
        return event

    def add_event_role(self, role, user_id, event_id):
        event_role = EventRole(role, user_id, event_id)
        db.session.add(event_role)
        db.session.commit()
        return event_role

    def add_review_config(self, review_form_id=1, num_reviews_required=1, num_optional_reviews=1):
        review_config = ReviewConfiguration(
            review_form_id=review_form_id, 
            num_reviews_required=num_reviews_required, 
            num_optional_reviews=num_optional_reviews)
        db.session.add(review_config)
        db.session.commit()
        return review_config

    def add_review_form(self, application_form_id=1, deadline=None, stage=1, active=True):
        deadline = deadline or datetime.now()
        review_form = ReviewForm(application_form_id, deadline, stage, active)
        db.session.add(review_form)
        db.session.commit()
        return review_form

    def add_review_section(self, review_form_id, order=1):
        review_section = ReviewSection(review_form_id, order=order)
        db.session.add(review_section)
        db.session.commit()

        return review_section

    def add_review_section_translation(self, review_section_id, language, headline='Review Section', description='Review Section Description'):
        translation = ReviewSectionTranslation(review_section_id, language, headline, description)
        db.session.add(translation)
        db.session.commit()

        return translation

    def add_review_question(self, review_section_id, weight=0, type='short-text', question_id=None, order=1):
        review_question = ReviewQuestion(review_section_id, question_id, type=type, is_required=True, order=order, weight=weight)
        db.session.add(review_question)
        db.session.commit()

        return review_question
    
    def add_review_question_translation(
        self,
        review_question_id,
        language,
        description='Review question description',
        headline='Review question headline',
        placeholder=None,
        options=None,
        validation_regex=None,
        validation_text=None):
        review_question_translation = ReviewQuestionTranslation(
            review_question_id,
            language,
            description=description,
            headline=headline,
            placeholder=placeholder,
            options=options,
            validation_regex=validation_regex,
            validation_text=validation_text
        )

        db.session.add(review_question_translation)
        db.session.commit()

        return review_question_translation

    def add_email_template(self, template_key, template='This is an email', language='en', subject='Subject', event_id=None):
        email_template = EmailTemplate(template_key, event_id, subject, template, language)
        db.session.add(email_template)
        db.session.commit()
        return email_template

    def get_auth_header_for(self, email, password='abc'):
        body = {
            'email': email,
            'password': password
        }
        response = self.app.post('api/v1/authenticate', data=body)
        data = json.loads(response.data)
        header = {'Authorization': data['token']}
        return header

    def add_to_db(self, obj):
        db.session.add(obj)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.reflect()
        db.drop_all()

    def create_application_form(self,
                            event_id = 1,
                            is_open = True,
                            nominations = False):
                            
        application_form = ApplicationForm(event_id, is_open, nominations)
        db.session.add(application_form)
        db.session.commit()
        return application_form

    def create_registration_form(self, event_id=1):
        registration_form = RegistrationForm(event_id)
        db.session.add(registration_form)
        db.session.commit()
        return registration_form
    
    def add_section(self, application_form_id, order=1):
        section = Section(application_form_id, order)
        db.session.add(section)
        db.session.commit()
        return section
    
    def add_section_translation(
        self,
        section_id,
        language,
        name='Section Name',
        description='Section Description',
        show_for_values=None):
        section_translation = SectionTranslation(section_id, language, name, description, show_for_values)
        db.session.add(section_translation)
        db.session.commit()
        return section_translation

    def add_question(
        self,
        application_form_id,
        section_id,
        order=1,
        question_type='short-text',
        key=None):
        question = Question(application_form_id, section_id, order, question_type, key=key)
        db.session.add(question)
        db.session.commit()
        return question

    def add_question_translation(self,
        question_id,
        language,
        headline='Question Headline',
        description=None,
        placeholder=None,
        validation_regex=None,
        validation_text=None,
        options=None,
        show_for_values=None):
        question_translation = QuestionTranslation(
            question_id,
            language,
            headline,
            description,
            placeholder,
            validation_regex,
            validation_text,
            options,
            show_for_values)
        db.session.add(question_translation)
        db.session.commit()
        return question_translation
    
    def add_response(self, application_form_id, user_id, is_submitted=False, is_withdrawn=False, language='en'):
        response = Response(application_form_id, user_id, language)
        if is_submitted:
            response.submit()
        if is_withdrawn:
            response.withdraw()

        db.session.add(response)
        db.session.commit()
        return response
    
    def add_response_reviewer(self, response_id, reviewer_user_id):
        rr = ResponseReviewer(response_id, reviewer_user_id)
        db.session.add(rr)
        db.session.commit()
        return rr

    def add_answer(self, response_id, question_id, answer_value):
        answer = Answer(response_id, question_id, answer_value)
        db.session.add(answer)
        db.session.commit()
        return answer

    def add_review_response(self, reviewer_user_id, response_id, review_form_id=1, language='en', is_submitted=False):
        rr = ReviewResponse(review_form_id, reviewer_user_id, response_id, language)
        if is_submitted:
            rr.submit()
        db.session.add(rr)
        db.session.commit()

        return rr

    def add_review_score(self, review_response_id, review_question_id, value):
        rs = ReviewScore(review_question_id, value)
        rs.review_response_id = review_response_id
        db.session.add(rs)
        db.session.commit()
        return rs

    def add_offer(self, user_id, event_id=1, offer_date=None, expiry_date=None, payment_required=False, travel_award=False, accommodation_award=False, candidate_response=None):
        offer_date = offer_date or datetime.now()
        expiry_date = expiry_date or datetime.now() + timedelta(10)

        offer = Offer(
            user_id=user_id, 
            event_id=event_id, 
            offer_date=offer_date, 
            expiry_date=expiry_date,
            payment_required=payment_required,
            travel_award=travel_award,
            accommodation_award=accommodation_award,
            candidate_response=candidate_response)

        db.session.add(offer)
        db.session.commit()
        return offer

    def add_invited_guest(self, user_id, event_id=1, role='Guest'):
        print(('Adding invited guest for user: {}, event: {}, role: {}'.format(user_id, event_id, role)))
        guest = InvitedGuest(event_id, user_id, role)
        db.session.add(guest)
        db.session.commit()
        return guest

    def add_tag(self, event_id=1, names={'en': 'Tag 1 en', 'fr': 'Tag 1 fr'}):
        tag = Tag(event_id)
        db.session.add(tag)
        db.session.commit()
        translations = [
            TagTranslation(tag.id, k, name) for k, name in names.items()
        ]
        db.session.add_all(translations)
        db.session.commit()
        return tag

    def tag_response(self, response_id, tag_id):
        rt = ResponseTag(response_id, tag_id)
        db.session.add(rt)
        db.session.commit()
        return rt
    
    def add_event_fee(
        self,
        event_id,
        created_by_user_id,
        name='Registration fee',
        iso_currency_code='usd',
        amount=200.00,
        description=None
    ):
        event_fee = EventFee(name, iso_currency_code, amount, created_by_user_id, description)
        event_fee.event_id = event_id
        db.session.add(event_fee)
        db.session.commit()
        return event_fee

    def add_invoice(
        self,
        created_by_user_id,
        user_id,
        line_items,
        email='user@user.com',
        iso_currency_code='usd',
    ):
        invoice = Invoice(email, iso_currency_code, line_items, created_by_user_id, str(user_id))
        db.session.add(invoice)
        db.session.commit()
        return invoice

    def get_default_line_items(self):
        return [
            InvoiceLineItem('registration', 'registration desc', 99.99),
            InvoiceLineItem('accommodation', 'accommodation desc', 199.99)
        ]
    
    def add_offer_invoice(self, invoice_id, offer_id):
        invoice = db.session.query(Invoice).get(invoice_id)
        invoice.link_offer(offer_id)
        db.session.commit()
    
    def add_invoice_payment_intent(self, invoice_id, payment_intent="pi_3L7GhOEpDzoopUbL0jGJhE2i"):
        invoice = db.session.query(Invoice).get(invoice_id)
        invoice.add_payment_intent(payment_intent)
        db.session.commit()