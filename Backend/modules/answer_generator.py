"""Answer generation module — responsible for generating original LLM answers.

This module is designed to be independent from the decomposition pipeline
(modules.call1_decomposition). It produces the original LLM answer together
with token-level metadata required by P1.2 (token logprob entropy computation).

The interface is deliberately structured so that the returned dict always has
the same keys, even when the real LLM is not configured.  This allows Call 1
and other consumers to always rely on a consistent interface without None-
checking for every field.

Typical call sequence (outside this project):
    1. Original LLM call (e.g., Gemini 3.1 Pro) with logprobs if available.
    2. Result stored alongside the answer text as token_ids, logprobs, offsets.
    3. `generate_answer()` is called with the question; the stored metadata
       is returned so Call 1 can compute avg logprob per claim.

Note: The current project has no Google API key configured and the
pre-generated answers in data/raw/sample_dataset.json are plain strings
without token metadata.  Running `generate_answer()` without an API key
will return a structured placeholder indicating the limitation.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()


def _get_google_api_key() -> Optional[str]:
    """Read the Google API key from the environment; never hard-code it."""
    return os.getenv("GOOGLE_API_KEY")


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
    """Call Gemini to generate an answer.

    Returns a dict with answer_text, token_ids, logprobs, offsets, and metadata.
    Note: Gemini does not provide token-level logprobs in the same way as OpenAI.
    Raises if the API key is missing or the call fails.
    """
    import google.generativeai as genai

    api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel('gemini-3.1-pro')

    response = model.generate_content(
        question,
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 500,
        }
    )

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
            "model": "gemini-3.1-pro",
            "question": question,
            "api_key_present": True,
            "note": "Token logprobs not available from Gemini API",
        },
    }


def generate_answer(question: str, generation_model: str = "gemini-2-5-pro") -> Dict[str, Any]:
    """Generate an LLM answer to the given question using the selected generation model.

    Supports Gemini (Google) and ChatGPT (OpenAI). If the required API key or library
    is missing, falls back to a deterministic placeholder answer.
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
            return {
                "answer_text": answer_text,
                "token_ids": None,
                "logprobs": None,
                "offsets": None,
                "generation_successful": False,
                "metadata": {
                    "reason": "GOOGLE_API_KEY_not_configured",
                    "model": "gemini-3.1-pro",
                    "question": question,
                },
            }
        try:
            return _call_gemini_generate(question)
        except Exception as e:
            # Provide a sentence fallback instead of None so the pipeline can extract claims
            fallback_text = _fallback_answer(question)
            return {
                "answer_text": fallback_text,
                "token_ids": None,
                "logprobs": None,
                "offsets": None,
                "generation_successful": False,
                "metadata": {
                    "reason": f"gemini_call_failed: {e}",
                    "model": "gemini-3.1-pro",
                    "question": question,
                },
            }
    # -------------------------------------------------
    # ChatGPT / OpenAI generation path
    # -------------------------------------------------
    if "chatgpt" in model_key or "gpt" in model_key:
        try:
            import openai
        except Exception:
            answer_text = None
            return {
                "answer_text": answer_text,
                "token_ids": None,
                "logprobs": None,
                "offsets": None,
                "generation_successful": False,
                "metadata": {
                    "reason": "openai_package_not_available",
                    "model": "chatgpt-4o",
                    "question": question,
                },
            }
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            answer_text = None
            return {
                "answer_text": answer_text,
                "token_ids": None,
                "logprobs": None,
                "offsets": None,
                "generation_successful": False,
                "metadata": {
                    "reason": "OPENAI_API_KEY_not_configured",
                    "model": "chatgpt-4o",
                    "question": question,
                },
            }
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": question}],
                temperature=0.7,
                max_tokens=500,
            )
            answer_text = response.choices[0].message.content.strip()
            return {
                "answer_text": answer_text,
                "token_ids": None,
                "logprobs": None,
                "offsets": None,
                "generation_successful": True,
                "metadata": {
                    "model": "chatgpt-4o",
                    "question": question,
                    "api_key_present": True,
                },
            }
        except Exception as e:
            return {
                "answer_text": None,
                "token_ids": None,
                "logprobs": None,
                "offsets": None,
                "generation_successful": False,
                "metadata": {
                    "reason": f"openai_call_failed: {e}",
                    "model": "chatgpt-4o",
                    "question": question,
                },
            }
    # -------------------------------------------------
    # Unknown or unsupported generation model – fallback
    # -------------------------------------------------
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

    try:
        return _call_gemini_generate(question)
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
                "reason": f"gemini_call_failed: {e}",
                "model": "gemini-3.1-pro",
                "question": question,
            },
        }