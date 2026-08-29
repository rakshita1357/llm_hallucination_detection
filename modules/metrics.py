"""Simple metrics tracking for Phase 4 P4.3.
Tracks:
* Number of LLM calls (Call 1 and Call 2)
* Number of retrieval queries performed
* Estimated cost based on a fixed per-call price (placeholder)
"""

# Counter globals – reset per request by calling reset()
from typing import List, Dict
llm_calls: int = 0
retrieval_calls: int = 0

# Total latency (seconds) of LLM calls for the current request
total_latency: float = 0.0

# Count of escalated claims for the current request
escalated_claims: int = 0

# Placeholder cost settings – these can be tuned to reflect real pricing.
COST_PER_LLM_CALL_USD: float = 0.0001  # example cost per Gemini call
COST_PER_RETRIEVAL_USD: float = 0.0   # retrieval in this prototype is free

def reset() -> None:
    """Reset all counters to zero. Call at the start of each pipeline run."""
    global llm_calls, retrieval_calls, total_latency, escalated_claims
    llm_calls = 0
    retrieval_calls = 0
    total_latency = 0.0
    escalated_claims = 0

def increment_llm_calls() -> None:
    global llm_calls
    llm_calls += 1

def increment_retrieval_calls() -> None:
    global retrieval_calls
    retrieval_calls += 1

def increment_escalated_claims(num: int = 1) -> None:
    global escalated_claims
    escalated_claims += num
    # No side‑effect on retrieval count

def estimate_cost() -> float:
    """Return the estimated total cost in USD based on counters and placeholders."""
    return llm_calls * COST_PER_LLM_CALL_USD + retrieval_calls * COST_PER_RETRIEVAL_USD

def add_latency(seconds: float) -> None:
    global total_latency
    total_latency += seconds

def get_total_latency() -> float:
    return total_latency

# Simple in‑memory history of past runs (not persisted across restarts)
_history: List[Dict] = []

def record_history(entry: Dict) -> None:
    _history.append(entry)

def get_history() -> List[Dict]:
    return list(_history)