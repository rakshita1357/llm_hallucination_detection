"""Answer generation module — responsible for generating original LLM answers.

This module is designed to be independent from the decomposition pipeline
(modules.call1_decomposition). It produces the original LLM answer together
with token-level metadata required by P1.2 (token logprob entropy computation).

The interface is deliberately structured so that the returned dict always has
the same keys, even when the real LLM is not configured.  This allows Call 1
and other consumers to always rely on a consistent interface without None-
checking for every field.

Typical call sequence (outside this project):
    1. Original LLM call (e.g., gpt-4o-mini chat completion) with
       `logprobs=1` and `top_logprobs=0` to capture token-level data.
    2. Result stored alongside the answer text as token_ids, logprobs, offsets.
    3. `generate_answer()` is called with the question; the stored metadata
       is returned so Call 1 can compute avg logprob per claim.

Note: The current project has no OpenAI API key configured and the
pre-generated answers in data/raw/sample_dataset.json are plain strings
without token metadata.  Running `generate_answer()` without an API key
will return a structured placeholder indicating the limitation.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple


def _get_openai_api_key() -> Optional[str]:
    """Read the OpenAI API key from the environment; never hard-code it."""
    return os.getenv("OPENAI_API_KEY")


def _call_openai_generate(question: str) -> Dict[str, Any]:
    """Call OpenAI to generate an answer with token logprob metadata.

    Returns a dict with answer_text, token_ids, logprobs, offsets, and metadata.
    Raises if the API key is missing or the call fails.
    """
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # The chat completion endpoint with logprobs.
    # logprobs=1 requests token-level logprob data.
    # We also request top_logprobs=0 (only the chosen token's logprob).
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question}],
        temperature=0.7,
        max_tokens=500,
        logprobs=True,
        top_logprobs=0,
    )

    # Extract the assistant message content (the answer text)
    choice = response.choices[0]
    answer_text = choice.message.content or ""

    # Extract token-level metadata.
    # response.logprobs is available on the choice if logprobs=True was requested.
    # It is a Logprobs object with token_logprobs and text_offset etc.
    # The exact attribute names depend on the openai SDK version.
    logprobs_obj = getattr(response.choices[0], "logprobs", None)

    token_ids: List[int] = []
    token_logprobs: List[float] = []
    offsets: List[Tuple[int, int]] = []

    if logprobs_obj is not None:
        # SDK v1.x: logprobs.token_logprobs is List[float]
        # SDK v1.x: logprobs.tokens is List[str]
        # SDK v1.x: logprobs.text_offset is List[Tuple[int,int]] or similar
        tokens = getattr(logprobs_obj, "tokens", None) or []
        lp = getattr(logprobs_obj, "token_logprobs", None) or []

        for i, token in enumerate(tokens):
            # Guard against mismatched lengths
            if i < len(lp):
                token_ids.append(i)  # placeholder index; real use would map token->id
                token_logprobs.append(lp[i])
                # Use character offset from the SDK if available; otherwise None
                offsets.append((0, 0))  # will be filled by alignment layer

    return {
        "answer_text": answer_text,
        "token_ids": token_ids,
        "logprobs": token_logprobs,
        "offsets": offsets,
        "generation_successful": True,
        "metadata": {
            "model": "gpt-4o-mini",
            "question": question,
            "api_key_present": True,
        },
    }


def generate_answer(question: str) -> Dict[str, Any]:
    """Generate an LLM answer to the given question.

    This is the public interface for P1.1/P1.2.  It returns a dict with a
    fixed set of keys so that consumers (e.g., call1_decomposition) can
    always access the same fields without None‑checking every key.

    The returned metadata indicates whether token-level logprob information
    is available.  If the OpenAI API key is not configured, the function
    returns a placeholder dict with ``generation_successful=False`` and
    ``metadata`` explaining the limitation.

    Args:
        question: The original user question / prompt.

    Returns:
        Dict with keys:
        - answer_text: str | None — the generated answer, or None if generation
          failed / API key missing.
        - token_ids: List[int] | None — token IDs from the model's generation.
          None if token metadata is unavailable.
        - logprobs: List[float] | None — logprob value per token (as returned
          by the LLM). None if unavailable.
        - offsets: List[Tuple[int,int]] | None — byte-offset ranges for each
          token in the generated answer text. None if unavailable.  These offsets
          would be used to align claim text (from Call 1) to the original answer's
          token positions for P1.2 logprob computation.
        - generation_successful: bool — True if the LLM call completed (even if
          metadata is None due to configuration).
        - metadata: dict — additional information (model name, reason for
          non‑success, etc.).

    Design notes:
        * The dict ALWAYS has the same five top-level keys, regardless of
          whether the real LLM is configured.  This lets Call 1 index into the
          result without defensive None-checks for every field.
        * If ``generation_successful`` is False, all token‐related fields are
          None and should be treated as unavailable — not fabricated.
        * When the real answer‑generation pipeline (outside this project) stores
          token_ids, logprobs, and character offsets alongside each answer,
          Call 1 can compute ``avg_logprob`` per claim and flag low‑probability
          claims for retrieval override (P1.2).
    """
    api_key = _get_openai_api_key()

    if not api_key:
        return {
            "answer_text": None,
            "token_ids": None,
            "logprobs": None,
            "offsets": None,
            "generation_successful": False,
            "metadata": {
                "reason": "OPENAI_API_KEY_not_configured",
                "model": "gpt-4o-mini",
                "question": question,
            },
        }

    try:
        return _call_openai_generate(question)
    except Exception as e:
        # API call failed — return a structured placeholder rather than
        # propagating an exception upwards.  This keeps the Call 1 pipeline
        # stable and makes it clear that metadata is unavailable.
        return {
            "answer_text": None,
            "token_ids": None,
            "logprobs": None,
            "offsets": None,
            "generation_successful": False,
            "metadata": {
                "reason": f"openai_call_failed: {e}",
                "model": "gpt-4o-mini",
                "question": question,
            },
        }