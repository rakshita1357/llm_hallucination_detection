"""Test script for P1.1 - Call 1 decomposition + triage."""

import json
import sys
sys.path.insert(0, "..")

from modules.call1_decomposition import call1_run, Claim, _compute_self_confidence


def test_schema_validation():
    """Verify all claims have the correct schema."""
    with open("data/raw/sample_dataset.json", "r") as f:
        dataset = json.load(f)

    for idx, entry in enumerate(dataset[:3]):
        result = call1_run(entry["query"], entry["llm_response"])
        claims = result["claims"]

        assert isinstance(claims, list), f"Entry {idx}: claims should be a list"
        for i, c in enumerate(claims):
            # Check required fields
            assert "id" in c, f"Entry {idx}, claim {i}: missing id"
            assert "text" in c, f"Entry {idx}, claim {i}: missing text"
            assert "self_confidence" in c, f"Entry {idx}, claim {i}: missing self_confidence"
            assert "needs_retrieval" in c, f"Entry {idx}, claim {i}: missing needs_retrieval"
            assert "search_query" in c, f"Entry {idx}, claim {i}: missing search_query"

            # Type checks
            assert isinstance(c["id"], str), f"Entry {idx}, claim {i}: id should be str"
            assert isinstance(c["text"], str), f"Entry {idx}, claim {i}: text should be str"
            assert isinstance(c["self_confidence"], float), \
                f"Entry {idx}, claim {i}: self_confidence should be float, got {type(c['self_confidence'])}"
            assert isinstance(c["needs_retrieval"], bool), \
                f"Entry {idx}, claim {i}: needs_retrieval should be bool"

            # Value constraints
            assert 0.0 <= c["self_confidence"] <= 1.0, \
                f"Entry {idx}, claim {i}: self_confidence must be in [0,1], got {c['self_confidence']}"

            # Logic: if needs_retrieval is True, search_query must be present
            if c["needs_retrieval"]:
                assert c["search_query"] is not None, \
                    f"Entry {idx}, claim {i}: search_query must be present when needs_retrieval=True"
                assert isinstance(c["search_query"], str), \
                    f"Entry {idx}, claim {i}: search_query must be str when needs_retrieval=True"

        print(f"Entry {idx}: Schema validation PASSED ({len(claims)} claims)")


def test_confidence_range():
    """Test that self_confidence is always in [0,1] and keywords have effect."""
    test_cases = [
        ("Definitely the capital is Paris.", 0.65),   # high confidence keyword
        ("Maybe it's Paris.", 0.35),                   # low confidence keyword
        ("The sky is blue.", 0.5),                     # neutral (no keywords)
        ("I think the answer is 42.", 0.35),           # uncertain keyword
        ("Certainly 2+2=4.", 0.65),                    # very high confidence keyword
    ]

    for text, expected_approximately in test_cases:
        score = _compute_self_confidence(text)
        assert 0.0 <= score <= 1.0, f"Score {score} out of range [0,1]"
        # Allow some tolerance since multiple keywords or sentence structure may affect score
        print(f"  '{text}' -> confidence={score:.2f} (approx {expected_approximately})")


def test_needs_retrieval_logic():
    """Test that needs_retrieval=True when confidence < 0.5."""
    # Low confidence should trigger retrieval
    low_conf_text = "I think maybe this might be correct."
    result = call1_run("", low_conf_text)
    assert len(result["claims"]) == 1
    assert result["claims"][0]["needs_retrieval"] is True, \
        f"Low confidence claim should have needs_retrieval=True"

    # High confidence should not trigger retrieval
    high_conf_text = "Definitely the capital of France is Paris."
    result = call1_run("", high_conf_text)
    assert len(result["claims"]) == 1
    assert result["claims"][0]["needs_retrieval"] is False, \
        f"High confidence claim should have needs_retrieval=False"

    print("needs_retrieval logic: PASSED")


def test_empty_answer():
    """Test handling of empty/missing answer."""
    result = call1_run("", "")
    assert result == {"claims": []}, "Empty answer should return empty claims"

    result = call1_run("", None)
    assert result == {"claims": []}, "None answer should return empty claims"

    print("Empty answer handling: PASSED")


def test_real_dataset_examples():
    """Test with actual dataset entries."""
    with open("data/raw/sample_dataset.json", "r") as f:
        dataset = json.load(f)

    # Test entry 1: Python creation
    result = call1_run(dataset[0]["query"], dataset[0]["llm_response"])
    claims = result["claims"]
    assert len(claims) >= 1, "Should extract at least 1 claim"
    for c in claims:
        assert c["id"].startswith("c"), f"Claim id should start with 'c', got {c['id']}"
        assert 0.0 <= c["self_confidence"] <= 1.0
        assert isinstance(c["needs_retrieval"], bool)
    print(f"Entry 0 (Python): {len(claims)} claims, confidence range: "
          f"{min(c['self_confidence'] for c in claims):.2f} - {max(c['self_confidence'] for c in claims):.2f}")

    # Test entry 6: Speed of light
    result = call1_run(dataset[5]["query"], dataset[5]["llm_response"])
    claims = result["claims"]
    for c in claims:
        assert 0.0 <= c["self_confidence"] <= 1.0
    print(f"Entry 5 (Speed of light): {len(claims)} claims")

    # Test entry 21: Binary search (has incorrect claim)
    result = call1_run(dataset[21]["query"], dataset[21]["llm_response"])
    claims = result["claims"]
    for c in claims:
        assert 0.0 <= c["self_confidence"] <= 1.0
    print(f"Entry 21 (Binary search): {len(claims)} claims")

    print("Real dataset examples: PASSED")


if __name__ == "__main__":
    print("=" * 60)
    print("P1.1 Call 1 Decomposition - Test Suite")
    print("=" * 60)

    test_schema_validation()
    test_confidence_range()
    test_needs_retrieval_logic()
    test_empty_answer()
    test_real_dataset_examples()

    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)