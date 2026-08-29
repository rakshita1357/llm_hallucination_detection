"""Phase 2 – P2.4 synthetic contradiction validation.

The test constructs two claims that contradict each other and have no external
evidence. A ``contradicts`` edge is supplied manually. The graph‑propagation
routine must flag both claims with ``internal_consistency_failure``.
"""

from modules.graph_propagation import propagate_claims


def test_internal_consistency_detection():
    # Two contradictory claims with no evidence (simulating a retrieval‑only miss).
    claims = [
        {"id": "c1", "verdict": "insufficient_evidence", "evidence": []},
        {"id": "c2", "verdict": "insufficient_evidence", "evidence": []},
    ]
    edges = [
        {"source_id": "c1", "target_id": "c2", "type": "contradicts"},
    ]
    result = propagate_claims(claims, edges)
    # Both claims should be flagged.
    failures = [c for c in result if c.get("internal_consistency_failure")]
    assert len(failures) == 2, "Both contradictory claims should be flagged"
