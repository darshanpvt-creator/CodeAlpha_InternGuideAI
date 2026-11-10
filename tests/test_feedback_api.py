import unittest
import uuid

from app import app
from database.db import save_message, get_connection


class TestFeedbackAPI(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.conversation_id = str(uuid.uuid4())

        self.message_id = save_message(
            self.conversation_id,
            "assistant",
            "Explore internship platforms and company career pages."
        )

    def tearDown(self):
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM feedback WHERE conversation_id = ?",
                (self.conversation_id,)
            )
            connection.execute(
                "DELETE FROM messages WHERE conversation_id = ?",
                (self.conversation_id,)
            )
            connection.execute(
                "DELETE FROM conversations WHERE id = ?",
                (self.conversation_id,)
            )

    def test_submit_helpful_feedback(self):
        response = self.client.post(
            "/api/feedback",
            json={
                "conversation_id": self.conversation_id,
                "message_id": self.message_id,
                "rating": "helpful"
            }
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["status"], "success")

    def test_submit_not_helpful_feedback(self):
        response = self.client.post(
            "/api/feedback",
            json={
                "conversation_id": self.conversation_id,
                "message_id": self.message_id,
                "rating": "not_helpful"
            }
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["status"], "success")

    def test_reject_invalid_rating(self):
        response = self.client.post(
            "/api/feedback",
            json={
                "conversation_id": self.conversation_id,
                "message_id": self.message_id,
                "rating": "average"
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_reject_invalid_conversation_id(self):
        response = self.client.post(
            "/api/feedback",
            json={
                "conversation_id": "invalid-id",
                "message_id": self.message_id,
                "rating": "helpful"
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_reject_missing_message_id(self):
        response = self.client.post(
            "/api/feedback",
            json={
                "conversation_id": self.conversation_id,
                "rating": "helpful"
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_reject_user_message_feedback(self):
        user_message_id = save_message(
            self.conversation_id,
            "user",
            "How do I find an internship?"
        )

        response = self.client.post(
            "/api/feedback",
            json={
                "conversation_id": self.conversation_id,
                "message_id": user_message_id,
                "rating": "helpful"
            }
        )

        self.assertEqual(response.status_code, 404)

    def test_reject_message_from_another_conversation(self):
        other_conversation_id = str(uuid.uuid4())

        other_message_id = save_message(
            other_conversation_id,
            "assistant",
            "This message belongs to another conversation."
        )

        try:
            response = self.client.post(
                "/api/feedback",
                json={
                    "conversation_id": self.conversation_id,
                    "message_id": other_message_id,
                    "rating": "helpful"
                }
            )

            self.assertEqual(response.status_code, 404)

        finally:
            with get_connection() as connection:
                connection.execute(
                    "DELETE FROM messages WHERE conversation_id = ?",
                    (other_conversation_id,)
                )
                connection.execute(
                    "DELETE FROM conversations WHERE id = ?",
                    (other_conversation_id,)
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
