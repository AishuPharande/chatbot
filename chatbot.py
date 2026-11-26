"""Lightweight NLP intent classifier for the customer support chatbot."""
from __future__ import annotations

import re
from typing import Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

INTENT_EXAMPLES = {
    "greeting": ["hello", "hi there", "hey", "good morning", "good afternoon", "good evening", "hello support team", "is anyone there", "hi chatbot", "hey can you help me"],
    "hours": ["what are your working hours", "when is support open", "are you open today", "what time do you close", "tell me your business hours", "when can I contact support", "support opening time", "are you available on weekends", "what time does the office open", "when does customer service close"],
    "password": ["I forgot my password", "how can I reset my password", "I cannot log in", "help me change my password", "password reset is not working", "I lost access to my account", "I cannot sign in", "how do I recover my account", "my login credentials are not working", "I need to update my password"],
    "refund": ["I want a refund", "how can I return this product", "please give my money back", "I want to cancel and get a refund", "when will my refund arrive", "my refund is delayed", "the product is damaged and I want to return it", "how do returns work", "refund status please", "I am not satisfied and want a refund"],
    "billing": ["my payment failed", "I have a billing problem", "I was charged twice", "money was deducted but order failed", "my transaction did not go through", "there is an incorrect charge", "I need help with an invoice", "payment is pending", "I was billed incorrectly", "my card payment was declined", "why did you take money from my account", "I paid but it still says unpaid"],
    "order_status": ["where is my order", "track my order", "what is my delivery status", "my package has not arrived", "when will my order be delivered", "my shipment is delayed", "I need an order update", "where can I see tracking details", "delivery status is not updating", "my parcel is missing", "when can I expect delivery", "track my shipment"],
    "human_agent": ["I want to talk to a human", "connect me to an agent", "can I speak to a person", "I need a support representative", "please contact customer service", "get me a real person", "I want to speak with support", "transfer me to an employee", "human help please", "I need someone to call me"],
    "thanks": ["thank you", "thanks a lot", "that helped", "thanks for your help", "great thank you", "I appreciate it", "many thanks", "thank you so much", "that is helpful", "perfect thanks"],
    "goodbye": ["bye", "goodbye", "see you later", "have a good day", "that is all bye", "talk to you later", "I am done thanks bye", "catch you later", "good night goodbye", "exit chat"],
}

RESPONSES = {
    "greeting": ("Hello! Welcome to customer support. How can I help you today?", False),
    "hours": ("Our sample support hours are Monday to Friday, 9:00 AM to 6:00 PM. Please update this policy for your organization.", False),
    "password": ("For account security, use the password-reset option on the sign-in page. If it does not work, I can help raise a support ticket.", False),
    "refund": ("Refund eligibility depends on the product and purchase date. Share relevant order details, but never send card numbers, passwords, PINs, or OTPs.", True),
    "billing": ("I can help with a billing issue. Never share card details, PINs, or OTPs here. I can create a support ticket for the team to investigate.", True),
    "order_status": ("Please check the Orders section of your account for the latest tracking status. If it looks incorrect, I can create a support ticket.", True),
    "human_agent": ("I can route your request to the support workflow by creating a ticket. Please briefly describe what you need help with.", True),
    "thanks": ("You're welcome! Is there anything else I can help you with?", False),
    "goodbye": ("Thanks for contacting support. Have a good day!", False),
}
FALLBACK_REPLY = ("I'm not fully sure how to answer that yet. Please explain the issue in a little more detail. If you're signed in, I can create a support ticket for our team.", True)
CONFIDENCE_THRESHOLD = 0.18

_training_texts = [text for examples in INTENT_EXAMPLES.values() for text in examples]
_training_labels = [intent for intent, examples in INTENT_EXAMPLES.items() for _ in examples]
_model = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2), strip_accents="unicode", sublinear_tf=True)),
    ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
])
_model.fit(_training_texts, _training_labels)


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", text.lower()).strip()


def predict_intent(message: str) -> Tuple[str, float]:
    cleaned = normalize(message)
    if not cleaned:
        return "unknown", 0.0
    probabilities = _model.predict_proba([cleaned])[0]
    best_index = probabilities.argmax()
    return _model.classes_[best_index], float(probabilities[best_index])


def get_bot_reply(message: str) -> Tuple[str, bool]:
    intent, confidence = predict_intent(message)
    if confidence < CONFIDENCE_THRESHOLD:
        return FALLBACK_REPLY
    return RESPONSES.get(intent, FALLBACK_REPLY)
