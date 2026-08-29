"""Residual‑claim identification (Phase 3 – P3.1).

After the full Phase 2 pipeline (retrieval, verification, similarity, NLI, graph
propagation) many claims may still be marked as ``insufficient_evidence``. This
module isolates the *border‑line* claims that are candidates for escalation or
further analysis.

A claim is considered *residual* when:

* Its final verdict is ``insufficient_evidence``.
* Its confidence (either the graph‑adjusted ``effective_confidence`` or the
  original ``self_confidence``) falls within a configurable decision‑boundary
  interval – by default ``[0.4, 0.6]``.

The function returns a list of claim dictionaries (the same shape used elsewhere)
so that downstream code can decide whether to flag, display, or upscale these
claims.
"""

from __future__ import annotations

from typing import List, Dict

def identify_residual_claims(
    claims: List[Dict],
    lower: float = 0.4,
    upper: float = 0.6,
) -> List[Dict]:
    """Return claims that are still ``insufficient_evidence`` and near the
    decision boundary.

    Parameters
    ----------
    claims:
        List of claim dictionaries after graph propagation. Each claim may have
        an ``effective_confidence`` (graph‑adjusted) or a ``self_confidence``
        field. If neither is present, the claim is ignored.
    lower, upper:
        Inclusive confidence interval that defines the borderline region.

    Returns
    -------
    List[Dict]
        Subset of the input claims that satisfy the residual criteria.
    """
    residuals: List[Dict] = []
    for claim in claims:
        if claim.get("verdict") != "insufficient_evidence":
            continue
        # Prefer the graph‑adjusted confidence if available.
        conf = claim.get("effective_confidence")
        if conf is None:
            conf = claim.get("self_confidence")
        if conf is None:
            # No confidence information – cannot decide, skip.
            continue
        if lower <= float(conf) <= upper:
            residuals.append(claim)
    return residuals
