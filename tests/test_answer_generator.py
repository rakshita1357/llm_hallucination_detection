"""Unit tests for modules.answer_generator — interface only.

These tests DO NOT require a real Google API key.  They verify the function
returns a dict with the expected keys and that the no-key path is handled
correctly without making any API calls.
"""

import sys
import os

# Ensure the project root (current directory) is on the path so we can import modules
sys.path.insert(0, ".")

# IMPORTANT: This test must not make real API calls.  Unset the key before importing.
os.environ.pop("GOOGLE_API_KEY", None)

from Backend.modules import generate_answer


def test_interface_returns_correct_keys():
    """Verify generate_answer always returns a dict with the same keys."""
    # No API key should be configured; the function must not crash.
    # Explicitly ensure no key is present so we test the no-key path.
    os.environ.pop("GOOGLE_API_KEY", None)
    result = generate_answer("What is the capital of France?")

    # Type check
    assert isinstance(result, dict), "generate_answer must return a dict"

    # Fixed set of keys — always present, regardless of configuration
    expected_keys = {
        "answer_text",
        "token_ids",
        "logprobs",
        "offsets",
        "generation_successful",
        "metadata",
    }
    actual_keys = set(result.keys())
    assert actual_keys == expected_keys, (
        f"Expected keys {expected_keys}, got {actual_keys}. "
        f"Got: {result}"
    )

    # Token-related fields should be None when no API key
    assert isinstance(result["answer_text"], str), (
        f"answer_text should be a string when no API key, got {result['answer_text']}"
    )
    assert result["answer_text"] != "", "answer_text should not be empty"
    assert result["token_ids"] is None, (
        f"token_ids should be None when no API key, got {result['token_ids']}"
    )
    assert result["logprobs"] is None, (
        f"logprobs should be None when no API key, got {result['logprobs']}"
    )
    assert result["offsets"] is None, (
        f"offsets should be None when no API key, got {result['offsets']}"
    )

    # generation_successful should be False
    assert result["generation_successful"] is False, (
        f"generation_successful should be False when no API key, "
        f"got {result['generation_successful']}"
    )

    # metadata should explain the limitation
    assert "reason" in result["metadata"], (
        "metadata must contain 'reason' key when API key is missing"
    )
    assert result["metadata"]["reason"] == "GOOGLE_API_KEY_not_configured", (
        f"Expected reason='GOOGLE_API_KEY_not_configured', "
        f"got '{result['metadata']['reason']}'"
    )

    print("test_interface_returns_correct_keys: PASSED")


def test_no_api_key_no_real_call():
    """Verify that without GOOGLE_API_KEY, no real API call is made.

    This is a best-effort check: we clear the env var, call the function,
    and assert the result has the expected placeholder structure.
    """
    # Ensure the key is definitely not set
    os.environ.pop("GOOGLE_API_KEY", None)

    result = generate_answer("Test question for no-key path")

    assert result["generation_successful"] is False
    assert isinstance(result["answer_text"], str)
    assert result["answer_text"] != ""
    assert result["token_ids"] is None
    assert result["logprobs"] is None
    assert result["offsets"] is None
    assert result["metadata"]["reason"] == "GOOGLE_API_KEY_not_configured"

    print("test_no_api_key_no_real_call: PASSED")


if __name__ == "__main__":
    print("=" * 60)
    print("P1.2 Answer Generator - Interface Tests")
    print("=" * 60)

    test_interface_returns_correct_keys()
    test_no_api_key_no_real_call()

    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)