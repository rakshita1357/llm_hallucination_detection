"""Graph propagation utilities (Phase 2 – P2.3).

This module provides a lightweight, deterministic propagation step that adjusts
claim confidence based on a simple directed edge graph. It does **not** rely on
any external APIs – all logic runs locally.

The expected inputs are:

* ``claims`` – a list of claim dictionaries (as produced by Call 2 verification).
  Required keys:
    - ``id`` – claim identifier (string)
    - ``verdict`` – one of ``"supported"``, ``"refuted"`` or ``"insufficient_evidence"``
    - ``evidence`` – optional list of evidence dictionaries; missing is treated as an empty list.
* ``edges`` – a list of edge dictionaries describing relationships between claims.
  Required keys:
    - ``source_id`` – the claim id where the edge originates
    - ``target_id`` – the claim id where the edge points to
    - ``type`` – either ``"depends_on"`` or ``"contradicts"``

The function returns a new list of claim dictionaries, each enriched with:

* ``effective_confidence`` – a float in ``[0, 1]`` reflecting the original verdict confidence possibly modified by graph reasoning.
* ``internal_consistency_failure`` – a boolean flag (present only when true) indicating that the claim participates in an unsubstantiated contradiction.

The implementation follows the specification in the task plan:
1. **Dependency down‑weighting** – If a claim ``A`` is ``refuted`` and claim ``B``
   has a ``depends_on`` edge from ``B`` → ``A``, ``B``'s ``effective_confidence``
   is multiplied by ``0.5`` (a simple halving). This propagates the refutation downstream.
2. **Internal inconsistency detection** – For any ``contradicts`` edge between two
   claims where **both** claims have *no* external evidence (i.e., the ``evidence``
   list is empty or missing), both claims are marked with
   ``internal_consistency_failure = True``.
"""

from __future__ import annotations

from typing import List, Dict

# Mapping from verdict strings to a base confidence score.
_VERDICT_CONFIDENCE = {
    "supported": 1.0,
    "refuted": 0.0,
    "insufficient_evidence": 0.5,
}


def propagate_claims(claims: List[Dict], edges: List[Dict]) -> List[Dict]:
    """Adjust claim confidences based on a directed edge graph.

    Parameters
    ----------
    claims:
        List of claim dictionaries. Each must contain at least ``id`` and ``verdict``.
        An optional ``evidence`` key (list) is used for the contradiction‑only check.
    edges:
        List of edge dictionaries. Each edge must have ``source_id``, ``target_id`` and ``type`` (``"depends_on"`` or ``"contradicts"``).

    Returns
    -------
    List[Dict]
        Claims enriched with ``effective_confidence`` and, when applicable,
        ``internal_consistency_failure``.
    """
    # Shallow copy of claims to avoid mutating caller data.
    claim_map: Dict[str, Dict] = {c["id"]: dict(c) for c in claims if "id" in c}

    # Initialise effective confidence from the claim's own self_confidence
    # when available (this preserves the real variation computed by Call 1
    # and by aggregation.py's evidence-weighted scoring), falling back to a
    # flat verdict-based default only when self_confidence is missing.
    # Previously this always overwrote effective_confidence with a flat
    # per-verdict constant (e.g. every insufficient_evidence claim -> 0.5),
    # which discarded all per-claim nuance and caused every such claim to
    # collapse onto the same score.
    for claim in claim_map.values():
        self_conf = claim.get("self_confidence")
        if isinstance(self_conf, (int, float)):
            base = float(self_conf)
        else:
            base = _VERDICT_CONFIDENCE.get(claim.get("verdict"), 0.5)
        claim["effective_confidence"] = base

    # 1. Dependency down‑weighting (refuted -> dependent claim).
    for edge in edges:
        if edge.get("type") != "depends_on":
            continue
        src_id = edge.get("source_id")
        tgt_id = edge.get("target_id")
        if not src_id or not tgt_id:
            continue
        src_claim = claim_map.get(src_id)
        tgt_claim = claim_map.get(tgt_id)
        if src_claim and tgt_claim and src_claim.get("verdict") == "refuted":
            tgt_claim["effective_confidence"] *= 0.5

    # 2. Internal‑consistency detection (contradicts without evidence).
    for edge in edges:
        if edge.get("type") != "contradicts":
            continue
        src_id = edge.get("source_id")
        tgt_id = edge.get("target_id")
        if not src_id or not tgt_id:
            continue
        src_claim = claim_map.get(src_id)
        tgt_claim = claim_map.get(tgt_id)
        if not src_claim or not tgt_claim:
            continue
        src_evidence = src_claim.get("evidence", []) or []
        tgt_evidence = tgt_claim.get("evidence", []) or []
        if not src_evidence and not tgt_evidence:
            src_claim["internal_consistency_failure"] = True
            tgt_claim["internal_consistency_failure"] = True

    return list(claim_map.values())
