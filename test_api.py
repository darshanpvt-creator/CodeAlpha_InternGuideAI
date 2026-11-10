import unittest

from app import app


class TestChatbotAPI(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "success")

    def test_chat(self):
        response = self.client.post(
            "/api/chat",
            json={"question": "How can I find an internship?"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["matched"])
        self.assertIn("answer", response.json)

    def test_empty_question(self):
        response = self.client.post(
            "/api/chat",
            json={"question": ""}
        )

        self.assertEqual(response.status_code, 400)

    def test_unrelated_question(self):
        response = self.client.post(
            "/api/chat",
            json={"question": "What is the weather today?"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json["matched"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
