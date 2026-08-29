"""Naive aggregation of claim verification results (P1.5).

The function takes the list of claim dictionaries produced by the previous steps
(Call 1 decomposition, optional retrieval, and Call 2 verification) and produces a
simple report:

* ``aggregate_confidence`` – a single float in ``[0, 1]`` representing the
  overall confidence that the original answer is factual. The naive strategy
  maps each claim verdict to a numeric score (supported = 1.0, refuted = 0.0,
  insufficient_evidence = 0.5) and returns the arithmetic mean.
* ``report`` – a list of per‑claim entries containing the ``id``, ``text``,
  ``verdict`` and the derived ``score`` used for aggregation. The original claim
  dictionary is otherwise preserved (e.g., ``self_confidence``, ``logprob_entropy``
  and any retrieved ``evidence``).

This module is deliberately lightweight; more sophisticated aggregation (e.g.,
confidence weighting, graph‑based propagation) will be added in later phases.
"""

from __future__ import annotations

from typing import List, Dict

# Mapping from verdict strings to numeric scores used for aggregation.
_VERDICT_SCORE = {
    "supported": 1.0,
    "refuted": 0.0,
    "insufficient_evidence": 0.5,
}


def _score_from_verdict(verdict: str) -> float:
    """Return the numeric score for a given verdict.

    Unknown verdicts fall back to ``0.5`` (neutral) to avoid crashes while still
    contributing a middle value to the average.
    """
    return _VERDICT_SCORE.get(verdict, 0.5)


def aggregate_claims(claims: List[Dict]) -> Dict:
    """Aggregate per‑claim verification results into an overall confidence.

    Parameters
    ----------
    claims:
        List of claim dictionaries. Each claim **must** contain a ``verdict``
        key with one of the values ``supported``, ``refuted`` or
        ``insufficient_evidence`` (as produced by ``call2_verification``). The
        function tolerates missing verdicts by treating them as neutral.

    Returns
    -------
    Dict with the following structure::

        {
            "aggregate_confidence": <float in [0, 1]>,
            "report": [
                {"id": ..., "text": ..., "verdict": ..., "score": <float>},
                ...
            ]
        }
    """
    if not claims:
        return {"aggregate_confidence": 0.0, "report": []}

    report: List[Dict] = []
    total_score = 0.0
    for claim in claims:
        verdict = claim.get("verdict", "insufficient_evidence")
        score = _score_from_verdict(verdict)
        total_score += score
        report.append({
            "id": claim.get("id"),
            "text": claim.get("text"),
            "verdict": verdict,
            "score": score,
        })

    aggregate_confidence = total_score / len(claims)
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
