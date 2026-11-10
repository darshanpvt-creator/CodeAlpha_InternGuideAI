import json

from chatbot.matcher import FAQMatcher

# Load FAQ dataset
with open("data/faqs.json", "r", encoding="utf-8") as file:
    faqs = json.load(file)

# Initialize matching engine
matcher = FAQMatcher(faqs)

# Test questions
test_questions = [
    "How do I get an internship?",
    "What programming skills should I learn?",
    "How can I prepare for interviews?",
    "What is the weather today?"
]

for question in test_questions:
    result = matcher.find_answer(question)

    print("\nQuestion:", question)
    print("Matched:", result["matched"])
    print("Confidence:", result["confidence"])
    print("Answer:", result["answer"])
    print("-" * 60)
