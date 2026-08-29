"""Main module for the Hallucination Detection Engine.

* When executed directly, it loads the sample dataset, extracts atomic claims using
  ``modules.atomic_claim_extractor`` and writes the result to ``data/processed``.
* It also hosts a FastAPI application exposing the full Phase 1 pipeline via the
  ``/pipeline`` endpoint.

The Gemini model used throughout the pipeline is ``gemini-3.1-pro`` (the
fallback implementation works without an API key)."""

import pandas as pd
from modules.atomic_claim_extractor import extract_atomic_claims

# ---------------------------------------------------------------------------
# Dataset processing (original script behavior)
# ---------------------------------------------------------------------------

def _process_dataset():
    """Load the raw dataset, extract atomic claims, and write the processed file.

    This function is called when the module is run as a script. Keeping it in a
    function prevents the heavy I/O from executing on import (e.g., when the
    FastAPI app is started with ``uvicorn main:app``).
    """
    df = pd.read_json("data/raw/sample_dataset.json")
    df["atomic_claims"] = df["llm_response"].apply(extract_atomic_claims)
    df.to_json(
        "data/processed/atomic_claims_dataset.json",
        orient="records",
        indent=4,
    )
    print("Atomic claim extraction completed!")

# ---------------------------------------------------------------------------
# FastAPI application exposing the Phase 1 pipeline
# ---------------------------------------------------------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict

from modules.call1_decomposition import call1_run
from modules.retrieval import retrieve_for_claims
from modules.call2_verification import call2_verify
from modules.aggregation import aggregate_claims
# Phase‑2 utilities
from modules.claim_pair_similarity import compute_claim_pair_similarities
from modules.nli_cross_encoder import run_nli_on_claim_pairs
from modules.graph_propagation import propagate_claims
from modules.residual_claims import identify_residual_claims

app = FastAPI()
# Enable CORS for the frontend (development) and any origin in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve built frontend assets when running in production.
# The Vite build output lives in `frontend/dist`. If the directory does not exist,
# this mount is harmless – FastAPI will simply ignore missing files.
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")

class PipelineRequest(BaseModel):
    question: str
    answer_text: str

class PipelineResponse(BaseModel):
    aggregate_confidence: float
    report: list
    residual_claims: list

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/pipeline", response_model=PipelineResponse)
def run_pipeline(request: PipelineRequest):
    # Step 1: Decompose and triage (Call 1)
    decomposition = call1_run(request.question, request.answer_text)
    claims = decomposition.get("claims", [])

    # Step 2: Retrieval (adds ``evidence`` field)
    claims = retrieve_for_claims(claims)

    # Step 3: Batched verification (adds ``verdict`` field)
    claims = call2_verify(claims)

    # -------------------------------------------------------------
    # Phase 2 – graph‑aware enrichment
    # -------------------------------------------------------------
    # 2.1 Compute claim‑pair similarities (embedding + entity overlap)
    similar_pairs = compute_claim_pair_similarities(claims, similarity_threshold=0.8)

    # 2.2 Run local NLI on the similar pairs
    nli_inputs = [
        {
            "claim1_id": pair["claim1_id"],
            "claim1_text": next(c["text"] for c in claims if c["id"] == pair["claim1_id"]),
            "claim2_id": pair["claim2_id"],
            "claim2_text": next(c["text"] for c in claims if c["id"] == pair["claim2_id"]),
        }
        for pair in similar_pairs
    ]
    nli_results = run_nli_on_claim_pairs(nli_inputs)

    # 2.3 Build an edge list from NLI results
    edges = []
    for res in nli_results:
        if res["nli"] == "supports":
            edge_type = "depends_on"
        elif res["nli"] == "contradicts":
            edge_type = "contradicts"
        else:
            continue
        edges.append({
            "source_id": res["claim1_id"],
            "target_id": res["claim2_id"],
            "type": edge_type,
        })

    # 2.4 Graph propagation – adjust confidence and flag internal contradictions
    claims = propagate_claims(claims, edges)

    # -------------------------------------------------------------
    # Phase 1 aggregation (now enriched with graph data)
    # -------------------------------------------------------------
    aggregation = aggregate_claims(claims)

    # Enrich the aggregation report with the extra fields for the frontend
    enriched_report = []
    for entry in aggregation["report"]:
        full_claim = next(c for c in claims if c["id"] == entry["id"])
        entry["effective_confidence"] = full_claim.get("effective_confidence", entry["score"])
        if full_claim.get("internal_consistency_failure"):
            entry["internal_consistency_failure"] = True
        enriched_report.append(entry)

    return {
        "aggregate_confidence": aggregation["aggregate_confidence"],
        "report": enriched_report,
    }

# ---------------------------------------------------------------------------
from modules.escalation import escalate_residual_claims
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # When run directly, first process the dataset then start the API server.
    _process_dataset()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
