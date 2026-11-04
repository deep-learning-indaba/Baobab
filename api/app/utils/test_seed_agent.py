from datetime import datetime, timedelta

from app import app, bcrypt, db
from app.events.models import Event, EventRole
from app.forms.models import Form, FormAnswer, FormResponse
from app.invitedGuest.models import InvitedGuest
from app.users.models import AppUser
from app.utils.seed_agent import ACCOUNTS, EVENT_KEY
from app.utils.testing import ApiTestCase


class SeedAgentCommandTest(ApiTestCase):

    def setUp(self):
        super().setUp()
        self.org_id = self.add_organisation(domain='localhost').id
        self.runner = app.test_cli_runner()

    def seed(self, password='seed-pw', *args):
        return self.runner.invoke(args=['seed-agent', *args], env={'BAOBAB_TEST_PASSWORD': password})

    def seeded_event(self):
        return Event.query.filter_by(key=EVENT_KEY).one()

    def counts(self):
        event_id = self.seeded_event().id
        return {
            'users': AppUser.query.filter(AppUser.email.like('claude-%@baobab.test')).count(),
            'forms': Form.query.filter_by(event_id=event_id).count(),
            'responses': FormResponse.query.join(Form, Form.id == FormResponse.form_id)
                                           .filter(Form.event_id == event_id).count(),
            'answers': FormAnswer.query.count(),
            'roles': EventRole.query.filter_by(event_id=event_id).count(),
            'guests': InvitedGuest.query.filter_by(event_id=event_id).count(),
        }

    def test_seeds_accounts_event_and_review_assignment(self):
        result = self.seed()
        self.assertEqual(result.exit_code, 0, result.output)

        event = self.seeded_event()
        self.assertEqual(event.organisation_id, self.org_id)
        self.assertTrue(event.uses_new_forms)
        self.assertLess(event.application_open, datetime.now())
        self.assertGreater(event.application_close, datetime.now())

        users = {role: AppUser.query.filter_by(email=email).one()
                 for role, (email, _, _, _) in ACCOUNTS.items()}
        self.assertTrue(users['admin'].is_admin)
        self.assertFalse(users['user'].is_admin)
        for user in users.values():
            self.assertTrue(user.verified_email)
            self.assertEqual(user.organisation_id, self.org_id)

        roles = {(r.user_id, r.role) for r in EventRole.query.filter_by(event_id=event.id)}
        self.assertEqual(roles, {(users['event-admin'].id, 'admin'), (users['reviewer'].id, 'reviewer')})
        self.assertEqual(InvitedGuest.query.filter_by(event_id=event.id).one().user_id, users['guest'].id)

        app_form = Form.query.filter_by(event_id=event.id, form_type='application').one()
        review_form = Form.query.filter_by(event_id=event.id, form_type='review').one()
        self.assertEqual(review_form.linked_form_id, app_form.id)

        application = FormResponse.query.filter_by(form_id=app_form.id).one()
        self.assertEqual(application.user_id, users['applicant'].id)
        self.assertTrue(application.is_submitted)
        self.assertEqual(len(application.answers), 3)

        assignment = FormResponse.query.filter_by(form_id=review_form.id).one()
        self.assertEqual(assignment.user_id, users['reviewer'].id)
        self.assertEqual(assignment.linked_response_id, application.id)
        self.assertFalse(assignment.is_submitted)

    def test_rerun_refreshes_without_duplicating(self):
        self.assertEqual(self.seed('first-pw').exit_code, 0)
        before = self.counts()

        event = self.seeded_event()
        event.application_close = datetime.now() - timedelta(days=1)
        db.session.commit()

        result = self.seed('second-pw')
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(self.counts(), before)
        self.assertGreater(self.seeded_event().application_close, datetime.now())

        admin = AppUser.query.filter_by(email=ACCOUNTS['admin'][0]).one()
        self.assertTrue(bcrypt.check_password_hash(admin.password, 'second-pw'))

    def test_requires_password(self):
        result = self.runner.invoke(args=['seed-agent'], env={'BAOBAB_TEST_PASSWORD': ''})
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('BAOBAB_TEST_PASSWORD', result.output)
        self.assertIsNone(Event.query.filter_by(key=EVENT_KEY).first())

    def test_unknown_organisation(self):
        result = self.seed('seed-pw', '--org-domain', 'nowhere')
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('nowhere', result.output)
        self.assertIsNone(Event.query.filter_by(key=EVENT_KEY).first())
