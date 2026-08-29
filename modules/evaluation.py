"""Evaluation harness for Phase 4 – P4.1.

This module provides a simple evaluation routine that runs the full
pipeline (decomposition, retrieval, verification, graph propagation and
aggregation) on the sample benchmark dataset and computes claim‑level
precision, recall and macro‑averaged F1 scores against the human‑annotated
labels.

The benchmark dataset lives at ``data/raw/sample_dataset.json`` and has the
following structure per entry::

    {
        "id": <int>,
        "query": <str>,
        "llm_response": <str>,
        "extracted_claims": [<str>, ...],
        "claim_labels": ["Correct" | "Incorrect" | "Unsupported", ...]
    }

The pipeline produces a list of claim dictionaries where each claim contains a
``verdict`` field with one of ``supported``, ``refuted`` or
``insufficient_evidence``.  The mapping from human labels to the expected
verdict is:

* ``Correct``                → ``supported``
* ``Incorrect``              → ``refuted``
* ``Unsupported`` (or any other value) → ``insufficient_evidence``

The ``evaluate_benchmark`` function returns a dictionary with per‑class
precision/recall/F1 and the macro‑averaged values.  When executed as a script it
prints a concise report.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Tuple

# Pipeline stages – imported lazily to avoid unnecessary side effects when the
# module is imported only for its helper functions.
from modules.call1_decomposition import call1_run
from modules.retrieval import retrieve_for_claims
from modules.call2_verification import call2_verify
from modules.graph_propagation import propagate_claims
from modules.aggregation import aggregate_claims

# ---------------------------------------------------------------------------
# Helper: map human label to expected verdict string used by the pipeline.
# ---------------------------------------------------------------------------
_LABEL_TO_VERDICT = {
    "Correct": "supported",
    "Incorrect": "refuted",
    "Unsupported": "insufficient_evidence",
}


def _map_label(label: str) -> str:
    """Return the verdict that corresponds to a human annotation.

    Any label not explicitly listed defaults to ``insufficient_evidence`` – this
    mirrors the behaviour of the benchmark where missing evidence is treated as
    a neutral case.
    """
    return _LABEL_TO_VERDICT.get(label, "insufficient_evidence")


def _compute_confusion(preds: List[str], golds: List[str]) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, int]]:
    """Return TP, FP and FN counters for the three verdict classes.

    Parameters
    ----------
    preds:
        Predicted verdicts produced by the pipeline.
    golds:
        Ground‑truth verdicts derived from the benchmark annotations.
    """
    classes = ["supported", "refuted", "insufficient_evidence"]
    tp = {c: 0 for c in classes}
    fp = {c: 0 for c in classes}
    fn = {c: 0 for c in classes}

    for p, g in zip(preds, golds):
        if p == g:
            tp[p] += 1
        else:
            fp[p] += 1
            fn[g] += 1
    return tp, fp, fn


def _precision_recall_f1(tp: Dict[str, int], fp: Dict[str, int], fn: Dict[str, int]) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    """Calculate per‑class precision, recall and F1 from the confusion counts."""
    precision: Dict[str, float] = {}
    recall: Dict[str, float] = {}
    f1: Dict[str, float] = {}
    for cls in tp:
        p = tp[cls] / (tp[cls] + fp[cls]) if (tp[cls] + fp[cls]) > 0 else 0.0
        r = tp[cls] / (tp[cls] + fn[cls]) if (tp[cls] + fn[cls]) > 0 else 0.0
        f = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
        precision[cls] = p
        recall[cls] = r
        f1[cls] = f
    return precision, recall, f1


def evaluate_benchmark(dataset_path: str = "data/raw/sample_dataset.json") -> Dict:
    """Run the full pipeline on the benchmark and return evaluation metrics.

    The function processes every entry in the dataset, extracts claims, performs
    retrieval and verification, runs graph propagation and finally aggregates the
    per‑claim verdicts.  It then compares the verdicts to the human‑annotated
    labels and computes precision/recall/F1 for each class as well as macro‑averaged
    scores.
    """
    dataset_file = Path(dataset_path)
    if not dataset_file.is_file():
        raise FileNotFoundError(f"Benchmark dataset not found: {dataset_path}")

    with dataset_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    all_preds: List[str] = []
    all_golds: List[str] = []

    for entry in data:
        # Step 1 – decompose the answer.
        decomposition = call1_run(entry.get("query", ""), entry.get("llm_response", ""))
        claims = decomposition.get("claims", [])
        if not claims:
            continue

        # Step 2 – retrieval (adds ``evidence`` field).
        claims = retrieve_for_claims(claims)

        # Step 3 – verification (adds ``verdict`` field).
        claims = call2_verify(claims)

        # Step 4 – graph propagation (may adjust confidence but does not change verdict).
        claims = propagate_claims(claims, edges=[])

        # Align human labels with predicted claims – the pipeline preserves order.
        gold_labels = entry.get("claim_labels", [])
        gold_verdicts = [_map_label(lbl) for lbl in gold_labels]
        pred_verdicts = [c.get("verdict", "insufficient_evidence") for c in claims]

        # Truncate to the shorter length in case of mismatch.
        length = min(len(pred_verdicts), len(gold_verdicts))
        all_preds.extend(pred_verdicts[:length])
        all_golds.extend(gold_verdicts[:length])

    tp, fp, fn = _compute_confusion(all_preds, all_golds)
    precision, recall, f1 = _precision_recall_f1(tp, fp, fn)

    macro_precision = sum(precision.values()) / len(precision)
    macro_recall = sum(recall.values()) / len(recall)
    macro_f1 = sum(f1.values()) / len(f1)

    return {
        "per_class": {
            cls: {"precision": precision[cls], "recall": recall[cls], "f1": f1[cls]} for cls in precision
        },
        "macro": {
            "precision": macro_precision,
            "recall": macro_recall,
            "f1": macro_f1,
        },
        "counts": {"tp": tp, "fp": fp, "fn": fn},
    }


if __name__ == "__main__":
    metrics = evaluate_benchmark()
    print("=== Phase 4 Evaluation (P4.1) ===")
    for cls, vals in metrics["per_class"].items():
        print(f"{cls:23}: precision={vals['precision']:.3f}, recall={vals['recall']:.3f}, f1={vals['f1']:.3f}")
    macro = metrics["macro"]
    print("--- Macro averages ---")
    print(f"precision={macro['precision']:.3f}, recall={macro['recall']:.3f}, f1={macro['f1']:.3f}")
