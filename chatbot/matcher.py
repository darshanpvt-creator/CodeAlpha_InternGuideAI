
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from chatbot.nlp_engine import preprocess_text


class FAQMatcher:
    def __init__(self, faqs, threshold=0.20):
        self.faqs = faqs
        self.threshold = threshold

        self.documents = []
        self.faq_indices = []

        # Include original questions and alternative phrasings
        for index, faq in enumerate(faqs):
            questions = [faq["question"]]
            questions.extend(faq.get("variations", []))

            for question in questions:
                self.documents.append(question)
                self.faq_indices.append(index)

        # Convert FAQ questions into TF-IDF vectors
        self.vectorizer = TfidfVectorizer(
            preprocessor=preprocess_text,
            tokenizer=str.split,
            token_pattern=None,
            lowercase=False,
            ngram_range=(1, 2),
            sublinear_tf=True
        )

        self.faq_vectors = self.vectorizer.fit_transform(
            self.documents
        )

    def find_answer(self, user_question):
        if not isinstance(user_question, str) or not user_question.strip():
            return {
                "matched": False,
                "answer": "Please enter a question so I can help you.",
                "confidence": 0.0
            }

        # Reject questions unrelated to internships and career guidance
        domain_keywords = {
            "intern", "internship", "career", "job", "resume", "cv",
            "skill", "programming", "coding", "project", "github",
            "interview", "placement", "certificate", "course",
            "student", "college", "university", "software",
            "developer", "engineer", "engineering", "artificial",
            "intelligence", "machine", "learning", "python",
            "java", "technology", "technical", "recruiter",
            "portfolio", "remote", "application", "experience", "communication",
            "documentation", "readme", "scam", "professional",
            "study", "time", "speak", "speaking", "confident",
            "confidence", "presentation", "communication"
        }

        # Normalize domain keywords using the same NLP preprocessing
        normalized_domain_keywords = set()

        for keyword in domain_keywords:
            normalized_domain_keywords.update(
                preprocess_text(keyword).split()
            )

        question_words = set(preprocess_text(user_question).split())

        if not question_words.intersection(normalized_domain_keywords):
            return {
                "matched": False,
                "answer": (
                    "I'm designed to help with internships, career "
                    "preparation, technical skills, projects, and "
                    "student guidance. Please ask me a related question."
                ),
                "confidence": 0.0
            }

        # Transform the user's question
        question_vector = self.vectorizer.transform([user_question])

        # Calculate cosine similarity
        similarities = cosine_similarity(
            question_vector,
            self.faq_vectors
        ).flatten()

        best_index = similarities.argmax()
        best_score = float(similarities[best_index])

        faq_index = self.faq_indices[best_index]
        best_faq = self.faqs[faq_index]

        # Reject weak matches
        if best_score < self.threshold:
            return {
                "matched": False,
                "answer": (
                    "I'm not confident I understand that question yet. "
                    "Please try rephrasing it or ask about internships, "
                    "skills, projects, resumes, or career preparation."
                ),
                "confidence": round(best_score, 4)
            }

        return {
            "matched": True,
            "category": best_faq["category"],
            "matched_question": best_faq["question"],
            "answer": best_faq["answer"],
            "confidence": round(best_score, 4)
        }
