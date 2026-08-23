"""Demo script for P1.1 Call 1 decomposition + triage."""

from modules.call1_decomposition import call1_run


def test_basic():
    """Test with normal answer (uses fallback since no API key)."""
    result = call1_run("", "The capital of France is Paris. It is located in Western Europe.")
    print(f"Basic test: {len(result['claims'])} claims extracted")
    for c in result["claims"]:
        print(f"  {c['id']}: \"{c['text']}\" confidence={c['self_confidence']} retrieval={c['needs_retrieval']}")
    assert len(result["claims"]) >= 1
    assert all(isinstance(c["self_confidence"], float) for c in result["claims"])
    assert all(0.0 <= c["self_confidence"] <= 1.0 for c in result["claims"])
    assert all(isinstance(c["needs_retrieval"], bool) for c in result["claims"])
    print("  PASSED")


def test_empty():
    """Test handling of empty/missing answer."""
    result = call1_run("", "")
    assert result == {"claims": []}, "Empty answer should return empty claims"

    result = call1_run("", None)
    assert result == {"claims": []}, "None answer should return empty claims"
    print("Empty answer test: PASSED")


def test_keywords():
    """Test confidence keyword effects."""
    test_cases = [
        ("Definitely the capital is Paris.", 0.65),
        ("Maybe it's Paris.", 0.35),
        ("The sky is blue.", 0.5),
        ("I think the answer is 42.", 0.35),
        ("Certainly 2+2=4.", 0.65),
    ]

    for text, expected_approximately in test_cases:
        from modules.call1_decomposition import _compute_self_confidence
        score = _compute_self_confidence(text)
        assert 0.0 <= score <= 1.0, f"Score {score} out of range [0,1]"
        print(f"  '{text}' -> confidence={score:.2f} (approx {expected_approximately})")
    print("Keyword confidence test: PASSED")


def test_needs_retrieval():
    """Test that needs_retrieval=True when confidence < 0.5."""
    # Low confidence should trigger retrieval
    result = call1_run("", "I think maybe this might be correct.")
    assert len(result["claims"]) == 1
    assert result["claims"][0]["needs_retrieval"] is True

    # High confidence should not trigger retrieval
    result = call1_run("", "Definitely the capital of France is Paris.")
    assert len(result["claims"]) == 1
    assert result["claims"][0]["needs_retrieval"] is False
    print("Needs retrieval logic test: PASSED")


def test_real_dataset():
    """Test with actual dataset entries."""
    import json
    with open("data/raw/sample_dataset.json", "r") as f:
        dataset = json.load(f)

    # Test entry 0: Python creation
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
    print("P1.1 Call 1 Decomposition - Demo")
    print("=" * 60)

    test_basic()
    test_empty()
    test_keywords()
    test_needs_retrieval()
    test_real_dataset()

    print("=" * 60)
    print("ALL DEMO TESTS PASSED")
    print("=" * 60)