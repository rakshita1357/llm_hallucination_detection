import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

# English stopwords
stop_words = set(stopwords.words('english'))


def clean_text(text):
    """
    Function to clean text data
    """

    # Convert to lowercase
    text = text.lower()

    # Remove special characters
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

    # Tokenize text
    tokens = word_tokenize(text)

    # Remove stopwords
    filtered_tokens = [
        word for word in tokens
        if word not in stop_words
    ]

    # Join tokens back
    cleaned_text = " ".join(filtered_tokens)

    return cleaned_text