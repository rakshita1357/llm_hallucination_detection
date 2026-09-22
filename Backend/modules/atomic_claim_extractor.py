import spacy
import re

# Load spaCy model – fallback to a blank English model if the full model is missing.
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = spacy.blank("en")
    # Ensure a sentencizer is available for sentence segmentation.
    if not nlp.has_pipe("sentencizer"):
        nlp.add_pipe("sentencizer")

# Common clause separators
CLAUSE_SPLITTERS = [
    " and ",
    " while ",
    " but ",
    " because ",
    " although ",
    " since ",
    " whereas "
]


def split_into_atomic_claims(sentence):
    """
    Split sentence into smaller atomic claims
    """

    claims = [sentence]

    # Apply recursive splitting
    for splitter in CLAUSE_SPLITTERS:

        temp_claims = []

        for claim in claims:

            split_parts = claim.split(splitter)

            for part in split_parts:

                cleaned = part.strip()

                if len(cleaned.split()) > 3:
                    temp_claims.append(cleaned)

        claims = temp_claims

    return claims


def extract_atomic_claims(text):
    """
    Extract atomic claims from full response
    """

    doc = nlp(text)

    atomic_claims = []

    # Process sentence-by-sentence
    for sent in doc.sents:

        sentence = sent.text.strip()

        split_claims = split_into_atomic_claims(sentence)

        atomic_claims.extend(split_claims)

    return atomic_claims