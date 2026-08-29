"""Simple retrieval stub for flagged claims (P1.3).

This module provides a very lightweight, deterministic retrieval implementation used for
the MVP pipeline. It:

* Deduplicates identical search queries (entity‑level clustering is a future
  enhancement).
* Caches results per process session – repeated queries in the same run reuse the
  cached answer.
* Returns a list of placeholder evidence snippets for each claim that requires
  retrieval. The shape matches the expected output for later stages (e.g., Call 2).

The real system would call an external search API or a local vector store. The
stub keeps the code testable without network access.
"""

from __future__ import annotations

from typing import Dict, List

# Simple in‑memory cache: query → list of evidence dicts
_EVIDENCE_CACHE: Dict[str, List[Dict[str, str]]] = {}


def _search(query: str) -> List[Dict[str, str]]:
    """Perform a mock search for ``query``.

    In a production system this would invoke a web search API or a local
    knowledge base. Here we return a deterministic placeholder so that the rest
    of the pipeline can operate without external dependencies.
    """
    # Placeholder evidence – in a real implementation this would be the actual
    # snippet(s) and source metadata.
    return [{"snippet": f"Evidence for query: {query}", "source": "stub"}]


def _get_evidence(query: str) -> List[Dict[str, str]]:
    """Return cached evidence if available, otherwise perform a search.

    The cache is scoped to the current interpreter session, satisfying the
    "per‑session cache" requirement.
    """
    if query not in _EVIDENCE_CACHE:
        _EVIDENCE_CACHE[query] = _search(query)
    return _EVIDENCE_CACHE[query]


def deduplicate_queries(queries: List[str]) -> List[str]:
    """Deduplicate a list of search queries.

    The current implementation uses exact string matching. A more sophisticated
    entity‑clustering step could be added later without changing the public API.
    """
    # Preserve order while removing duplicates.
    seen = set()
    deduped: List[str] = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            deduped.append(q)
    return deduped


def retrieve_for_claims(claims: List[Dict]) -> List[Dict]:
    """Retrieve evidence for claims that have ``needs_retrieval`` set.

    Each claim dict is expected to contain a ``search_query`` key (string). The
    function enriches the claim with an ``evidence`` field – a list of evidence
    dictionaries. Claims that do not need retrieval receive an empty list.
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
        # Copy claim to avoid mutating the original dict.
        new_claim = dict(claim)
        new_claim["evidence"] = evidence
        enriched_claims.append(new_claim)
    return enriched_claims
