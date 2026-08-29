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
from pydantic import BaseModel

from modules.call1_decomposition import call1_run
from modules.retrieval import retrieve_for_claims
from modules.call2_verification import call2_verify
from modules.aggregation import aggregate_claims

app = FastAPI()

class PipelineRequest(BaseModel):
    question: str
    answer_text: str

class PipelineResponse(BaseModel):
    aggregate_confidence: float
    report: list

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/pipeline", response_model=PipelineResponse)
def run_pipeline(request: PipelineRequest):
    # Step 1: Decompose and triage
    decomposition = call1_run(request.question, request.answer_text)
    claims = decomposition.get("claims", [])

    # Step 2: Retrieval (adds ``evidence`` field)
    claims = retrieve_for_claims(claims)

    # Step 3: Batched verification (adds ``verdict`` field)
    claims = call2_verify(claims)

    # Step 4: Naïve aggregation
    result = aggregate_claims(claims)

    return {
        "aggregate_confidence": result["aggregate_confidence"],
        "report": result["report"],
    }

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # When run directly, first process the dataset then start the API server.
    _process_dataset()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
