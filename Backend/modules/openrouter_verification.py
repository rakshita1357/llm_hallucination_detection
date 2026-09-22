"""Verification of claims using OpenRouter models.

This module runs the three verification models (Nemotron, GLM, Inkling) against a list
of claims and aggregates their verdicts via majority voting.
"""

import json
import re
from collections import Counter, defaultdict
from typing import List, Dict

from .openrouter_client import call_model
from .call2_verification import _SYSTEM_PROMPT, _format_claim_batch

# Model identifiers as per the specification
VERIFICATION_MODEL_IDS = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "mistralai/mistral-7b-instruct:free",
    "meta-llama/llama-3.1-8b-instruct:free",
]


def _parse_verdicts(response_text: str) -> List[Dict]:
    """Extract the ``verdicts`` list from the model's raw response.

    The model is instructed to return JSON; we attempt to locate a JSON object
    in the response and parse it. If parsing fails or the expected structure is
    missing, an empty list is returned.
    """
    if not response_text:
        return []
    # Find the first JSON object in the text.
    json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
    json_str = json_match.group(0) if json_match else response_text
    try:
        data = json.loads(json_str)
        if isinstance(data, dict) and "verdicts" in data:
            return data["verdicts"]
    except Exception:
        pass
    return []


def verify_claims(claims: List[Dict], model_ids: List[str] = None) -> List[Dict]:
    """Verify each claim with the provided OpenRouter verification models.

    Parameters
    ----------
    claims: List[Dict]
        The claim dictionaries produced by the decomposition step.
    model_ids: List[str] | None
        Model identifiers to use. If ``None``, the default three models are used.

    Returns
    -------
    List[Dict]
        The same claim objects enriched with a ``verdict`` field (aggregated) and
        a private ``_verifier_results`` list containing the raw verdicts from each
        model for debugging/analysis.
    """
    if model_ids is None:
        model_ids = VERIFICATION_MODEL_IDS

    batch_size = 20
    # Accumulate per‑claim verdicts from each model.
    verdicts_by_claim: Dict[str, List[str]] = defaultdict(list)
    for model_id in model_ids:
        # Process in batches to respect the hard‑cap.
        for i in range(0, len(claims), batch_size):
            batch = claims[i : i + batch_size]
            user_prompt = _format_claim_batch(batch)
            resp_text = call_model(model_id, _SYSTEM_PROMPT, user_prompt)
            if resp_text is None:
                # Model call failed; skip this batch for this model.
                continue
            batch_verdicts = _parse_verdicts(resp_text)
            for v in batch_verdicts:
                claim_id = v.get("id")
                verdict = v.get("verdict")
                if claim_id and verdict:
                    verdicts_by_claim[claim_id].append(verdict)
    # Aggregate per claim.
    for claim in claims:
        cid = claim.get("id")
        vlist = verdicts_by_claim.get(cid, [])
        # Store raw results for possible UI use.
        claim["_verifier_results"] = vlist
        if not vlist:
            # No information from any verifier – treat as insufficient evidence.
            claim["verdict"] = "insufficient_evidence"
            continue
        counts = Counter(vlist)
        # Determine majority verdict.
        most_common = counts.most_common()
        top_count = most_common[0][1]
        top_verdicts = [v for v, c in most_common if c == top_count]
        if len(top_verdicts) == 1:
            claim["verdict"] = top_verdicts[0]
        else:
            # Tie or ambiguous – fall back to insufficient evidence.
            claim["verdict"] = "insufficient_evidence"
    return claims
