"""Verification of claims using NVIDIA NIM models (replaces OpenRouter).

This module runs three free, lightweight NVIDIA NIM-hosted models against a
list of claims and aggregates their verdicts via majority voting, mirroring
the interface of openrouter_verification.verify_claims exactly so it can be
swapped in without touching main.py or any other caller.

Models chosen (all free-tier NIM endpoints, small *active* param counts
despite large total MoE sizes, from three different labs for voting
diversity):
    - nvidia/nemotron-3.5-lightning-30b-a3b   (30B MoE, 3B active)
    - google/gemma-4-31b-it                   (31B MoE, 31B active)
    - nvidia/nemotron-3-super-120b-a12b       (120B MoE, 12B active)

Uses a dedicated API key (NVIDIA_NIM_API_2) so verification traffic is
tracked/billed separately from answer-generation NIM traffic
(NVIDIA_NIM_API), per the user's request.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from typing import List, Dict, Optional

from Backend.modules import metrics
from Backend.modules.call2_verification import _SYSTEM_PROMPT, _format_claim_batch

NVIDIA_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Model identifiers to use for verification. If NVIDIA changes/retires a free
# endpoint, update the id here (get the exact "API Reference" model id from
# the model's page on build.nvidia.com) — one bad id will only disable that
# one model's vote, not the whole pipeline, since call_nim_model fails soft
# per-model with visible logging.
VERIFICATION_MODEL_IDS = [
    "nvidia/nemotron-3.5-lightning-30b-a3b",
    "google/gemma-4-31b-it",
    "nvidia/nemotron-3-super-120b-a12b",
]


def _get_nim_api_key() -> Optional[str]:
    """Read the dedicated NVIDIA NIM verification key from the environment."""
    return os.getenv("NVIDIA_NIM_API_2")


def call_nim_model(model_id: str, system_prompt: str, user_prompt: str) -> Optional[str]:
    """Invoke an NVIDIA NIM model with a system and user prompt.

    Returns the response text, or None on failure. Failures are printed
    (status code + response body / exception) rather than swallowed, so a
    bad model id or auth problem is visible in logs instead of silently
    producing an empty vote for every claim.
    """
    api_key = _get_nim_api_key()
    if not api_key:
        print("[NIM VERIFY SKIPPED] NVIDIA_NIM_API_2 not configured")
        return None

    try:
        from openai import OpenAI
    except Exception as e:
        print(f"[NIM VERIFY FAILED] openai package not available: {e!r}")
        return None

    try:
        client = OpenAI(api_key=api_key, base_url=NVIDIA_NIM_BASE_URL)
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=2000,
        )
        content = response.choices[0].message.content
        if not content:
            print(f"[NIM VERIFY FAILED] model={model_id!r} returned empty content")
            return None
        return content
    except Exception as e:
        print(f"[NIM VERIFY FAILED] model={model_id!r} exception={e!r}")
        return None


def _parse_verdicts(response_text: str) -> List[Dict]:
    """Extract the ``verdicts`` list from the model's raw response.

    Handles markdown code fences (```json ... ```) the same way Call 1 and
    Call 2 do, since NIM models sometimes wrap JSON output in them.
    """
    if not response_text:
        return []
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"```\s*$", "", cleaned)
        cleaned = cleaned.strip()
    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    json_str = json_match.group(0) if json_match else cleaned
    try:
        data = json.loads(json_str)
        if isinstance(data, dict) and "verdicts" in data:
            return data["verdicts"]
        print(f"[NIM VERIFY] unexpected JSON shape (no 'verdicts' key): {json_str[:300]!r}")
    except Exception as e:
        print(f"[NIM VERIFY] JSON parse failed: {e!r} | raw: {json_str[:300]!r}")
    return []


def verify_claims(claims: List[Dict], model_ids: List[str] = None) -> List[Dict]:
    """Verify each claim with the configured NVIDIA NIM verification models.

    Same interface and majority-vote aggregation logic as
    openrouter_verification.verify_claims, so this is a drop-in replacement.

    Parameters
    ----------
    claims: List[Dict]
        The claim dictionaries produced by the decomposition step.
    model_ids: List[str] | None
        Model identifiers to use. If ``None``, VERIFICATION_MODEL_IDS is used.

    Returns
    -------
    List[Dict]
        The same claim objects enriched with a ``verdict`` field (aggregated)
        and a private ``_verifier_results`` list containing the raw verdicts
        from each model for debugging/analysis.
    """
    if model_ids is None:
        model_ids = VERIFICATION_MODEL_IDS

    batch_size = 20
    verdicts_by_claim: Dict[str, List[str]] = defaultdict(list)
    for model_id in model_ids:
        for i in range(0, len(claims), batch_size):
            batch = claims[i : i + batch_size]
            user_prompt = _format_claim_batch(batch)
            metrics.increment_llm_calls()
            resp_text = call_nim_model(model_id, _SYSTEM_PROMPT, user_prompt)
            if resp_text is None:
                # Model call failed; skip this batch for this model (the
                # other models' votes still count for these claims).
                continue
            batch_verdicts = _parse_verdicts(resp_text)
            for v in batch_verdicts:
                claim_id = v.get("id")
                verdict = v.get("verdict")
                if claim_id and verdict:
                    verdicts_by_claim[claim_id].append(verdict)

    for claim in claims:
        cid = claim.get("id")
        vlist = verdicts_by_claim.get(cid, [])
        claim["_verifier_results"] = vlist
        if not vlist:
            claim["verdict"] = "insufficient_evidence"
            continue
        counts = Counter(vlist)
        most_common = counts.most_common()
        top_count = most_common[0][1]
        top_verdicts = [v for v, c in most_common if c == top_count]
        if len(top_verdicts) == 1:
            claim["verdict"] = top_verdicts[0]
        else:
            claim["verdict"] = "insufficient_evidence"
    return claims


# ---------------------------------------------------------------------------
# Simple CLI for manual testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m modules.nim_verification <claims_json_file>")
        sys.exit(1)
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        input_claims = json.load(f)
    results = verify_claims(input_claims)
    print(json.dumps(results, indent=2))
