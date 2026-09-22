"""Backend modules package for SkepticAI.

This package exposes the core pipeline functions for the hallucination detection engine.
"""

# Answer generation
from Backend.modules.answer_generator import generate_answer

# Atomic claim extraction
from Backend.modules.atomic_claim_extractor import extract_atomic_claims

# Call 1 - Claim decomposition
from Backend.modules.call1_decomposition import call1_run

# Retrieval
from Backend.modules.retrieval import retrieve_for_claims

# Verification
from Backend.modules.openrouter_verification import (
    verify_claims,
    VERIFICATION_MODEL_IDS,
)

# Aggregation
from Backend.modules.aggregation import aggregate_claims

# Phase 2 - Claim pair similarity
from Backend.modules.claim_pair_similarity import compute_claim_pair_similarities

# Phase 2 - Graph propagation
from Backend.modules.graph_propagation import propagate_claims

# NLI Cross-encoder
from Backend.modules.nli_cross_encoder import run_nli_on_claim_pairs

# Residual detection and escalation
from Backend.modules.residual_claims import identify_residual_claims
from Backend.modules.escalation import escalate_residual_claims

# Metrics (module)
from Backend.modules import metrics

# OpenRouter client
from Backend.modules.openrouter_client import call_model

# Call 2 verification internals
from Backend.modules.call2_verification import _SYSTEM_PROMPT, _format_claim_batch

__all__ = [
    # Answer generation
    "generate_answer",
    # Atomic claim extraction
    "extract_atomic_claims",
    # Call 1
    "call1_run",
    # Retrieval
    "retrieve_for_claims",
    # Verification
    "verify_claims",
    "VERIFICATION_MODEL_IDS",
    # Aggregation
    "aggregate_claims",
    # Phase 2 - Claim pair similarity
    "compute_claim_pair_similarities",
    # Phase 2 - Graph propagation
    "propagate_claims",
    # NLI
    "run_nli_on_claim_pairs",
    # Residual/Escalation
    "identify_residual_claims",
    "escalate_residual_claims",
    # Metrics
    "metrics",
    # OpenRouter
    "call_model",
    # Call 2 internals
    "_SYSTEM_PROMPT",
    "_format_claim_batch",
]