"""`flask seed-agent`: test accounts and an always-open event for browser verification.

Creates (or refreshes) one event in the organisation served at `localhost`, with
an application form, a linked review form, and one account per role the
verification scenarios need. Every account gets the password in
BAOBAB_TEST_PASSWORD. Safe to run repeatedly: existing rows are updated in
place, and the event dates are re-anchored to today so it never goes stale.
"""
import os
from datetime import datetime, timedelta

import click

from app import app, db
from app.events.models import Event, EventRole, EventType
from app.forms.models import (Form, FormAnswer, FormQuestion, FormQuestionTranslation,
                              FormResponse, FormSection, FormSectionTranslation,
                              FormTranslation)
from app.invitedGuest.models import InvitedGuest
from app.organisation.models import Organisation
from app.users.models import AppUser

EVENT_KEY = 'agent-test'

# role key -> (email, first name, last name, site admin)
ACCOUNTS = {
    'admin': ('claude-admin@baobab.test', 'Claude', 'Admin', True),
    'user': ('claude-user@baobab.test', 'Claude', 'User', False),
    'event-admin': ('claude-event-admin@baobab.test', 'Claude', 'EventAdmin', False),
    'reviewer': ('claude-reviewer@baobab.test', 'Claude', 'Reviewer', False),
    'applicant': ('claude-applicant@baobab.test', 'Claude', 'Applicant', False),
    'guest': ('claude-guest@baobab.test', 'Claude', 'Guest', False),
}

APPLICATION_QUESTIONS = [
    # key, type, en headline, fr headline, options, applicant's answer
    ('institution', 'short-text', 'Institution', 'Institution', None, 'University of Cape Town'),
    ('motivation', 'long-text', 'Why do you want to attend?', 'Pourquoi voulez-vous participer ?',
     None, 'I want to learn about machine learning research and meet the community.'),
    ('career_stage', 'multi-choice', 'Career stage', 'Étape de carrière',
     {'en': [{'value': 'undergrad', 'label': 'Undergraduate'},
             {'value': 'postgrad', 'label': 'Postgraduate'},
             {'value': 'professional', 'label': 'Professional'}],
      'fr': [{'value': 'undergrad', 'label': 'Premier cycle'},
             {'value': 'postgrad', 'label': 'Deuxième cycle'},
             {'value': 'professional', 'label': 'Professionnel'}]},
     'postgrad'),
]

REVIEW_QUESTIONS = [
    ('score', 'numeric', 'Overall score (1-5)', 'Note globale (1-5)', None, {'weight': 1}),
    ('comments', 'long-text', 'Comments', 'Commentaires', None, None),
]


def _user(org_id, role, password):
    email, first, last, is_admin = ACCOUNTS[role]
    user = AppUser.query.filter_by(email=email, organisation_id=org_id).first()
    if user is None:
        user = AppUser(email, first, last, None, password, org_id, is_admin=is_admin)
        db.session.add(user)
    else:
        user.set_password(password)
        user.is_admin = is_admin
        user.active = True
        user.is_deleted = False
    user.verify()
    db.session.flush()
    return user


def _event(org_id):
    now = datetime.now()
    dates = dict(
        start_date=now + timedelta(days=60),
        end_date=now + timedelta(days=65),
        application_open=now - timedelta(days=7),
        application_close=now + timedelta(days=30),
        review_open=now - timedelta(days=7),
        review_close=now + timedelta(days=45),
        selection_open=now - timedelta(days=7),
        selection_close=now + timedelta(days=45),
        offer_open=now - timedelta(days=7),
        offer_close=now + timedelta(days=50),
        registration_open=now - timedelta(days=7),
        registration_close=now + timedelta(days=55),
    )
    event = Event.query.filter_by(key=EVENT_KEY).first()
    if event is None:
        event = Event(
            {'en': 'Agent Test Event', 'fr': "Événement de test de l'agent"},
            {'en': 'Seeded event for automated browser verification.',
             'fr': 'Événement créé pour la vérification automatisée dans le navigateur.'},
            key=EVENT_KEY, organisation_id=org_id, email_from='noreply@baobab.test',
            url='https://baobab.test', event_type=EventType.EVENT, travel_grant=False,
            languages=['en', 'fr'], uses_new_forms=True, **dates)
        db.session.add(event)
    else:
        for field, value in dates.items():
            setattr(event, field, value)
    db.session.flush()
    return event


def _translated(form_id, name_en, name_fr):
    for language, name in (('en', name_en), ('fr', name_fr)):
        db.session.add(FormTranslation(form_id, language, name))


