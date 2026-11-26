"""Run with: python -m unittest -v"""
import unittest

from chatbot import get_bot_reply, predict_intent


class ChatbotIntentTests(unittest.TestCase):
    def test_billing_variations(self):
        for message in ("my transaction failed", "I was charged twice", "payment is pending"):
            with self.subTest(message=message):
                intent, confidence = predict_intent(message)
                self.assertEqual(intent, "billing")
                self.assertGreater(confidence, 0.18)
                reply, needs_ticket = get_bot_reply(message)
                self.assertIn("billing", reply.lower())
                self.assertTrue(needs_ticket)

    def test_greeting_does_not_create_ticket(self):
        reply, needs_ticket = get_bot_reply("Good morning")
        self.assertIn("Hello", reply)
        self.assertFalse(needs_ticket)

    def test_order_status_creates_ticket_path(self):
        reply, needs_ticket = get_bot_reply("Where is my package?")
        self.assertTrue(needs_ticket)
        self.assertIn("Orders", reply)

    def test_empty_message_is_safe(self):
        reply, needs_ticket = get_bot_reply("!!!")
        self.assertTrue(needs_ticket)
        self.assertIn("not fully sure", reply)


if __name__ == "__main__":
    unittest.main()
