import unittest
import uuid
import os
from unittest import mock
from unittest.mock import patch

import app as app_module
from database.db import get_connection, save_unanswered_question


class UnansweredQuestionAPITests(unittest.TestCase):

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
        self.conversation_id = str(uuid.uuid4())

    def tearDown(self):
        with get_connection() as connection:
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

    def test_unmatched_question_is_saved(self):
        mocked_result = {
            "matched": False,
            "confidence": 0.12,
            "answer": "I could not find a suitable answer.",
            "category": None,
            "matched_question": None
        }

        with patch.object(
            app_module.matcher,
            "find_answer",
            return_value=mocked_result
        ):
            response = self.client.post(
                "/api/chat",
                json={
                    "question": "How do I apply for an unusual internship?",
                    "conversation_id": self.conversation_id
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["matched"])

        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT question, confidence
                FROM unanswered_questions
                WHERE conversation_id = ?
                """,
                (self.conversation_id,)
            ).fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(
            row["question"],
            "How do I apply for an unusual internship?"
        )
        self.assertAlmostEqual(row["confidence"], 0.12)

    def test_matched_question_is_not_saved_as_unanswered(self):
        mocked_result = {
            "matched": True,
            "confidence": 0.95,
            "answer": "You can apply through the company career page.",
            "category": "Internships",
            "matched_question": "How do I apply for an internship?"
        }

        with patch.object(
            app_module.matcher,
            "find_answer",
            return_value=mocked_result
        ):
            response = self.client.post(
                "/api/chat",
                json={
                    "question": "How do I apply for an internship?",
                    "conversation_id": self.conversation_id
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["matched"])

        with get_connection() as connection:
            count = connection.execute(
                """
                SELECT COUNT(*)
                FROM unanswered_questions
                WHERE conversation_id = ?
                """,
                (self.conversation_id,)
            ).fetchone()[0]

        self.assertEqual(count, 0)

    def test_admin_api_returns_logged_unanswered_questions(self):
        question = "How can I find a specialized AI internship?"
        confidence = 0.18

        save_unanswered_question(
            self.conversation_id,
            question,
            confidence
        )

        response = self.client.get("/api/admin/unanswered")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertGreaterEqual(data["total"], 1)

        matching_questions = [
            item for item in data["questions"]
            if item["question"] == question
            and item["confidence"] == confidence
        ]

        self.assertTrue(matching_questions)


if __name__ == "__main__":
    unittest.main()
