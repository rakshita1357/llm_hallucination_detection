# Task Plan: Hallucination Detection Engine

## Phase 1 — MVP Core Loop ✅ Validate the 2-call cost claim end-to-end with minimal local processing.

### Sub-tasks:
- **P1.1**: Implement Call 1 — decomposition + triage structured LLM prompt ✅
  - Parse LLM answer into atomic claims with `id`, `text`, `self_confidence`, `needs_retrieval`, `search_query`
  - Output JSON structured claims list with strict schema validation
  - Module: `modules/call1_decomposition.py` — LLM call isolated in `call1_run()`, falls back to rule-based heuristic if no API key
  - Test: `test_p11.py`
  - LLM provider: Gemini 3.1 Pro, key read from `GOOGLE_API_KEY` environment variable
- **P1.2**: Implement free signal — token logprob entropy computation
  - Align claim text to token offsets
  - Compute average log-probability per claim
  - Flag claims with low logprob for retrieval override
- **P1.3**: Implement retrieval for flagged claims
  - Issue search queries for claims with `needs_retrieval: true`
  - Deduplicate queries by entity clustering
  - Cache results per session
- **P1.4**: Implement Call 2 — batched verification
  - Pack all retrieved claims into single structured LLM call
  - Output verdicts: `supported`/`refuted`/`insufficient_evidence`
  - Hard cap of 20 claims per batch; split into multiple passes if needed
- **P1.5**: Implement naive aggregation
  - Aggregate per-claim verdicts into aggregate confidence score in [0,1]
  - Generate basic report with per-claim verdicts

### Deliverable:
End-to-end pipeline producing claim-level factuality report with exactly 2 LLM calls per answer (plus occasional batch splitting).

---

## Phase 2 — Graph Layer
Add local embedding-based edge filtering, NLI cross-encoder, and propagation logic.

### Sub-tasks:
- **P2.1**: Implement local sentence-embedding model for claim pairs
  - Compute pairwise similarity between claims
  - Filter to pairs above similarity threshold or same-entity claims (via lightweight NER)
- **P2.2**: Implement local cross-encoder NLI model
  - Run NLI on filtered claim pairs from Call 1
  - Refine/confirm `supports`/`contradicts` edges from Call 1's output
  - Must not require any LLM API call
- **P2.3**: Implement graph propagation logic
  - Traverse edge graph: if claim A is `refuted` and B has `depends_on` edge from B to A, downweight B's effective confidence
  - If two claims have `contradicts` edge and neither has external evidence, flag as internal-consistency failure
- **P2.4**: Validate against synthetic contradiction test set
  - Hand-crafted answers with internal contradictions but no external evidence
  - Verify graph propagation catches hallucinations retrieval-only pipelines miss

### Deliverable:
Pipeline with local graph-aware propagation improving recall on contradictory claims without additional LLM calls.

---

## Phase 3 — Bounded Escalation
Add residual-claim escalation with 15% cap and monitoring.

### Sub-tasks:
- **P3.1**: Implement residual-claim identification
  - After Call 2 + graph propagation, identify claims still `insufficient_evidence` near decision boundary
  - Flag contradictions with no clear resolution
- **P3.2**: Implement escalation logic
  - Escalate only the residual set to a second, independent model judge
  - Hard cap: if residual set exceeds ~15% of total claims, log warning
  - Model choice: different family/provider than Call 2 to avoid correlated blind spots
- **P3.3**: Implement monitoring and observability
  - Log call counts, retrieval counts, and escalation rate per answer
  - Track escalation rate as first-class metric
  - Alert if escalation rate trends above 15%

### Deliverable:
Pipeline with rare escalation calls (≤15% of claims) and monitoring proving the cost guarantee.

---

## Phase 4 — Evaluation Harness & Hardening
Full benchmark run, schema validation, and dashboards.

### Sub-tasks:
- **P4.1**: Implement evaluation benchmark against FActScore biography dataset
  - Report claim-level precision/recall vs. human-annotated benchmark
  - Target: within 3pts of naive per-claim baseline
- **P4.2**: Implement schema validation/retry logic for LLM calls
  - Both Call 1 and Call 2 must return validated structured output
  - Malformed output triggers single retry, not silent failure
- **P4.3**: Implement latency and cost tracking
  - Report LLM calls, retrieval calls, and wall-clock latency per answer
  - Target: <6s p50, <12s p95 for 200-word answer
  - Report cost per answer vs. naive baseline (≥60% reduction)
- **P4.4**: Build observability dashboards
  - Call counts per answer
  - Retrieval counts per answer
  - Escalation rate over time
  - Latency distributions

### Deliverable:
Complete system with evaluation harness, observability, and documented cost/accuracy tradeoffs ready for production use.