import unittest
import uuid

from app import app
from database.db import save_message, get_connection


class TestConversationHistoryAPI(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.conversation_id = str(uuid.uuid4())

        save_message(
            self.conversation_id,
            "user",
            "How can I find an internship?"
        )

        save_message(
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
                "DELETE FROM unanswered_questions WHERE conversation_id = ?",
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

    def test_retrieve_conversation_history(self):
        response = self.client.get(
            f"/api/history/{self.conversation_id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "success")
        self.assertEqual(
            response.json["conversation_id"],
            self.conversation_id
        )
        self.assertEqual(len(response.json["messages"]), 2)
        self.assertEqual(
            response.json["messages"][0]["role"],
            "user"
        )
        self.assertEqual(
            response.json["messages"][1]["role"],
            "assistant"
        )

    def test_invalid_conversation_id(self):
        response = self.client.get("/api/history/invalid-id")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)

    def test_empty_conversation_history(self):
        unknown_id = str(uuid.uuid4())

        response = self.client.get(
            f"/api/history/{unknown_id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["messages"], [])

    def test_conversation_appears_in_recent_list(self):
        response = self.client.get("/api/conversations")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "success")

        conversations = response.json["conversations"]

        matching = [
            item for item in conversations
            if item["id"] == self.conversation_id
        ]

        self.assertEqual(len(matching), 1)
        self.assertEqual(
            matching[0]["title"],
            "How can I find an internship?"
        )
        self.assertEqual(matching[0]["message_count"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
