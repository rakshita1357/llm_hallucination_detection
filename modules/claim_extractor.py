import spacy

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")


def extract_claims(text):
    """
    Extract claims from LLM response
    """

    doc = nlp(text)

    claims = []

    # Split into sentences
    for sentence in doc.sents:

        sentence_text = sentence.text.strip()

        # Ignore very short sentences
        if len(sentence_text.split()) > 3:
            claims.append(sentence_text)

    return claims