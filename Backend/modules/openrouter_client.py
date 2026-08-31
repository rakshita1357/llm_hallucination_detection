"""OpenRouter client for verification models.

Provides a thin wrapper around the OpenRouter API. The client is deliberately
lightweight – it builds the request payload, sends the HTTP POST, and returns
the raw response text (or ``None`` on failure).

All verification calls must use the same ``Authorization: Bearer <key>`` header
and respect the shared base URL ``https://openrouter.ai/api/v1``.
"""

import os
import json
import requests
from typing import Optional

BASE_URL = "https://openrouter.ai/api/v1"

def _get_api_key() -> Optional[str]:
    """Read the OpenRouter API key from the environment.

    Returns ``None`` if the key is missing.
    """
    return os.getenv("OPENROUTER_API_KEY")

def call_model(model_id: str, system_prompt: str, user_prompt: str) -> Optional[str]:
    """Invoke an OpenRouter model with a system and user prompt.

    Parameters
    ----------
    model_id: str
        The model identifier, e.g. ``nvidia/nemotron-3-ultra-550b-a55b:free``.
    system_prompt: str
        The system message defining the task.
    user_prompt: str
        The user‑facing prompt (e.g., batched claims).

    Returns
    -------
    Optional[str]
        The ``response`` text from the model if the request succeeded and a
        ``content`` field is present; otherwise ``None``.
    """
    api_key = _get_api_key()
    if not api_key:
        return None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 2000,
    }
    try:
        resp = requests.post(f"{BASE_URL}/chat/completions", json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # OpenRouter returns a list of choices similar to OpenAI
        if isinstance(data, dict):
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content")
        return None
    except Exception as e:
        # Logging is omitted to avoid leaking keys; callers should handle None.
        return None
