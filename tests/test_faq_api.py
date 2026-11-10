import unittest
from unittest import mock
import json
import copy
import os
import tempfile

import app as app_module


class FAQManagementAPITests(unittest.TestCase):

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

        self.original_faqs = copy.deepcopy(app_module.faqs)
        self.original_matcher = app_module.matcher

        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            delete=False
        )

        self.temp_path = temp_file.name

        json.dump(self.original_faqs, temp_file, indent=2)
        temp_file.close()

        self.path_patcher = mock.patch.object(
            app_module,
            "FAQ_PATH",
            self.temp_path
        )
        self.path_patcher.start()

        app_module.faqs = copy.deepcopy(self.original_faqs)
        app_module.matcher = self.original_matcher

        self.valid_faq = {
            "category": "Testing",
            "question": "How can students prepare for technical interviews?",
            "answer": "Practice programming, data structures and problem solving.",
            "variations": [
                "How to prepare for coding interviews?"
            ],
            "tags": [
                "interviews",
                "coding"
            ]
        }

    def tearDown(self):
        app_module.faqs = self.original_faqs
        app_module.matcher = self.original_matcher

        self.path_patcher.stop()

        if os.path.exists(self.temp_path):
            os.remove(self.temp_path)

    def test_add_valid_faq(self):
        response = self.client.post(
            "/api/admin/faqs",
            json=self.valid_faq
        )

        self.assertEqual(response.status_code, 201)

        data = response.get_json()

        self.assertEqual(data["status"], "success")
        self.assertEqual(data["faq"]["question"], self.valid_faq["question"])
        self.assertEqual(data["faq"]["category"], "Testing")

        with open(self.temp_path, "r", encoding="utf-8") as file:
            saved_faqs = json.load(file)

        self.assertTrue(
            any(
                faq["question"] == self.valid_faq["question"]
                for faq in saved_faqs
            )
        )

    def test_reject_missing_required_fields(self):
        invalid_faq = {
            "category": "Testing",
            "question": "A question without an answer"
        }

        response = self.client.post(
            "/api/admin/faqs",
            json=invalid_faq
        )

        self.assertEqual(response.status_code, 400)

    def test_reject_invalid_variations(self):
        invalid_faq = self.valid_faq.copy()
        invalid_faq["variations"] = "This should be a list"

        response = self.client.post(
            "/api/admin/faqs",
            json=invalid_faq
        )

        self.assertEqual(response.status_code, 400)

    def test_reject_invalid_tags(self):
        invalid_faq = self.valid_faq.copy()
        invalid_faq["tags"] = ["valid tag", 123]

        response = self.client.post(
            "/api/admin/faqs",
            json=invalid_faq
        )

        self.assertEqual(response.status_code, 400)

    def test_reject_duplicate_question(self):
        existing_question = self.original_faqs[0]["question"]

        duplicate_faq = self.valid_faq.copy()
        duplicate_faq["question"] = existing_question

        response = self.client.post(
            "/api/admin/faqs",
            json=duplicate_faq
        )

        self.assertEqual(response.status_code, 409)

    def test_reject_non_json_request(self):
        response = self.client.post(
            "/api/admin/faqs",
            data="invalid JSON",
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
