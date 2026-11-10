import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chatbot.matcher import FAQMatcher

BASE_DIR = Path(__file__).resolve().parents[1]

with open(BASE_DIR / "data" / "faqs.json", encoding="utf-8") as file:
    faqs = json.load(file)

matcher = FAQMatcher(faqs)

tests = [
    ("What is an internship?", "Internships"),
    ("Why should I do an internship?", "Internships"),
    ("What work do interns perform?", "Internships"),
    ("Can undergraduate students apply?", "Eligibility"),
    ("Am I eligible for an internship?", "Eligibility"),
    ("Where do I search for internship opportunities?", "Applications"),
    ("How do I get an internship?", "Applications"),
    ("How can I find work from home internships?", "Internships"),
    ("What should my CV contain?", "Resume"),
    ("How can I make a good student resume?", "Resume"),
    ("Which programming skills should I learn?", "Skills"),
    ("What should a computer science student study?", "Skills"),
    ("Why should I build projects?", "Projects"),
    ("Do projects help in getting internships?", "Projects"),
    ("How do I showcase my coding work?", "GitHub"),
    ("Where should I upload my source code?", "GitHub"),
    ("How do I prepare for coding interviews?", "Interview Preparation"),
    ("What topics should I revise before an interview?", "Interview Preparation"),
    ("Are course completion certificates valuable?", "Certificates"),
    ("Do online courses help students?", "Certificates"),
    ("How do I become a software engineer?", "Career Guidance"),
    ("Give me a software developer roadmap.", "Career Guidance"),
    ("What files are needed for project submission?", "Submissions"),
    ("How do I share my completed internship project?", "Submissions"),
    ("How can I perform well during an internship?", "Internship Experience"),
    ("What are my responsibilities as an intern?", "Internship Experience"),
    ("How do I manage college and internship together?", "Productivity"),
    ("How can I manage my study time?", "Productivity"),
    ("How do I prepare for campus interviews?", "Placements"),
    ("What should I practice for placements?", "Placements"),
    ("How can I speak confidently?", "Communication"),
    ("How do I improve my speaking skills?", "Communication"),
    ("What is an artificial intelligence internship?", "AI Engineering"),
    ("What do AI engineering interns do?", "AI Engineering"),
    ("How should I prepare for an AI internship?", "Preparation"),
    ("Which Python libraries should I learn for machine learning?", "Preparation"),
    ("What should I write in my GitHub README?", "Projects"),
    ("What sections belong in project documentation?", "Projects"),
    ("How do I recognize internship scams?", "Applications"),
    ("Should I pay money to get an internship?", "Applications"),
    ("internship", "Internships"),
    ("resume", "Resume"),
    ("GitHub portfolio", "GitHub"),
    ("AI internship preparation", "Preparation"),
    ("placement preparation", "Placements"),
    ("What is the weather on Mars?", None),
    ("Who won yesterday's football match?", None),
    ("Tell me a joke about animals.", None),
    ("What is the capital of Japan?", None),
    ("How do I bake a chocolate cake?", None),
    ("Explain quantum physics.", None),
]

results = []
correct = 0
positive_correct = 0
negative_correct = 0
positive_total = 0
negative_total = 0
confidence_total = 0.0

print("\n" + "=" * 65)
print("       INTERNGUIDE AI - 50 QUESTION EVALUATION")
print("=" * 65)

for index, (question, expected) in enumerate(tests, 1):
    result = matcher.find_answer(question)
    actual = result.get("category") if result.get("matched") else None
    confidence = result.get("confidence", 0.0)

    passed = actual == expected
    correct += int(passed)
    confidence_total += confidence

    if expected is None:
        negative_total += 1
        negative_correct += int(passed)
    else:
        positive_total += 1
        positive_correct += int(passed)

    results.append({
        "test_number": index,
        "question": question,
        "expected_category": expected,
        "actual_category": actual,
        "confidence": confidence,
        "passed": passed
    })

    print(f"{index:02}. {'PASS' if passed else 'FAIL'} | {question}")
    if not passed:
        print(f"    Expected: {expected} | Actual: {actual}")

total = len(tests)
report = {
    "total_tests": total,
    "correct_predictions": correct,
    "failed_predictions": total - correct,
    "overall_accuracy_percent": round(correct / total * 100, 2),
    "faq_matching_rate_percent": round(
        positive_correct / positive_total * 100, 2
    ),
    "unrelated_query_rejection_percent": round(
        negative_correct / negative_total * 100, 2
    ),
    "average_confidence": round(confidence_total / total, 4),
    "positive_tests": positive_total,
    "negative_tests": negative_total,
    "results": results
}

output = BASE_DIR / "evaluation_report_50.json"
output.write_text(json.dumps(report, indent=4), encoding="utf-8")

print("\n" + "=" * 65)
print("                 FINAL EVALUATION")
print("=" * 65)
print(f"Total tests:                 {total}")
print(f"Correct predictions:         {correct}/{total}")
print(f"Failed predictions:          {total - correct}")
print(f"Overall accuracy:            {report['overall_accuracy_percent']}%")
print(f"FAQ matching rate:            {report['faq_matching_rate_percent']}%")
print(f"Unrelated query rejection:    {report['unrelated_query_rejection_percent']}%")
print(f"Average confidence:           {report['average_confidence']}")
print(f"\nFull report saved: {output}")
print("=" * 65)
