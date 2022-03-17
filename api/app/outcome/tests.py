import json
from datetime import datetime, timedelta

from app import LOGGER, db
from app.outcome.models import Outcome, Status
from app.outcome.repository import OutcomeRepository as outcome_repository
from app.utils.testing import ApiTestCase


class OutcomeApiTest(ApiTestCase):
    def seed_static_data(self):
        db.session.expire_on_commit = False

        self.event1 = self.add_event(name={"en": "Event 1"}, key="event1")
        self.event2 = self.add_event(name={"en": "Event 2"}, key="event2")

        self.test_user1 = self.add_user("something@email.com")
        self.test_user2 = self.add_user("something_else@email.com")
        self.event1_admin = self.add_user("event1admin@email.com")
        self.event2_admin = self.add_user("event2admin@email.com")

        self.event1.add_event_role("admin", self.event1_admin.id)
        self.event2.add_event_role("admin", self.event2_admin.id)

        # Add 2 outcomes for event 1 to user 1
        self.event1_user1_outcome1 = Outcome(
            self.event1.id, self.test_user1.id, "WAITLIST", self.event1_admin.id
        )
        self.event1_user1_outcome1.reset_latest()
        self.event1_user1_outcome2 = Outcome(
            self.event1.id, self.test_user1.id, "ACCEPTED", self.event1_admin.id
        )

        # Add 1 outcome for event 1 to user 2
        self.event1_user2_outcome = Outcome(
            self.event1.id, self.test_user2.id, "REJECTED", self.event1_admin.id
        )

        # Add 1 outcome for event 2 to user 1
        self.event2_user1_outcome = Outcome(
            self.event2.id, self.test_user1.id, "WAITLIST", self.event2_admin.id
        )

        db.session.add_all(
            [
                self.event1_user1_outcome1,
                self.event1_user1_outcome2,
                self.event1_user2_outcome,
                self.event2_user1_outcome,
            ]
        )

        db.session.commit()

        self.add_email_template("outcome-rejected")
        self.add_email_template("outcome-waitlist")

        db.session.flush()

        self.event1_user1_outcome1_id = self.event1_user1_outcome1.id
        self.event1_user1_outcome2_id = self.event1_user1_outcome2.id
        self.event1_user2_outcome_id = self.event1_user2_outcome.id
        self.event2_user1_outcome_id = self.event2_user1_outcome.id

        self.test_user1_id = self.test_user1.id

    def test_repository_get_latest_by_user_for_event(self):
        """Test that repository method gets the correct latest outcome for a user."""
        self.seed_static_data()
        result = outcome_repository.get_latest_by_user_for_event(
            self.test_user1.id, self.event1.id
        )
        self.assertEqual(result.id, self.event1_user1_outcome2.id)
        self.assertEqual(result.status, Status.ACCEPTED)

        result = outcome_repository.get_latest_by_user_for_event(
            self.test_user2.id, self.event1.id
        )
        self.assertEqual(result.id, self.event1_user2_outcome.id)
        self.assertEqual(result.status, Status.REJECTED)

    def test_get_all_by_user_for_event(self):
        """Test that repository method gets all outcomes for a user."""
        self.seed_static_data()
        result = outcome_repository.get_all_by_user_for_event(
            self.test_user1.id, self.event1.id
        )
        self.assertEqual(len(result), 2)
        self.assertCountEqual(
            [o.id for o in result],
            [self.event1_user1_outcome1.id, self.event1_user1_outcome2.id],
        )

    def test_get_latest_for_event(self):
        """Test that repository method gets the latest outcomes for an event."""
        self.seed_static_data()
        result = outcome_repository.get_latest_for_event(self.event1.id)
        self.assertEqual(len(result), 2)
        self.assertCountEqual(
            [o.id for o in result],
            [self.event1_user1_outcome2.id, self.event1_user2_outcome.id],
        )

    def test_outcome_get(self):
        """Test usual get case."""
        self.seed_static_data()
        response = self.app.get(
            "/api/v1/outcome",
            data={"event_id": self.event1.id},
            headers=self.get_auth_header_for("something@email.com"),
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["id"], self.event1_user1_outcome2_id)
        self.assertEqual(data["status"], "ACCEPTED")
        self.assertEqual(
            data["timestamp"], self.event1_user1_outcome2.timestamp.isoformat()
        )

    def test_get_with_no_outcome(self):
        """Test get method when there is no outcome."""
        self.seed_static_data()
        response = self.app.get(
            "/api/v1/outcome",
            data={"event_id": self.event2.id},
            headers=self.get_auth_header_for("something_else@email.com"),
        )
        self.assertEqual(response.status_code, 404)

    def test_outcome_post_non_event_admin(self):
        """Test that a forbidden status is given when the logged in user is not an event admin."""
        self.seed_static_data()
        response = self.app.post(
            "/api/v1/outcome",
            data={
                "event_id": self.event1.id,
                "user_id": self.test_user1.id,
                "outcome": "ACCEPTED",
            },
            headers=self.get_auth_header_for("something@email.com"),
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 403)

    def test_post(self):
        """Test typical post flow."""
        self.seed_static_data()
        response = self.app.post(
            "/api/v1/outcome",
            data={
                "event_id": self.event2.id,
                "user_id": self.test_user1.id,
                "outcome": "REJECTED",
            },
            headers=self.get_auth_header_for("event2admin@email.com"),
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 201)

        outcomes = outcome_repository.get_all_by_user_for_event(
            self.test_user1_id, self.event2.id
        )
        outcomes = list(sorted(outcomes, key=lambda o: o.timestamp))
        print(outcomes)

        self.assertEqual(outcomes[0].status, Status.WAITLIST)
        self.assertFalse(outcomes[0].latest)

        self.assertEqual(outcomes[1].status, Status.REJECTED)
        self.assertTrue(outcomes[1].latest)

    def test_outcome_list_get_event_admin(self):
        """Test that outcome list get can only be performed by an event admin."""
        self.seed_static_data()
        response = self.app.get(
            "/api/v1/outcome-list",
            data={"event_id": self.event1.id},
            headers=self.get_auth_header_for("something_else@email.com"),
        )
        self.assertEqual(response.status_code, 403)

    def test_outcome_list_get_correct_event_admin(self):
        """Test that outcome list get can only be performed by the correct event admin."""
        self.seed_static_data()
        response = self.app.get(
            "/api/v1/outcome-list",
            data={"event_id": self.event1.id},
            headers=self.get_auth_header_for("event2admin@email.com"),
        )
        self.assertEqual(response.status_code, 403)

    def test_outcome_list_get(self):
        """Test getting all outcomes for an event."""
        self.seed_static_data()
        response = self.app.get(
            "/api/v1/outcome-list",
            data={"event_id": self.event1.id},
            headers=self.get_auth_header_for("event1admin@email.com"),
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(data), 2)
        self.assertCountEqual(
            [o["user"]["email"] for o in data],
            ["something@email.com", "something_else@email.com"],
        )
