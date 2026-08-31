"""Evidence-weighted aggregation of claim verification results.

The function takes the list of claim dictionaries produced by the previous steps
(Call 1 decomposition, retrieval, and Call 2 verification) and produces a
report with an evidence-weighted confidence score.

Key improvements over naive aggregation:
- ``insufficient_evidence`` maps to a low score (0.1) instead of neutral 0.5
- Confidence is weighted by evidence quality (number of sources, source diversity)
- Verifier agreement is factored into the final confidence
- Self-confidence from the generation model is used as a secondary signal only
"""
from __future__ import annotations

from typing import List, Dict

# Mapping from verdict strings to base numeric scores.
# insufficient_evidence is now low (0.1) instead of neutral (0.5).
_VERDICT_BASE_SCORE = {
    "supported": 1.0,
    "refuted": 0.0,
    "insufficient_evidence": 0.1,
}

# Minimum score floor for any claim
_MIN_CLAIM_SCORE = 0.05


def _base_score_from_verdict(verdict: str) -> float:
    """Return the base numeric score for a given verdict."""
    return _VERDICT_BASE_SCORE.get(verdict, _MIN_CLAIM_SCORE)


def _evidence_quality_score(claim: Dict) -> float:
    """Calculate evidence quality score in [0, 1] based on retrieved evidence.

    Factors:
    - Number of evidence sources (more sources = higher confidence)
    - Source diversity (different domains = higher confidence)
    - Evidence snippet length (more content = higher confidence)
    """
    evidence = claim.get("evidence", [])
    if not evidence:
        return 0.0

    # Count unique sources (by domain/URL)
    sources = set()
    total_snippet_length = 0
    for ev in evidence:
        if isinstance(ev, dict):
            url = ev.get("source", "")
            if url:
                # Extract domain for diversity scoring
                from urllib.parse import urlparse
                try:
                    domain = urlparse(url).netloc
                    sources.add(domain)
                except Exception:
                    pass
            snippet = ev.get("snippet", "")
            if isinstance(snippet, str):
                total_snippet_length += len(snippet)

    num_sources = len(evidence)
    num_unique_domains = len(sources)

    # Score based on number of sources (capped at 5)
    source_score = min(num_sources / 5.0, 1.0)

    # Bonus for domain diversity (capped at 3 unique domains)
    diversity_score = min(num_unique_domains / 3.0, 1.0) * 0.3

    # Snippet length bonus (capped at 500 chars per source)
    avg_snippet_len = total_snippet_length / max(num_sources, 1)
    length_score = min(avg_snippet_len / 500.0, 1.0) * 0.2

    # Combined evidence quality score (max 1.0)
    quality = min(source_score + diversity_score + length_score, 1.0)
    return quality


def _verifier_agreement_score(claim: Dict) -> float:
    """Calculate verifier agreement score in [0, 1].

    Higher when multiple verifiers agree on the same verdict.
    """
    verifier_results = claim.get("_verifier_results", [])
    if not verifier_results:
        return 0.0

    from collections import Counter
    counts = Counter(verifier_results)
    total = len(verifier_results)
    max_count = max(counts.values())

    # Agreement ratio: proportion of verifiers agreeing on majority verdict
    agreement = max_count / total if total > 0 else 0.0

    # Bonus for having multiple verifiers (up to 3)
    verifier_count_bonus = min(total / 3.0, 1.0) * 0.2

    return min(agreement + verifier_count_bonus, 1.0)


def _compute_claim_score(claim: Dict) -> float:
    """Compute final confidence score for a single claim.

    Combines:
    - Base verdict score
    - Evidence quality weight
    - Verifier agreement weight
    - Self-confidence as secondary signal (only for insufficient_evidence)
    """
    verdict = claim.get("verdict", "insufficient_evidence")
    base_score = _base_score_from_verdict(verdict)

    # Evidence quality factor (0 to 1)
    evidence_quality = _evidence_quality_score(claim)

    # Verifier agreement factor (0 to 1)
    agreement = _verifier_agreement_score(claim)

    # For supported claims with good evidence and agreement, boost confidence
    if verdict == "supported":
        # Weight: 70% base, 20% evidence quality, 10% agreement
        # High base score (1.0) dominates; evidence and agreement provide modest boost
        score = 0.7 * base_score + 0.2 * evidence_quality + 0.1 * agreement
    elif verdict == "refuted":
        # Refuted claims are high confidence if evidence supports refutation
        score = 0.7 * base_score + 0.2 * evidence_quality + 0.1 * agreement
    else:  # insufficient_evidence
        # Low base score (0.1), but can be boosted by self-confidence
        self_conf = claim.get("self_confidence")
        if isinstance(self_conf, (int, float)):
            self_conf = max(0.0, min(1.0, self_conf))
            # Self-confidence can lift the score but capped at 0.4
            self_conf_boost = self_conf * 0.3
        else:
            self_conf_boost = 0.0

        # Weight: 60% base (low), 20% evidence quality, 20% self-confidence boost
        score = 0.6 * base_score + 0.2 * evidence_quality + 0.2 * self_conf_boost

    # Floor the score
    return max(score, _MIN_CLAIM_SCORE)


def aggregate_claims(claims: List[Dict]) -> Dict:
    """Aggregate per-claim verification results into an evidence-weighted confidence.

    Returns:
        Dict with aggregate_confidence (evidence-weighted) and per-claim report.
    """
    if not claims:
        return {"aggregate_confidence": 0.0, "report": []}

    report: List[Dict] = []
    total_score = 0.0
    for claim in claims:
        verdict = claim.get("verdict", "insufficient_evidence")
        score = _compute_claim_score(claim)
        total_score += score
        report.append({
            "id": claim.get("id"),
            "text": claim.get("text"),
            "verdict": verdict,
            "score": round(score, 3),
        })

    aggregate_confidence = round(total_score / len(claims), 3)
    return {"aggregate_confidence": aggregate_confidence, "report": report}


# ---------------------------------------------------------------------------
# Simple CLI for quick verification
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json, sys
    if len(sys.argv) < 2:
        print("Usage: python -m modules.aggregation <claims_json_file>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        claims = json.load(f)
    result = aggregate_claims(claims)
    print(json.dumps(result, indent=2))
