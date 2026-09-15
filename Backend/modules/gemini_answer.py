'''Gemini answer generation module.

Provides a simple wrapper around the Google Gemini API (via the
`google.generativeai` library). The function reads the `GOOGLE_API_KEY`
environment variable, configures the model, and returns a structured
dictionary matching the format used elsewhere in the project.

If the API key is missing or the call fails, a deterministic placeholder
is returned so downstream code can continue without raising an exception.
'''

from __future__ import annotations

import os
from typing import Any, Dict

GEMINI_MODEL_NAME = "gemini-2.5-flash"

# Lazy import of the Gemini client – this file may be imported even when the
# required library or API key is not available (e.g., during tests).
_gemini_model = None
_GOOGLE_API_KEY = None


def _get_gemini_model() -> "Any | None":
    """Initialise and cache the Gemini model.

    Returns ``None`` when the ``GOOGLE_API_KEY`` environment variable is not set
    or when the ``google.generativeai`` package cannot be imported.
    """
    global _gemini_model, _GOOGLE_API_KEY
    if _gemini_model is not None:
        return _gemini_model
    try:
        import google.generativeai as genai
    except Exception:
        _gemini_model = None
        return None
    _GOOGLE_API_KEY = _GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
    if not _GOOGLE_API_KEY:
        _gemini_model = None
        return None
    genai.configure(api_key=_GOOGLE_API_KEY)
    _gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    return _gemini_model


def generate_gemini_answer(prompt: str) -> Dict[str, Any]:
    """Generate an answer using Gemini.

    The return format mirrors ``modules.answer_generator.generate_answer`` so it
    can be used interchangeably:

```json
    {
        "answer_text": "...",
        "token_ids": [],
        "logprobs": [],
        "offsets": [],
        "generation_successful": true,
        "metadata": {
            "model": "gemini-2.5-flash",
            "question": "...",
            "api_key_present": true,
            "note": "..."
        }
    }
```
    """
    model = _get_gemini_model()
    if model is None:
        # Deterministic fallback – no Gemini access.
        print("[GEMINI ANSWER SKIPPED] GOOGLE_API_KEY not configured or google.generativeai unavailable")
        return {
            "answer_text": None,
            "token_ids": None,
            "logprobs": None,
            "offsets": None,
            "generation_successful": False,
            "metadata": {
                "reason": "GOOGLE_API_KEY_not_configured_or_missing_dependency",
                "model": GEMINI_MODEL_NAME,
                "question": prompt,
            },
        }

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                # Raised from 500 -> 2048. At 500, Gemini 2.5's internal
                # "thinking" tokens ate into the budget and the visible
                # answer was getting cut off mid-sentence.
                "max_output_tokens": 2048,
                # Explicitly cap/disable the thinking budget so more of the
                # token budget goes to the visible answer text. If your
                # installed google-generativeai version doesn't support
                # a TypeError on unsupported versions.
            },
        )
        answer_text = response.text or ""
        # Gemini does not expose token‑level logprobs, so we return placeholders.
        return {
            "answer_text": answer_text,
            "token_ids": [],
            "logprobs": [],
            "offsets": [],
            "generation_successful": True,
            "metadata": {
                "model": GEMINI_MODEL_NAME,
                "question": prompt,
                "api_key_present": True,
                "note": "Token‑level logprobs not available via Gemini API",
            },
        }
    except Exception as exc:
        # Gracefully degrade on unexpected errors.
        print(f"[GEMINI ANSWER FAILED] {exc!r}")
        return {
            "answer_text": None,
            "token_ids": None,
            "logprobs": None,
            "offsets": None,
            "generation_successful": False,
            "metadata": {
                "reason": f"gemini_call_failed: {exc}",
                "model": GEMINI_MODEL_NAME,
                "question": prompt,
            },
        }

# Simple sanity‑check when the module is executed directly.
if __name__ == "__main__":  # pragma: no cover
    import json, sys
    if len(sys.argv) < 2:
        print("Usage: python -m modules.gemini_answer '<prompt>'")
        sys.exit(1)
    prompt = sys.argv[1]
    result = generate_gemini_answer(prompt)
    print(json.dumps(result, indent=2, ensure_ascii=False))