def _questions(form, section_key, section_en, section_fr, questions):
    section = FormSection(form.id, 1, key=section_key)
    db.session.add(section)
    db.session.flush()
    db.session.add(FormSectionTranslation(section.id, 'en', section_en))
    db.session.add(FormSectionTranslation(section.id, 'fr', section_fr))

    by_key = {}
    for order, (key, qtype, en, fr, options, settings) in enumerate(questions, start=1):
        question = FormQuestion(form.id, section.id, order, qtype, key=key, settings=settings)
        db.session.add(question)
        db.session.flush()
        for language, headline in (('en', en), ('fr', fr)):
            db.session.add(FormQuestionTranslation(
                question.id, language, headline,
                options=options[language] if options else None))
        by_key[key] = question
    return by_key


def _forms(event, created_by):
    """Create the application and review forms on first run; leave them alone after."""
    app_form = Form.query.filter_by(event_id=event.id, form_type='application').first()
    if app_form is not None:
        review_form = Form.query.filter_by(event_id=event.id, form_type='review', stage=1).first()
        questions = {q.key: q for q in app_form.questions}
        return app_form, review_form, questions

    app_form = Form(event.id, created_by.id, form_type='application')
    db.session.add(app_form)
    db.session.flush()
    _translated(app_form.id, 'Application', 'Candidature')
    questions = _questions(
        app_form, 'about-you', 'About you', 'À propos de vous',
        [(key, qtype, en, fr, options, None) for key, qtype, en, fr, options, _ in APPLICATION_QUESTIONS])

    review_form = Form(event.id, created_by.id, form_type='review', stage=1,
                       multiple_responses=True, linked_form_id=app_form.id,
                       settings={'num_reviews_required': 1})
    db.session.add(review_form)
    db.session.flush()
    _translated(review_form.id, 'Review', 'Évaluation')
    _questions(review_form, 'review', 'Review', 'Évaluation', REVIEW_QUESTIONS)
    return app_form, review_form, questions


def _role(event, user, role):
    if not EventRole.query.filter_by(event_id=event.id, user_id=user.id, role=role).first():
        db.session.add(EventRole(role, user.id, event.id))


def _submitted_application(app_form, applicant, questions):
    response = FormResponse.query.filter_by(form_id=app_form.id, user_id=applicant.id).first()
    if response is None:
        response = FormResponse(app_form.id, applicant.id)
        db.session.add(response)
        db.session.flush()
        for key, _, _, _, _, answer in APPLICATION_QUESTIONS:
            db.session.add(FormAnswer(response.id, questions[key].id, answer))
    response.is_submitted = True
    response.submitted_timestamp = response.submitted_timestamp or datetime.now()
    response.is_withdrawn = False
    return response


def _review_assignment(review_form, reviewer, application):
    # An assignment is an empty review-form response linked to the application;
    # see FormReviewAssignmentAPI.
    if not FormResponse.query.filter_by(form_id=review_form.id, user_id=reviewer.id,
                                        linked_response_id=application.id).first():
        db.session.add(FormResponse(review_form.id, reviewer.id, linked_response_id=application.id))


@app.cli.command('seed-agent')
@click.option('--org-domain', default='localhost', show_default=True,
              help='Domain of the organisation to seed (the dev site is served as localhost).')
def seed_agent(org_domain):
    """Create or refresh the agent test accounts and Agent Test Event."""
    password = os.environ.get('BAOBAB_TEST_PASSWORD')
    if not password:
        raise click.ClickException('Set BAOBAB_TEST_PASSWORD to the password for the seeded accounts.')

    org = Organisation.query.filter_by(domain=org_domain).first()
    if org is None:
        raise click.ClickException('No organisation with domain {!r}. Run `flask db upgrade` first.'.format(org_domain))

    users = {role: _user(org.id, role, password) for role in ACCOUNTS}
    event = _event(org.id)
    app_form, review_form, questions = _forms(event, users['event-admin'])

    _role(event, users['event-admin'], 'admin')
    _role(event, users['reviewer'], 'reviewer')
    if not InvitedGuest.query.filter_by(event_id=event.id, user_id=users['guest'].id).first():
        db.session.add(InvitedGuest(event.id, users['guest'].id, 'Guest'))

    application = _submitted_application(app_form, users['applicant'], questions)
    db.session.flush()
    _review_assignment(review_form, users['reviewer'], application)

    db.session.commit()

    click.echo('Seeded event {!r} (id {}) in organisation {!r}.'.format(EVENT_KEY, event.id, org.name))
    for role, (email, _, _, _) in ACCOUNTS.items():
        click.echo('  {:<12} {}'.format(role, email))
