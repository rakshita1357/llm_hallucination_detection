"""Call 2 – Batched verification of claims.

This module implements the second LLM call of the MVP pipeline:
* It receives a list of claim dictionaries (the output of `call1_decomposition`
  possibly enriched by `retrieval.retrieve_for_claims`).
* Claims are grouped into batches of up to 20 items to respect the hard cap.
* For each batch a single Gemini request is made with a structured prompt that
  asks the model to verify each claim based on the supplied evidence snippets.
* The model must return a JSON object of the form:

```json
{"verdicts": [{"id": "c1", "verdict": "supported"}, ...]}
```

* The function merges the returned verdicts back onto the original claim objects
  (adding a ``verdict`` key) and returns the enriched list.

If the Gemini API key is not configured, a deterministic fallback is used:
* Every claim receives the verdict ``insufficient_evidence`` – this mirrors the
  behavior expected when retrieval yields no evidence.

The implementation mirrors the style of `modules.call1_decomposition` and keeps
the LLM interaction isolated so the rest of the pipeline can be swapped out
without changes.
"""

from __future__ import annotations

import json
import os
import re
from typing import List, Dict, Optional

# ---------------------------------------------------------------------------
# Gemini model handling (identical to call1_decomposition for consistency)
# ---------------------------------------------------------------------------
_gemini_model = None
_GOOGLE_API_KEY = None


def _get_gemini_model():
    """Lazy‑initialise the Gemini model using ``GOOGLE_API_KEY``.

    Returns ``None`` when the environment variable is missing, allowing the
    caller to fall back to a deterministic stub.
    """
    global _gemini_model, _GOOGLE_API_KEY
    if _gemini_model is not None:
        return _gemini_model
    try:
        import google.generativeai as genai
        _GOOGLE_API_KEY = _GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
        if _GOOGLE_API_KEY:
            genai.configure(api_key=_GOOGLE_API_KEY)
            _gemini_model = genai.GenerativeModel("gemini-3.1-pro")
        else:
            _gemini_model = None
    except ImportError:
        _gemini_model = None
    return _gemini_model

# ---------------------------------------------------------------------------
# Prompt construction helpers
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are an AI assistant that verifies factual claims based on provided evidence.
For each claim you must output a JSON object with the following schema:

{\"verdicts\": [{\"id\": <claim_id>, \"verdict\": <one of \"supported\", \"refuted\", \"insufficient_evidence\">}, ...]}

Follow these rules:
1. Use only the evidence supplied for a claim when deciding the verdict.
2. If the evidence directly supports the claim, output "supported".
3. If the evidence directly contradicts the claim, output "refuted".
4. If the evidence is missing, ambiguous, or does not address the claim, output "insufficient_evidence".
5. Do **not** fabricate evidence – rely solely on the snippets given.
"""


def _format_claim_batch(claims: List[Dict]) -> str:
    """Create a user‑prompt string describing a batch of claims.

    The format is deliberately simple so the LLM can reliably parse it.
    Each claim is rendered as:
    ```
    ID: <id>
    Claim: <text>
    Evidence:
    - <snippet 1>
    - <snippet 2>
    ```
    Blank lines separate claims.
    """
    parts: List[str] = []
    for claim in claims:
        claim_id = claim.get("id", "")
        claim_text = claim.get("text", "")
        evidence = claim.get("evidence", [])
        # Ensure evidence is a list of dicts with a "snippet" key.
        snippets = [e.get("snippet", "") for e in evidence if isinstance(e, dict)]
        evidence_block = "\n".join(f"- {s}" for s in snippets) if snippets else "(none)"
        parts.append(
            f"ID: {claim_id}\nClaim: {claim_text}\nEvidence:\n{evidence_block}\n"
        )
    return "\n".join(parts)

# ---------------------------------------------------------------------------
# Core verification logic
# ---------------------------------------------------------------------------

def _verify_batch(claims_batch: List[Dict]) -> List[Dict]:
    """Verify a single batch of up to 20 claims using Gemini.

    Returns a list of ``{"id": ..., "verdict": ...}`` dictionaries.
    If the LLM call fails or returns malformed JSON, the function falls back
    to a heuristic based on ``self_confidence`` when available.
    """
    model = _get_gemini_model()
    if model is None:
        # No API key – deterministic fallback.
        return [{"id": c.get("id", ""), "verdict": "insufficient_evidence"} for c in claims_batch]

    user_prompt = _format_claim_batch(claims_batch)
    try:
        response = model.generate_content(
            _SYSTEM_PROMPT + "\n\n" + user_prompt,
            generation_config={"temperature": 0.0, "max_output_tokens": 2000},
        )
        content = response.text or ""
        # Extract the JSON block.
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        json_str = json_match.group(0) if json_match else content
        data = json.loads(json_str)
        if isinstance(data, dict) and "verdicts" in data and isinstance(data["verdicts"], list):
            return data["verdicts"]
    except Exception as e:
        print(f"Call2 verification failed: {e}")

    # Fallback heuristic – rely on self_confidence if present.
    fallback = []
    for c in claims_batch:
        conf = c.get("self_confidence")
        if isinstance(conf, (int, float)):
            if conf >= 0.8:
                verdict = "supported"
            elif conf <= 0.2:
                verdict = "refuted"
            else:
                verdict = "insufficient_evidence"
        else:
            verdict = "insufficient_evidence"
        fallback.append({"id": c.get("id", ""), "verdict": verdict})
    return fallback


def call2_verify(claims: List[Dict], batch_size: int = 20) -> List[Dict]:
    """Public API – verify all claims, respecting the hard batch limit.

    Parameters
    ----------
    claims:
        List of claim dictionaries. Each claim may optionally contain an ``evidence``
        key (produced by :pymod:`modules.retrieval`).
    batch_size:
        Maximum number of claims to send in a single LLM request. The default of 20
        matches the requirement.

    Returns
    -------
    List[Dict]
        The input claims enriched with a new ``verdict`` field.
    """
    if not claims:
        return []

    enriched: List[Dict] = []
    # Process in batches.
    for i in range(0, len(claims), batch_size):
        batch = claims[i : i + batch_size]
        verdicts = _verify_batch(batch)
        # Build a lookup for quick association.
        verdict_map = {v.get("id", ""): v.get("verdict", "insufficient_evidence") for v in verdicts}
        for claim in batch:
            claim_copy = dict(claim)  # avoid mutating the caller's dicts
            claim_copy["verdict"] = verdict_map.get(claim.get("id", ""), "insufficient_evidence")
            enriched.append(claim_copy)
    return enriched

# ---------------------------------------------------------------------------
# Simple CLI for manual testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python -m modules.call2_verification <claims_json_file>")
        sys.exit(1)
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        input_claims = json.load(f)
    results = call2_verify(input_claims)
    print(json.dumps(results, indent=2))
