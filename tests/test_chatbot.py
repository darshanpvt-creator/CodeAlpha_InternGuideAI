
import json
import unittest

from chatbot.matcher import FAQMatcher


class TestFAQMatcher(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open("data/faqs.json", encoding="utf-8") as file:
            faqs = json.load(file)

        cls.matcher = FAQMatcher(faqs)

    def test_internship_question(self):
        result = self.matcher.find_answer(
            "Where can I get practical work experience?"
        )
        self.assertTrue(result["matched"])

    def test_resume_question(self):
        result = self.matcher.find_answer(
            "What details should my CV contain?"
        )
        self.assertTrue(result["matched"])

    def test_skills_question(self):
        result = self.matcher.find_answer(
            "Which programming languages are useful?"
        )
        self.assertTrue(result["matched"])

    def test_unrelated_question(self):
        result = self.matcher.find_answer(
            "What is the weather today?"
        )
        self.assertFalse(result["matched"])

    def test_empty_question(self):
        result = self.matcher.find_answer("")
        self.assertFalse(result["matched"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
