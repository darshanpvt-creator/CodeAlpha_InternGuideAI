
import re
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Initialize NLP tools
stemmer = PorterStemmer()
try:
    STOP_WORDS = set(stopwords.words("english"))
except LookupError:
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    STOP_WORDS = set(ENGLISH_STOP_WORDS)

def preprocess_text(text):
    """
    Clean and normalize user questions.
    """

    if not isinstance(text, str):
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # Extract words and numbers
    tokens = re.findall(r"\b[a-zA-Z0-9]+\b", text)

    # Remove stopwords and apply stemming
    processed_tokens = [
        stemmer.stem(word)
        for word in tokens
        if word not in STOP_WORDS
    ]

    return " ".join(processed_tokens)

