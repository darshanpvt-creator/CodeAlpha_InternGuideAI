import unittest
import uuid
import os
from unittest import mock

import app as app_module
from database.db import (
    get_connection,
    save_message,
    save_feedback,
    save_unanswered_question
)


class AnalyticsAPITests(unittest.TestCase):

    def setUp(self):
        self.admin_password_patcher = mock.patch.dict(
            os.environ,
            {"ADMIN_PASSWORD": "test-admin-password"}
        )
        self.admin_password_patcher.start()
        self.addCleanup(self.admin_password_patcher.stop)

        app_module.app.config["SECRET_KEY"] = "test-secret-key"
        app_module.app.config["TESTING"] = True

        self.client = app_module.app.test_client()

        login_response = self.client.post(
            "/admin/login",
            data={"password": "test-admin-password"}
        )
        self.assertEqual(login_response.status_code, 302)

        self.conversation_ids = [
            str(uuid.uuid4()),
            str(uuid.uuid4())
        ]

        self.unique_question = (
            "Analytics test question " + str(uuid.uuid4())
        )

        # Capture existing statistics before adding test records.
        response = self.client.get("/api/admin/stats")
        self.assertEqual(response.status_code, 200)
        self.baseline = response.get_json()

        # Create two conversations with the same user question.
        assistant_message_ids = []

        for conversation_id in self.conversation_ids:
            save_message(
                conversation_id,
                "user",
                self.unique_question
            )

            assistant_id = save_message(
                conversation_id,
                "assistant",
                "Test assistant response."
            )

            assistant_message_ids.append(assistant_id)

        # Add one helpful and one not-helpful feedback record.
        save_feedback(
            self.conversation_ids[0],
            assistant_message_ids[0],
            "helpful"
        )

        save_feedback(
            self.conversation_ids[1],
            assistant_message_ids[1],
            "not_helpful"
        )

        # Add one unanswered question.
        save_unanswered_question(
            self.conversation_ids[0],
            "Unanswered analytics test question",
            0.15
        )

    def tearDown(self):
        with get_connection() as connection:
            for conversation_id in self.conversation_ids:
                connection.execute(
                    "DELETE FROM feedback WHERE conversation_id = ?",
                    (conversation_id,)
                )
                connection.execute(
                    "DELETE FROM unanswered_questions WHERE conversation_id = ?",
                    (conversation_id,)
                )
                connection.execute(
                    "DELETE FROM messages WHERE conversation_id = ?",
                    (conversation_id,)
                )
                connection.execute(
                    "DELETE FROM conversations WHERE id = ?",
                    (conversation_id,)
                )

    def test_analytics_returns_correct_statistics(self):
        response = self.client.get("/api/admin/stats")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(
            data["total_conversations"],
            self.baseline["total_conversations"] + 2
        )

        self.assertEqual(
            data["total_messages"],
            self.baseline["total_messages"] + 4
        )

        self.assertEqual(
            data["total_unanswered"],
            self.baseline["total_unanswered"] + 1
        )

        self.assertEqual(
            data["feedback"]["helpful"],
            self.baseline["feedback"]["helpful"] + 1
        )

        self.assertEqual(
            data["feedback"]["not_helpful"],
            self.baseline["feedback"]["not_helpful"] + 1
        )

        total_feedback = (
            data["feedback"]["helpful"]
            + data["feedback"]["not_helpful"]
        )

        expected_rate = round(
            data["feedback"]["helpful"] / total_feedback * 100,
            2
        )

        self.assertEqual(data["helpful_rate"], expected_rate)

        self.assertLessEqual(len(data["top_questions"]), 5)

        frequencies = [
            item["frequency"] for item in data["top_questions"]
        ]

        self.assertEqual(frequencies, sorted(frequencies, reverse=True))

        for item in data["top_questions"]:
            self.assertIn("question", item)
            self.assertIn("frequency", item)
            self.assertGreater(item["frequency"], 0)

        with get_connection() as connection:
            count = connection.execute(
                """
                SELECT COUNT(*)
                FROM messages
                WHERE conversation_id IN (?, ?)
                AND role = 'user'
                AND content = ?
                """,
                (
                    self.conversation_ids[0],
                    self.conversation_ids[1],
                    self.unique_question
                )
            ).fetchone()[0]

        self.assertEqual(count, 2)

    def test_analytics_response_contains_all_required_fields(self):
        response = self.client.get("/api/admin/stats")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        required_fields = [
            "total_conversations",
            "total_messages",
            "total_unanswered",
            "feedback",
            "helpful_rate",
            "top_questions"
        ]

        for field in required_fields:
            self.assertIn(field, data)

        self.assertIn("helpful", data["feedback"])
        self.assertIn("not_helpful", data["feedback"])
        self.assertIsInstance(data["top_questions"], list)


if __name__ == "__main__":
    unittest.main()

