
from chatbot.nlp_engine import preprocess_text

questions = [
    "How can I find an internship?",
    "WHAT ARE THE BEST SKILLS FOR CSE STUDENTS?",
    "How do I prepare for technical interviews?"
]

for question in questions:
    print("Original:", question)
    print("Processed:", preprocess_text(question))
    print("-" * 50)
