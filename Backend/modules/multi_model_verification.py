'''Multi‑model verification module.

Provides a thin wrapper around the existing ``call2_verify`` function that
iterates over a list of LLM back‑ends (e.g., Nemotron, GLM, Inkling). Each
model is assumed to be reachable via the generic client logic added to
``modules.call2_verification`` – the client is created from environment
variables ``<MODEL>_API_KEY`` and ``<MODEL>_API_URL``.

The function returns a dictionary mapping the model name to a list of
verdict dictionaries (``{"id": <claim_id>, "verdict": <verdict>}``).
If a model cannot be initialised the entry will contain an empty list.
'''"""

from __future__ import annotations

import copy
from typing import List, Dict

# The verification core already supports selecting a model via the
# ``verification_model`` argument.
from modules.call2_verification import call2_verify


def verify_claims_multi_models(
    claims: List[Dict],
    models: List[str] | None = None,
) -> Dict[str, List[Dict]]:
    """Verify *claims* with several LLM back‑ends.

    Parameters
    ----------
    claims:
        List of claim dictionaries (must contain ``id`` and ``text`` at a
        minimum). The list is deep‑copied for each model to avoid cross‑model
        contamination.
    models:
        Optional list of model identifiers. If ``None`` the default set of
        three auxiliary models is used: ``["nemotron", "glm", "inkling"]``.

    Returns
    -------
    dict[str, list[dict]]
        Mapping from the model name to a list of ``{"id": ..., "verdict": ...}``
        objects as produced by ``call2_verify``.
    """
    if models is None:
        models = ["nemotron", "glm", "inkling"]

    results: Dict[str, List[Dict]] = {}
    for model_name in models:
        # Work on a fresh copy for each model to keep verdicts independent.
        claims_copy = copy.deepcopy(claims)
        try:
            enriched = call2_verify(
                claims_copy,
                verification_model=model_name,
            )
            # Extract just the id and verdict for a compact result.
            model_verdicts = [
                {"id": c.get("id"), "verdict": c.get("verdict", "insufficient_evidence")}
                for c in enriched
            ]
            results[model_name] = model_verdicts
        except Exception as exc:  # pragma: no cover – defensive programming
            # In case the verification pipeline itself raises an unexpected error.
            print(f"Verification with model '{model_name}' failed: {exc}")
            results[model_name] = []
    return results

# Simple CLI for manual testing.
if __name__ == "__main__":  # pragma: no cover
    import json, sys
    if len(sys.argv) < 2:
        print("Usage: python -m modules.multi_model_verification <claims_json_file>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        input_claims = json.load(f)
    out = verify_claims_multi_models(input_claims)
    print(json.dumps(out, indent=2, ensure_ascii=False))
"""
