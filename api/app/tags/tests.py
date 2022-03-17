import json

from app import db
from app.tags.models import Tag, TagTranslation
from app.utils.testing import ApiTestCase


class ReviewsApiTest(ApiTestCase):
    def seed_static_data(self):
        self.event1 = self.add_event(key="event1")
        self.event2 = self.add_event(key="event2")
        self.user1 = self.add_user("event1admin@mail.com")
        self.user2 = self.add_user("event2admin@mail.com")
        self.user3 = self.add_user("user@mail.com")

        self.event1.add_event_role("admin", self.user1.id)
        self.event2.add_event_role("admin", self.user2.id)

        db.session.commit()

        self.tags = [Tag(self.event1.id), Tag(self.event1.id), Tag(self.event2.id)]

        db.session.add_all(self.tags)
        db.session.commit()

        tag_translations = [
            TagTranslation(self.tags[0].id, "en", "English Tag 1 Event 1"),
            TagTranslation(self.tags[0].id, "fr", "French Tag 1 Event 1"),
            TagTranslation(self.tags[1].id, "en", "English Tag 2 Event 1"),
            TagTranslation(self.tags[1].id, "fr", "French Tag 2 Event 1"),
            TagTranslation(self.tags[2].id, "en", "English Tag 1 Event 2"),
        ]

        db.session.add_all(tag_translations)
        db.session.commit()

        self.user1_headers = self.get_auth_header_for("event1admin@mail.com")
        self.user2_headers = self.get_auth_header_for("event2admin@mail.com")
        self.user3_headers = self.get_auth_header_for("user@mail.com")

    def test_get_tag(self):
        """Test typical get request."""
        self.seed_static_data()
        params = {"id": 1, "event_id": 1}
        response = self.app.get("/api/v1/tag", headers=self.user1_headers, data=params)
        data = json.loads(response.data)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["event_id"], 1)
        self.assertDictEqual(
            data["name"], {"en": "English Tag 1 Event 1", "fr": "French Tag 1 Event 1"}
        )

    def test_get_event_admin(self):
        """Check a non event admin can't get a tag."""
        self.seed_static_data()
        params = {"id": 1, "event_id": 1}
        response = self.app.get("/api/v1/tag", headers=self.user3_headers, data=params)
        self.assertEqual(response.status_code, 403)

    def test_get_event_admin_correct_event(self):
        """Check that an event admin for a different event can't get a tag."""
        self.seed_static_data()
        params = {"id": 1, "event_id": 1}
        response = self.app.get("/api/v1/tag", headers=self.user2_headers, data=params)
        self.assertEqual(response.status_code, 403)

    def test_typical_post(self):
        """Test a typical post request."""
        self.seed_static_data()
        params = {
            "event_id": 2,
            "name": {
                "en": "English Tag 2 Event 2",
                "fr": "French Tag 2 Event 2",
            },
        }
        response = self.app.post(
            "/api/v1/tag",
            headers=self.user2_headers,
            data=json.dumps(params),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        new_id = data["id"]

        response = self.app.get(
            "/api/v1/tag",
            headers=self.user2_headers,
            data={"id": new_id, "event_id": 2},
        )
        data = json.loads(response.data)

        self.assertEqual(data["id"], new_id)
        self.assertEqual(data["event_id"], 2)
        self.assertDictEqual(
            data["name"], {"en": "English Tag 2 Event 2", "fr": "French Tag 2 Event 2"}
        )

    def test_post_event_admin(self):
        """Test that a non-event admin can't post a new tag."""
        self.seed_static_data()
        params = {
            "event_id": 2,
            "name": {
                "en": "English Tag 2 Event 2",
                "fr": "French Tag 2 Event 2",
            },
        }
        # User 1 is not an event admin for event 2
        response = self.app.post(
            "/api/v1/tag",
            headers=self.user1_headers,
            data=json.dumps(params),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_put(self):
        """Test typcial put request."""
        self.seed_static_data()
        params = {
            "id": 2,
            "event_id": 1,
            "name": {"en": "Renamed English Name", "zu": "Zulu Name"},  # Rename
        }

        response = self.app.put(
            "/api/v1/tag",
            headers=self.user1_headers,
            data=json.dumps(params),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        response = self.app.get(
            "/api/v1/tag", headers=self.user1_headers, data={"id": 2, "event_id": 1}
        )
        data = json.loads(response.data)

        self.assertEqual(data["id"], 2)
        self.assertEqual(data["event_id"], 1)
        self.assertDictEqual(
            data["name"], {"en": "Renamed English Name", "zu": "Zulu Name"}
        )

    def test_tag_list(self):
        """Test that a list of tags can be retrieved in the correct language."""
        self.seed_static_data()
        params = {"event_id": 1, "language": "en"}

        response = self.app.get("/api/v1/tags", headers=self.user1_headers, data=params)
        data = json.loads(response.data)

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["event_id"], 1)
        self.assertEqual(data[0]["name"], "English Tag 1 Event 1")
        self.assertEqual(data[1]["id"], 2)
        self.assertEqual(data[1]["event_id"], 1)
        self.assertEqual(data[1]["name"], "English Tag 2 Event 1")

        params = {"event_id": 1, "language": "fr"}

        response = self.app.get("/api/v1/tags", headers=self.user1_headers, data=params)
        data = json.loads(response.data)

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["event_id"], 1)
        self.assertEqual(data[0]["name"], "French Tag 1 Event 1")
        self.assertEqual(data[1]["id"], 2)
        self.assertEqual(data[1]["event_id"], 1)
        self.assertEqual(data[1]["name"], "French Tag 2 Event 1")

    def test_tag_list_default_language(self):
        """Test that the language defaults to English when not found."""
        self.seed_static_data()
        params = {"event_id": 2, "language": "zu"}

        response = self.app.get("/api/v1/tags", headers=self.user2_headers, data=params)
        data = json.loads(response.data)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 3)
        self.assertEqual(data[0]["event_id"], 2)
        self.assertEqual(data[0]["name"], "English Tag 1 Event 2")
