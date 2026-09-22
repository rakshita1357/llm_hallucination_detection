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
import requests
from typing import Dict, List
from Backend.modules import metrics

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
    data_path = os.path.join(os.path.dirname(__file__), "../..", "data", "raw", "sample_dataset.json")
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
    """Search the web for *query* using the Exa API and return up to *top_k* results.

    Each result is a dictionary with ``snippet`` (highlights from the page) and ``source`` (the URL).
    If the EXA_API_KEY is missing or the request fails, an empty list is returned.
    """
    if not query:
        return []
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        return []
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "type": "auto",
        "num_results": top_k,
        "contents": {
            "highlights": {"numSentences": 3, "highlightsPerUrl": 1, "query": query},
            "text": {"maxCharacters": 500},
        },
    }
    try:
        resp = requests.post("https://api.exa.ai/search", json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results: List[Dict[str, str]] = []
        for item in data.get("results", [])[:top_k]:
            snippet = ""
            contents = item.get("contents")
            if isinstance(contents, dict):
                highlights = contents.get("highlights")
            else:
                # Exa also returns highlights/text as top-level keys on some
                # API versions rather than nested under "contents".
                highlights = item.get("highlights")
            if isinstance(highlights, list) and highlights:
                snippet = " ".join(str(h) for h in highlights if h)
            elif isinstance(highlights, str):
                snippet = highlights
            if not snippet:
                text = contents.get("text") if isinstance(contents, dict) else item.get("text")
                if isinstance(text, str):
                    snippet = text
            results.append({
                "snippet": snippet,
                "source": item.get("url", ""),
                "title": item.get("title", ""),
            })
        return results
    except Exception as e:
        print(f"[EXA SEARCH FAILED] {e!r}")
        return []

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
        metrics.increment_retrieval_calls()

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
