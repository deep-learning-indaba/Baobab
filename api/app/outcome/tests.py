import json
from datetime import datetime, timedelta
from app import db, LOGGER

from app.utils.testing import ApiTestCase
from app.outcome.models import Outcome, Status
from app.outcome.repository import OutcomeRepository as outcome_repository

class OutcomeApiTest(ApiTestCase):
    def setUp(self):
        super(OutcomeApiTest, self).setUp()

        self.event1 = self.add_event(name='Event 1', key='event1')
        self.event2 = self.add_event(name='Event 2', key='event2')

        self.test_user1 = self.add_user('something@email.com')
        self.test_user2 = self.add_user('something_else@email.com')
        self.event1_admin = self.add_user('event1admin@email.com')
        self.event2_admin = self.add_user('event2admin@email.com')

        self.event1.add_event_role('event_admin', self.event1_admin.id)
        self.event2.add_event_role('event_admin', self.event2_admin.id)

        # Add 2 outcomes for event 1 to user 1
        self.event1_user1_outcome1 = Outcome(self.event1.id, self.test_user1.id, 'WAITLIST', self.event1_admin.id)
        self.event1_user1_outcome1.reset_latest()
        self.event1_user1_outcome2 = Outcome(self.event1.id, self.test_user1.id, 'ACCEPTED', self.event1_admin.id)

        # Add 1 outcome for event 1 to user 2
        self.event1_user2_outcome = Outcome(self.event1.id, self.test_user2.id, 'REJECTED', self.event1_admin.id)

        # Add 1 outcome for event 2 to user 1
        self.event2_user1_outcome = Outcome(self.event2.id, self.test_user1.id, 'WAITLIST', self.event2_admin.id)

        db.session.add_all([
            self.event1_user1_outcome1,
            self.event1_user1_outcome2,
            self.event1_user2_outcome,
            self.event2_user1_outcome
        ])
        db.session.commit()
        db.session.flush()

    def test_repository_get_latest_by_user_for_event(self):
        result = outcome_repository.get_latest_by_user_for_event(self.test_user1.id, self.event1.id)
        self.assertEqual(result.id, self.event1_user1_outcome2.id)
        self.assertEqual(result.status, Status.ACCEPTED)

        result = outcome_repository.get_latest_by_user_for_event(self.test_user2.id, self.event1.id)
        self.assertEqual(result.id, self.event1_user2_outcome.id)
        self.assertEqual(result.status, Status.REJECTED)

    def test_get_all_by_user_for_event(self):
        result = outcome_repository.get_all_by_user_for_event(self.test_user1.id, self.event1.id)
        self.assertEqual(len(result), 2)
        self.assertItemsEqual([o.id for o in result], [self.event1_user1_outcome1.id, self.event1_user1_outcome2.id])
    
    def test_get_latest_for_event(self):
        result = outcome_repository.get_latest_for_event(self.event1.id)
        self.assertEqual(len(result), 2)
        self.assertItemsEqual([o.id for o in result], [self.event1_user1_outcome2.id, self.event1_user2_outcome.id])





