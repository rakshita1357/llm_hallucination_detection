"""Local sentence‑embedding similarity for claim pairs (Phase 2 – P2.1).

This module provides utilities to compute pairwise similarity between the
atomic claims produced by :pymod:`modules.call1_decomposition`. It uses a
lightweight local sentence‑embedding model from the *sentence‑transformers*
library and spaCy NER to detect entity overlaps. Pairs are returned when
either:

* the cosine similarity of the embeddings exceeds a configurable threshold, or
* the two claims share at least one named entity (case‑insensitive).

The result can be used by later phases to build a claim‑graph with edges such
as ``supports`` or ``contradicts``.
"""

from __future__ import annotations

import json
from typing import List, Dict, Set

import numpy as np
# Attempt to import sentence_transformers; fall back to a simple bag‑of‑words approach if unavailable.
try:
    from sentence_transformers import SentenceTransformer, util
    _HAS_SENTENCE_TRANSFORMERS = True
except Exception:  # pragma: no cover
    _HAS_SENTENCE_TRANSFORMERS = False
import spacy

# ---------------------------------------------------------------------------
# Lazy‑initialised globals for the heavy models.
# ---------------------------------------------------------------------------
_transformer = None
_nlp = None


def _get_transformer():
    """Return a singleton SentenceTransformer instance if the library is available.

    If ``sentence_transformers`` cannot be imported, the function returns ``None``
    and the caller should fall back to a lightweight bag‑of‑words embedding.
    """
    global _transformer
    if _transformer is None:
        if _HAS_SENTENCE_TRANSFORMERS:
            _transformer = SentenceTransformer("all-MiniLM-L6-v2")
        else:
            _transformer = None
    return _transformer


def _get_nlp() -> spacy.language.Language:
    """Return a spaCy ``Language`` pipeline with NER support.

    The ``en_core_web_sm`` model ships with named‑entity recognition. If it is not
    installed we fall back to a blank ``en`` pipeline; the entity step will then
    produce an empty set, which is acceptable – the similarity threshold will
    still drive the filtering.
    """
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback to a blank model – it contains a ``sentencizer`` but no NER.
            _nlp = spacy.blank("en")
            if not _nlp.has_pipe("sentencizer"):
                _nlp.add_pipe("sentencizer")
    return _nlp


def _extract_entities(text: str) -> Set[str]:
    """Extract a set of lower‑cased named‑entity strings from *text*.

    The function uses the spaCy NER component if available. Entity text is
    normalised to lower case to make the comparison case‑insensitive.
    """
    doc = _get_nlp()(text)
    return {ent.text.lower() for ent in doc.ents}


def compute_claim_pair_similarities(
    claims: List[Dict],
    similarity_threshold: float = 0.8,
) -> List[Dict]:
    """Return claim‑pair similarity information.

    Parameters
    ----------
    claims:
        List of claim dictionaries. Each dictionary must contain at least the
        keys ``"id"`` and ``"text"``. Missing keys are ignored for that entry.
    similarity_threshold:
        Cosine similarity cutoff for embedding‑based matches. The default of
        ``0.8`` matches the typical “high similarity” regime for the MiniLM
        model.

    Returns
    -------
    List[Dict]
        Each dict represents a pair that satisfied one of the inclusion
        criteria and has the form::

            {
                "claim1_id": "c1",
                "claim2_id": "c2",
                "similarity": 0.85,
                "reason": "embedding" | "entity" | "both"
            }
    """
    if not claims:
        return []

    # Preserve the original ordering for deterministic output.
    ids = []
    texts = []
    for claim in claims:
        claim_id = claim.get("id")
        claim_text = claim.get("text")
        if not claim_id or not claim_text:
            continue
        ids.append(str(claim_id))
        texts.append(str(claim_text))

    if len(ids) < 2:
        return []

    # ---------------------------------------------------------------
    # Embedding computation.
    # ---------------------------------------------------------------
    # Embedding (or fallback) computation.
    if _HAS_SENTENCE_TRANSFORMERS:
        transformer = _get_transformer()
        embeddings = transformer.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    else:
        # Simple bag‑of‑words binary vectors, normalized.
        nlp = _get_nlp()
        vocab: dict[str, int] = {}
        token_lists: List[List[str]] = []
        for txt in texts:
            doc = nlp(txt)
            tokens = [token.lemma_.lower() for token in doc if not token.is_punct and not token.is_space]
            token_lists.append(tokens)
            for token in tokens:
                if token not in vocab:
                    vocab[token] = len(vocab)
        vocab_size = len(vocab)
        embeddings = np.zeros((len(texts), vocab_size), dtype=np.float32)
        for i, tokens in enumerate(token_lists):
            for token in tokens:
                embeddings[i, vocab[token]] = 1.0
        # Normalise vectors.
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embeddings = embeddings / norms

    # Entity extraction – pre‑compute per‑claim sets to avoid repeated work.
    entity_sets = [_extract_entities(t) for t in texts]

    # Pairwise evaluation.
    results: List[Dict] = []
    n = len(ids)
    # Cosine similarity matrix (embeddings are unit‑norm).
    sim_matrix = embeddings @ embeddings.T
    for i in range(n):
        for j in range(i + 1, n):
            sim_score = float(sim_matrix[i, j])
            overlap = bool(entity_sets[i] & entity_sets[j])
            reason = None
            if sim_score >= similarity_threshold and overlap:
                reason = "both"
            elif sim_score >= similarity_threshold:
                reason = "embedding"
            elif overlap:
                reason = "entity"
            else:
                continue  # Neither criterion met.

            results.append(
                {
                    "claim1_id": ids[i],
                    "claim2_id": ids[j],
                    "similarity": round(sim_score, 4),
                    "reason": reason,
                }
            )
    return results

# ---------------------------------------------------------------------------
# Simple CLI for quick sanity‑checking.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Compute claim‑pair similarities.")
    parser.add_argument("claims_file", help="Path to JSON file containing a list of claim objects.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Cosine similarity threshold for embedding matches (default: 0.8).",
    )
    args = parser.parse_args()

    try:
        with open(args.claims_file, "r", encoding="utf-8") as f:
            claims_data = json.load(f)
    except Exception as exc:
        sys.stderr.write(f"Failed to load claims file: {exc}\n")
        sys.exit(1)

    out = compute_claim_pair_similarities(claims_data, similarity_threshold=args.threshold)
    print(json.dumps(out, indent=2))
