'''Gemini answer generation module.

Migrated to the modern `google-genai` SDK (via Backend.modules.genai_client)
from the deprecated `google.generativeai` package. thinking_budget=0 ensures
the full max_output_tokens budget goes to the visible answer instead of
being silently consumed by internal "thinking" tokens, which was the root
cause of truncated answers under the old SDK.
'''

from __future__ import annotations

from typing import Any, Dict

from Backend.modules.genai_client import generate

GEMINI_MODEL_NAME = "gemini-2.5-flash"


def generate_gemini_answer(prompt: str) -> Dict[str, Any]:
    """Generate an answer using Gemini via the google-genai SDK.

    Return format mirrors ``modules.answer_generator.generate_answer`` so it
    can be used interchangeably.
    """
    try:
        response = generate(
            model=GEMINI_MODEL_NAME,
            prompt=prompt,
            temperature=0.7,
            max_output_tokens=2048,
            thinking_budget=0,
        )
    except Exception as exc:
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

    if response is None:
        print("[GEMINI ANSWER SKIPPED] GOOGLE_API_KEY not configured")
        return {
            "answer_text": None,
            "token_ids": None,
            "logprobs": None,
            "offsets": None,
            "generation_successful": False,
            "metadata": {
                "reason": "GOOGLE_API_KEY_not_configured",
                "model": GEMINI_MODEL_NAME,
                "question": prompt,
            },
        }

    answer_text = response.text or ""
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
            "note": "Token-level logprobs not available via Gemini API",
            "thoughts_token_count": getattr(response.usage_metadata, "thoughts_token_count", None),
        },
    }


if __name__ == "__main__":  # pragma: no cover
    import json, sys
    if len(sys.argv) < 2:
        print("Usage: python -m modules.gemini_answer '<prompt>'")
        sys.exit(1)
    prompt = sys.argv[1]
    result = generate_gemini_answer(prompt)
    print(json.dumps(result, indent=2, ensure_ascii=False))
