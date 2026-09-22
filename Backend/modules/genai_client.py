"""Shared google-genai client helper.

Centralizes Gemini access via the modern `google-genai` SDK (replaces the
deprecated `google.generativeai` package). All modules that call Gemini
should go through `generate_json_or_text()` or `get_client()` here instead
of importing google.generativeai directly, so thinking-budget behavior is
consistent everywhere.
"""

from __future__ import annotations

import os
from typing import Any, Optional

_client = None


def get_client():
    """Lazily construct and cache a genai.Client using GOOGLE_API_KEY."""
    global _client
    if _client is not None:
        return _client
    from google import genai

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    _client = genai.Client(api_key=api_key)
    return _client


def generate(
    model: str,
    prompt: str,
    temperature: float = 0.7,
    max_output_tokens: int = 2048,
    thinking_budget: int = 0,
) -> Optional[Any]:
    """Call Gemini via google-genai and return the raw response object.

    thinking_budget=0 disables "thinking" tokens entirely for Gemini 2.5
    models, so the full max_output_tokens budget goes to the visible
    answer instead of being silently consumed by internal reasoning.

    Returns None if no API key is configured. Raises on API errors so
    callers can decide how to fall back (matches prior behavior).
    """
    client = get_client()
    if client is None:
        return None

    from google.genai import types

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
        ),
    )
    return response
