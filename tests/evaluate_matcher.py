import json
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chatbot.matcher import FAQMatcher

FAQ_PATH = Path("data/faqs.json")

with FAQ_PATH.open("r", encoding="utf-8") as file:
    faqs = json.load(file)

matcher = FAQMatcher(faqs)

test_cases = [
    ("How can I detect fake internships?", "Applications", True),
    ("What belongs in a README?", "Projects", True),
    ("How do I prepare for campus placements?", "Placements", True),
    ("Which technical skills should CSE students learn?", "Skills", True),
    ("What is an AI engineering internship?", "AI Engineering", True),
    ("How can I find remote internships?", "Internships", True),
    ("What is the weather on Mars?", None, False),
    ("Who won the football match yesterday?", None, False),
    ("Tell me a joke about animals.", None, False),
    ("What is the capital of Japan?", None, False),
]

correct = 0
positive_correct = 0
negative_correct = 0
positive_total = 0
negative_total = 0
confidence_total = 0.0

print("\n" + "=" * 65)
print("             INTERNGUIDE AI - EVALUATION REPORT")
print("=" * 65)

for number, (question, expected_category, should_match) in enumerate(test_cases, 1):
    result = matcher.find_answer(question)
    matched = result.get("matched", False)
    confidence = result.get("confidence", 0.0)

    if should_match:
        positive_total += 1
        passed = matched and result.get("category") == expected_category
        if passed:
            positive_correct += 1
    else:
        negative_total += 1
        passed = not matched
        if passed:
            negative_correct += 1

    if passed:
        correct += 1

    confidence_total += confidence

    status = "PASS" if passed else "FAIL"
    actual = result.get("category", "Fallback / No match")

    print(f"\nTest {number}: {status}")
    print(f"Question: {question}")
    print(f"Expected: {expected_category or 'No match'}")
    print(f"Actual:   {actual}")
    print(f"Confidence: {confidence:.4f}")

total = len(test_cases)
accuracy = correct / total * 100
positive_rate = positive_correct / positive_total * 100
rejection_rate = negative_correct / negative_total * 100
average_confidence = confidence_total / total

print("\n" + "=" * 65)
print("                    FINAL METRICS")
print("=" * 65)
print(f"Total tests:                 {total}")
print(f"Correct predictions:         {correct}/{total}")
print(f"Overall accuracy:            {accuracy:.2f}%")
print(f"Correct FAQ matching rate:   {positive_rate:.2f}%")
print(f"Unrelated query rejection:   {rejection_rate:.2f}%")
print(f"Average confidence:          {average_confidence:.4f}")
print("=" * 65)

report = {
    "total_tests": total,
    "correct_predictions": correct,
    "overall_accuracy_percent": round(accuracy, 2),
    "faq_matching_rate_percent": round(positive_rate, 2),
    "unrelated_query_rejection_percent": round(rejection_rate, 2),
    "average_confidence": round(average_confidence, 4),
}

Path("evaluation_report.json").write_text(
    json.dumps(report, indent=4),
    encoding="utf-8"
)

print("\nReport saved to evaluation_report.json")

