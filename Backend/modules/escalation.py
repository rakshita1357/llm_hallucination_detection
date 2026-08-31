"""Residual‑claim escalation (Phase 3 – P3.2).

The escalation step invokes a *different* model (or heuristic) on the residual
claims identified by ``identify_residual_claims``. In a real system this would be
a call to a second LLM provider; here we implement a deterministic fallback that
behaves differently from the primary pipeline.

Constraints:
* The residual set must not exceed ~15% of the total claim count. If it does,
  a warning is logged (via ``print``) but the function still proceeds – a real
  deployment could abort or truncate.
* The function returns a list of dictionaries, each containing the original claim
  ``id`` and a new ``escalated_verdict`` field (``"supported"`` or ``"refuted"``).
  The heuristic simply looks for negation/uncertainty cues to decide.
"""

from __future__ import annotations

from typing import List, Dict

# Simple cue list that tends to indicate a claim is less certain.
_UNCERTAIN_CUES = {"not", "never", "maybe", "perhaps", "possible", "could", "unlikely"}


def _heuristic_escalation(claim: Dict) -> str:
    """Return ``"refuted"`` if the claim text contains uncertain cues, else ``"supported"``.
    This deterministic rule provides a different behavior from the primary
    verification step, emulating a second model.
    """
    text = claim.get("text", "").lower()
    tokens = set(text.split())
    if tokens & _UNCERTAIN_CUES:
        return "refuted"
    return "supported"


def escalate_residual_claims(
    all_claims: List[Dict],
    residual_claims: List[Dict],
    max_fraction: float = 0.15,
) -> List[Dict]:
    """Escalate residual claims using a secondary heuristic/model.

    Parameters
    ----------
    all_claims:
        Full list of claim dictionaries after graph propagation.
    residual_claims:
        Sub‑set returned by ``identify_residual_claims``.
    max_fraction:
        Upper bound on the proportion of residual claims allowed before a
        warning is emitted (default 15%).

    Returns
    -------
    List[Dict]
        Each entry contains ``id`` and ``escalated_verdict``. The original
        claim dictionary is left untouched; callers can merge the result as
        needed.
    """
    if not residual_claims:
        return []
    total = len(all_claims)
    if total > 0 and len(residual_claims) / total > max_fraction:
        print(
            f"[Escalation warning] Residual set size {len(residual_claims)}/{total} "
            f"exceeds {max_fraction*100:.0f}% – consider reviewing the cap."
        )
    escalated: List[Dict] = []
    for rc in residual_claims:
        verdict = _heuristic_escalation(rc)
        escalated.append({"id": rc.get("id"), "escalated_verdict": verdict})
    return escalated
