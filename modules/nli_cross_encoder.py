"""Local cross‑encoder NLI model (Phase 2 – P2.2).

This module provides a pure‑Python, locally‑hosted NLI inference utility that
operates without any external LLM API calls. It uses the ``sentence‑transformers``
``CrossEncoder`` class with a pre‑trained NLI model (``cross-encoder/nli-roberta-
base``) to predict whether one claim *supports* another, *contradicts* it, or
is *neutral*.

The public function ``run_nli_on_claim_pairs`` expects a list of dictionaries
each containing the following keys:

* ``claim1_id`` – identifier of the source claim (premise)
* ``claim1_text`` – text of the source claim
* ``claim2_id`` – identifier of the target claim (hypothesis)
* ``claim2_text`` – text of the target claim

It returns a list of dictionaries with the original ids and an ``nli`` field that
holds one of ``"supports"``, ``"contradicts"`` or ``"neutral"``. The function
falls back gracefully when the ``sentence‑transformers`` library or the model
cannot be loaded – in that case all pairs are marked ``"neutral"``.
"""

from __future__ import annotations

from typing import List, Dict

# ---------------------------------------------------------------------------
# Lazy import – ``sentence_transformers`` is optional for environments where
# the heavy model cannot be downloaded. The module will still be importable and
# will simply return ``neutral`` for every pair if the library is missing.
# ---------------------------------------------------------------------------
try:
    from sentence_transformers import CrossEncoder
    _HAS_CROSS_ENCODER = True
except Exception:  # pragma: no cover
    _HAS_CROSS_ENCODER = False

_cross_encoder = None


def _get_cross_encoder() -> "CrossEncoder | None":
    """Lazy‑initialise the cross‑encoder NLI model.

    The model is downloaded on first use and cached by ``sentence‑transformers``.
    If the library is unavailable, ``None`` is returned.
    """
    global _cross_encoder
    if _cross_encoder is None and _HAS_CROSS_ENCODER:
        # ``cross-encoder/nli-roberta-base`` is a compact, high‑quality NLI model.
        _cross_encoder = CrossEncoder("cross-encoder/nli-roberta-base")
    return _cross_encoder


def _classify_score(score: float, support_thr: float = 0.5, contradict_thr: float = 0.1) -> str:
    """Map a raw cross‑encoder score to a textual NLI label.

    ``cross-encoder/nli-roberta-base`` produces higher scores for the *entailment*
    class. Empirically, scores above ~0.5 are strong entailments, while scores
    below ~0.1 tend to correlate with *contradiction*. Values in‑between are
    treated as ``neutral``.
    """
    if score >= support_thr:
        return "supports"
    if score <= contradict_thr:
        return "contradicts"
    return "neutral"


def run_nli_on_claim_pairs(
    claim_pairs: List[Dict],
    support_threshold: float = 0.5,
    contradict_threshold: float = 0.1,
) -> List[Dict]:
    """Run a local NLI model on a list of claim pairs.

    Parameters
    ----------
    claim_pairs:
        List of dictionaries. Each dictionary must contain the keys
        ``"claim1_id"``, ``"claim1_text"``, ``"claim2_id"`` and ``"claim2_text"``.
    support_threshold:
        Score at or above which the pair is considered ``"supports"``.
    contradict_threshold:
        Score at or below which the pair is considered ``"contradicts"``.

    Returns
    -------
    List[Dict]
        Each result dictionary contains ``claim1_id``, ``claim2_id`` and an ``nli``
        field with one of ``"supports"``, ``"contradicts"`` or ``"neutral"``.
        If the cross‑encoder model cannot be loaded, all pairs are returned as
        ``"neutral"``.
    """
    if not claim_pairs:
        return []

    model = _get_cross_encoder()
    if model is None:
        # Graceful fallback – no NLI model available.
        return [
            {
                "claim1_id": cp.get("claim1_id"),
                "claim2_id": cp.get("claim2_id"),
                "nli": "neutral",
            }
            for cp in claim_pairs
        ]

    # Prepare input for the cross‑encoder: each entry is a [premise, hypothesis]
    # pair. We treat ``claim1`` as the premise and ``claim2`` as the hypothesis.
    inputs = [[cp["claim1_text"], cp["claim2_text"]] for cp in claim_pairs]
    scores = model.predict(inputs)

    # ``scores`` is an array of shape (batch, 3) – one score per NLI class
    # (contradiction, neutral, entailment). We select the class with the highest
    # score for each pair.
    label_map = {0: "contradicts", 1: "neutral", 2: "supports"}

    results: List[Dict] = []
    for cp, score_vec in zip(claim_pairs, scores):
        # Convert to NumPy array for uniform handling.
        import numpy as _np
        arr = _np.asarray(score_vec).ravel()
        if arr.size == 0:
            # Fallback – treat as neutral if no scores.
            label = "neutral"
        else:
            idx = int(_np.argmax(arr))
            label = label_map.get(idx, "neutral")
        results.append({
            "claim1_id": cp.get("claim1_id"),
            "claim2_id": cp.get("claim2_id"),
            "nli": label,
        })
    return results

# ---------------------------------------------------------------------------
# Simple CLI for ad‑hoc testing.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Run local NLI on claim pairs.")
    parser.add_argument("pairs_file", help="Path to JSON file containing a list of claim‑pair objects.")
    parser.add_argument("--support_thr", type=float, default=0.5, help="Score >= this is considered 'supports'.")
    parser.add_argument("--contradict_thr", type=float, default=0.1, help="Score <= this is considered 'contradicts'.")
    args = parser.parse_args()

    try:
        with open(args.pairs_file, "r", encoding="utf-8") as f:
            pairs = json.load(f)
    except Exception as exc:
        sys.stderr.write(f"Failed to load pairs file: {exc}\n")
        sys.exit(1)

    out = run_nli_on_claim_pairs(pairs, support_threshold=args.support_thr, contradict_threshold=args.contradict_thr)
    print(json.dumps(out, indent=2))
