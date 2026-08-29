"""Realistic (still lightweight) retrieval for flagged claims (Phase 1 → P1.3).

The original stub returned a hard‑coded placeholder. This implementation
loads the *sample dataset* (`data/raw/sample_dataset.json`) and uses a
sentence‑embedding model (``sentence‑transformers`` – ``all‑MiniLM‑L6‑v2``) to
perform a deterministic nearest‑neighbor search over the LLM‑generated answers.
If the embedding library cannot be imported, a simple bag‑of‑words fallback is used.

The public API remains unchanged:

* ``deduplicate_queries`` – deduplicates query strings while preserving order.
* ``retrieve_for_claims`` – enriches each claim with an ``evidence`` field
  (list of ``{"snippet": ..., "source": ...}``).

All results are cached per‑process session to honour the “per‑session cache”
requirement and to avoid recomputation for repeated queries.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List

# ---------------------------------------------------------------------------
# Lazy optional imports – we fall back to a bag‑of‑words approach if the heavy
# ``sentence_transformers`` library (or its model download) is unavailable.
# ---------------------------------------------------------------------------
try:
    from sentence_transformers import SentenceTransformer, util
    _HAS_SENTENCE_TRANSFORMERS = True
except Exception:  # pragma: no cover
    _HAS_SENTENCE_TRANSFORMERS = False

# Global caches – instantiated lazily on first use.
_EVIDENCE_CACHE: Dict[str, List[Dict[str, str]]] = {}
_DOCS: List[Dict] = []            # Each entry: {"id": int, "text": str}
_DOC_EMBEDS = None                # ``numpy.ndarray`` of shape (n_docs, dim)
_transformer = None

# ---------------------------------------------------------------------------
# Helpers for loading the corpus and building embeddings
# ---------------------------------------------------------------------------
def _load_corpus() -> None:
    """Load the JSON dataset once per process.

    The file lives at ``data/raw/sample_dataset.json`` relative to the project
    root. For each entry we store its ``id`` and the full ``llm_response`` text –
    this will serve as the searchable document.
    """
    global _DOCS
    if _DOCS:
        return  # Already loaded
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "sample_dataset.json")
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as exc:
        raise RuntimeError(f"Failed to load retrieval corpus: {exc}")
    # Keep only the id and the LLM response text.
    _DOCS = [{"id": entry.get("id"), "text": entry.get("llm_response", "")} for entry in raw]

def _get_transformer() -> "SentenceTransformer | None":
    """Lazy‑initialise the MiniLM embedding model.

    Returns ``None`` when the ``sentence_transformers`` library is unavailable.
    """
    global _transformer
    if _transformer is None and _HAS_SENTENCE_TRANSFORMERS:
        _transformer = SentenceTransformer("all-MiniLM-L6-v2")
    return _transformer

def _embed_texts(texts: List[str]):
    """Return normalized embeddings for *texts*.

    Uses the MiniLM model when available; otherwise falls back to a deterministic
    binary bag‑of‑words representation (compatible with cosine similarity).
    """
    if _HAS_SENTENCE_TRANSFORMERS:
        model = _get_transformer()
        if model is not None:
            return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    # ---- Fallback: simple bag‑of‑words vectors (binary presence) ----
    import numpy as _np
    vocab: dict[str, int] = {}
    token_lists: List[List[str]] = []
    # Minimal tokenisation – split on whitespace and lower‑case.
    for txt in texts:
        tokens = [t.lower() for t in txt.split() if t]
        token_lists.append(tokens)
        for tok in tokens:
            if tok not in vocab:
                vocab[tok] = len(vocab)
    vocab_size = len(vocab)
    mat = _np.zeros((len(texts), vocab_size), dtype=_np.float32)
    for i, tokens in enumerate(token_lists):
        for tok in set(tokens):
            mat[i, vocab[tok]] = 1.0
    # Normalise rows to unit length (avoid division by zero).
    norms = _np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms

def _ensure_doc_embeddings():
    """Compute and cache embeddings for the corpus documents.
    """
    global _DOC_EMBEDS
    if _DOC_EMBEDS is None:
        _load_corpus()
        texts = [doc["text"] for doc in _DOCS]
        _DOC_EMBEDS = _embed_texts(texts)

def _search(query: str, top_k: int = 3) -> List[Dict[str, str]]:
    """Return the *top_k* most similar documents for *query*.

    Each result is a dictionary with ``snippet`` (truncated document text) and
    ``source`` (the original dataset ``id``). The function is deterministic –
    ties are broken by the original document order.
    """
    if not query:
        return []
    _ensure_doc_embeddings()
    query_emb = _embed_texts([query])  # shape (1, dim)
    # Cosine similarity via dot‑product (vectors are L2‑normalised).
    import numpy as _np
    sims = _np.dot(_DOC_EMBEDS, query_emb.T).ravel()
    # Get indices of the highest scores.
    top_idxs = _np.argsort(-sims)[:top_k]
    results: List[Dict[str, str]] = []
    for idx in top_idxs:
        doc = _DOCS[idx]
        snippet = doc["text"][:200].strip()
        if len(doc["text"]) > 200:
            snippet += "..."
        results.append({"snippet": snippet, "source": f"doc_{doc['id']}"})
    return results

# ---------------------------------------------------------------------------
# Public helpers – unchanged signatures
# ---------------------------------------------------------------------------
def _get_evidence(query: str) -> List[Dict[str, str]]:
    """Return cached evidence if present, otherwise perform a search.
    """
    if query not in _EVIDENCE_CACHE:
        _EVIDENCE_CACHE[query] = _search(query)
    return _EVIDENCE_CACHE[query]

def deduplicate_queries(queries: List[str]) -> List[str]:
    """Deduplicate a list of search queries whilst preserving order.
    """
    seen = set()
    deduped: List[str] = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            deduped.append(q)
    return deduped

def retrieve_for_claims(claims: List[Dict]) -> List[Dict]:
    """Enrich claims with evidence when ``needs_retrieval`` is true.

    Each claim must contain a ``search_query`` string. The function returns a new
    list of claim dictionaries where the ``evidence`` key holds a list of snippet
    dictionaries (or an empty list when no retrieval is required).
    """
    # Gather queries for claims that request retrieval.
    queries = [c["search_query"] for c in claims if c.get("needs_retrieval") and c.get("search_query")]
    unique_queries = deduplicate_queries(queries)

    # Populate cache for all unique queries.
    for q in unique_queries:
        _get_evidence(q)

    # Attach evidence to each claim.
    enriched_claims: List[Dict] = []
    for claim in claims:
        if claim.get("needs_retrieval") and claim.get("search_query"):
            evidence = _EVIDENCE_CACHE.get(claim["search_query"], [])
        else:
            evidence = []
        new_claim = dict(claim)  # shallow copy
        new_claim["evidence"] = evidence
        enriched_claims.append(new_claim)
    return enriched_claims
