"""Answer generation module — responsible for generating original LLM answers.

This module is designed to be independent from the decomposition pipeline
(modules.call1_decomposition). It produces the original LLM answer together
with token-level metadata required by P1.2 (token logprob entropy computation).

The interface is deliberately structured so that the returned dict always has
the same keys, even when the real LLM is not configured. This allows Call 1
and other consumers to always rely on a consistent interface without None-
checking for every field.

Generation backends:
    - Gemini (Google) — via Backend.modules.genai_client (google-genai SDK,
      thinking_budget=0 to avoid truncation from internal thinking tokens).
    - NVIDIA NIM (OpenAI-compatible endpoint) — serves openai/gpt-oss-120b
      and other NIM-hosted models via the standard OpenAI SDK pointed at
      NVIDIA's base_url.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

from Backend.modules.genai_client import generate as genai_generate

load_dotenv()

# Model names — change here once, used everywhere in this module.
GEMINI_MODEL_NAME = "gemini-2.5-flash"
NVIDIA_NIM_MODEL_NAME = "openai/gpt-oss-120b"
NVIDIA_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"


def _get_google_api_key() -> Optional[str]:
    """Read the Google API key from the environment; never hard-code it."""
    return os.getenv("GOOGLE_API_KEY")


def _get_nvidia_nim_api_key() -> Optional[str]:
    """Read the NVIDIA NIM API key from the environment; never hard-code it."""
    return os.getenv("NVIDIA_NIM_API")


def _fallback_answer(question: str) -> str:
    """Deterministic fallback answer for simple capital queries.

    Used when no API key is configured for the selected generation model.
    """
    _CAPITALS = {
        "france": "Paris",
        "germany": "Berlin",
        "spain": "Madrid",
        "italy": "Rome",
        "united kingdom": "London",
        "uk": "London",
        "usa": "Washington, D.C.",
        "united states": "Washington, D.C.",
        "australia": "Canberra",
    }
    m = re.search(r"capital of ([a-zA-Z\s]+)", question.lower())
    if m:
        country = m.group(1).strip()
        capital = _CAPITALS.get(country)
        if capital:
            return f"The capital of {country.title()} is {capital}."
        return "I don't have that information right now."
    return "I couldn't determine an answer; please rephrase your question."


def _call_gemini_generate(question: str) -> Dict[str, Any]:
    """Call Gemini to generate an answer via the google-genai SDK.

    Returns a dict with answer_text, token_ids, logprobs, offsets, and metadata.
    Note: Gemini does not provide token-level logprobs in the same way as OpenAI.
    Raises if the API key is missing or the call fails.
    """
    response = genai_generate(
        model=GEMINI_MODEL_NAME,
        prompt=question,
        temperature=0.7,
        max_output_tokens=2048,
        thinking_budget=0,
    )

    if response is None:
        raise RuntimeError("GOOGLE_API_KEY not configured")

    # Extract the answer text
    answer_text = response.text or ""

    # Note: Gemini does not provide token-level logprobs in the same format as OpenAI
    # Return placeholder values for token metadata
    token_ids: List[int] = []
    token_logprobs: List[float] = []
    offsets: List[Tuple[int, int]] = []

    return {
        "answer_text": answer_text,
        "token_ids": token_ids,
        "logprobs": token_logprobs,
        "offsets": offsets,
        "generation_successful": True,
        "metadata": {
            "model": GEMINI_MODEL_NAME,
            "question": question,
            "api_key_present": True,
            "note": "Token logprobs not available from Gemini API",
            "thoughts_token_count": getattr(response.usage_metadata, "thoughts_token_count", None),
        },
    }


def generate_answer(question: str, generation_model: str = "gemini-2.5-flash") -> Dict[str, Any]:
    """Generate an LLM answer to the given question using the selected generation model.

    Supports Gemini (Google) and NVIDIA NIM (OpenAI-compatible, e.g. openai/gpt-oss-120b).
    If the required API key or library is missing, falls back to a deterministic
    placeholder answer.
    """
    model_key = generation_model.lower()
    # -------------------------------------------------
    # Gemini generation path
    # -------------------------------------------------
    if "gemini" in model_key:
        api_key = _get_google_api_key()
        if not api_key:
            # Fallback placeholder answer
            answer_text = _fallback_answer(question)
            print("[GEMINI CALL SKIPPED] GOOGLE_API_KEY not configured")
            return {
                "answer_text": answer_text,
                "token_ids": None,
                "logprobs": None,
                "offsets": None,
                "generation_successful": False,
                "metadata": {
                    "reason": "GOOGLE_API_KEY_not_configured",
                    "model": GEMINI_MODEL_NAME,
                    "question": question,
                },
            }
        try:
            return _call_gemini_generate(question)
        except Exception as e:
            # Provide a sentence fallback instead of None so the pipeline can extract claims
            print(f"[GEMINI CALL FAILED] {e!r}")
            fallback_text = _fallback_answer(question)
            return {
                "answer_text": fallback_text,
                "token_ids": None,
                "logprobs": None,
                "offsets": None,
                "generation_successful": False,
                "metadata": {
                    "reason": f"gemini_call_failed: {e}",
                    "model": GEMINI_MODEL_NAME,
                    "question": question,
                },
            }
    # -------------------------------------------------
    # NVIDIA NIM generation path (OpenAI-compatible endpoint)
    # Serves models like "openai/gpt-oss-120b". Triggered by "gpt", "nim",
    # or "nvidia" appearing in the requested model string.
    # -------------------------------------------------
    if "gpt" in model_key or "nim" in model_key or "nvidia" in model_key:
        try:
            from openai import OpenAI
        except Exception:
            print("[OPENAI PACKAGE NOT AVAILABLE]")
            return {
                "answer_text": None,
                "token_ids": None,
                "logprobs": None,
                "offsets": None,
                "generation_successful": False,
                "metadata": {
                    "reason": "openai_package_not_available",
                    "model": NVIDIA_NIM_MODEL_NAME,
                    "question": question,
                },
            }
        api_key = _get_nvidia_nim_api_key()
        if not api_key:
            print("[NVIDIA NIM CALL SKIPPED] NVIDIA_NIM_API not configured")
            return {
                "answer_text": None,
                "token_ids": None,
                "logprobs": None,
                "offsets": None,
                "generation_successful": False,
                "metadata": {
                    "reason": "NVIDIA_NIM_API_not_configured",
                    "model": NVIDIA_NIM_MODEL_NAME,
                    "question": question,
                },
            }
        try:
            client = OpenAI(api_key=api_key, base_url=NVIDIA_NIM_BASE_URL)
            response = client.chat.completions.create(
                model=NVIDIA_NIM_MODEL_NAME,
                messages=[{"role": "user", "content": question}],
                temperature=0.7,
                max_tokens=2048,
            )
            answer_text = response.choices[0].message.content.strip()
            return {
                "answer_text": answer_text,
                "token_ids": None,
                "logprobs": None,
                "offsets": None,
                "generation_successful": True,
                "metadata": {
                    "model": NVIDIA_NIM_MODEL_NAME,
                    "question": question,
                    "api_key_present": True,
                },
            }
        except Exception as e:
            print(f"[NVIDIA NIM CALL FAILED] {e!r}")
            return {
                "answer_text": None,
                "token_ids": None,
                "logprobs": None,
                "offsets": None,
                "generation_successful": False,
                "metadata": {
                    "reason": f"nvidia_nim_call_failed: {e}",
                    "model": NVIDIA_NIM_MODEL_NAME,
                    "question": question,
                },
            }
    # -------------------------------------------------
    # Unknown or unsupported generation model – fallback
    # -------------------------------------------------
    print(f"[UNSUPPORTED GENERATION MODEL] {generation_model!r}")
    answer_text = None
    return {
        "answer_text": answer_text,
        "token_ids": None,
        "logprobs": None,
        "offsets": None,
        "generation_successful": False,
        "metadata": {
            "reason": "unsupported_generation_model",
            "model": generation_model,
            "question": question,
        },
    }
