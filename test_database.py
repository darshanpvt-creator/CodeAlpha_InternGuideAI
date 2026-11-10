import unittest
import uuid

from database.db import init_db, save_message, get_messages


class TestConversationDatabase(unittest.TestCase):

    def setUp(self):
        init_db()
        self.conversation_id = str(uuid.uuid4())

    def test_save_and_retrieve_messages(self):
        save_message(self.conversation_id, "user", "How do I find an internship?")
        save_message(self.conversation_id, "assistant", "Explore internship platforms and company career pages.")

        messages = get_messages(self.conversation_id)

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[1]["role"], "assistant")

    def test_empty_conversation(self):
        messages = get_messages(self.conversation_id)
        self.assertEqual(messages, [])

    def test_invalid_role(self):
        with self.assertRaises(ValueError):
            save_message(self.conversation_id, "admin", "Invalid message")


if __name__ == "__main__":
    unittest.main(verbosity=2)
