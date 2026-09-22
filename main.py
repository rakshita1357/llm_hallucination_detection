"""Main module for the Hallucination Detection Engine.

* When executed directly, it loads the sample dataset, extracts atomic claims using
  ``modules.atomic_claim_extractor`` and writes the result to ``data/processed``.
* It also hosts a FastAPI application exposing the full Phase 1 pipeline via the
  ``/pipeline`` endpoint.

The Gemini model used throughout the pipeline is ``gemini-2.5-flash`` (the
fallback implementation works without an API key)."""

import pandas as pd
from Backend.modules import extract_atomic_claims

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
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict
from fastapi.responses import HTMLResponse
from datetime import datetime
from Backend.modules import metrics

from Backend.modules import call1_run
from Backend.modules import retrieve_for_claims
from Backend.modules import verify_claims, VERIFICATION_MODEL_IDS
from Backend.modules import aggregate_claims
# Phase‑2 utilities
from Backend.modules import compute_claim_pair_similarities
from Backend.modules.nli_cross_encoder import run_nli_on_claim_pairs
from Backend.modules import propagate_claims
from Backend.modules import identify_residual_claims
from Backend.modules import escalate_residual_claims
# Answer generation
from Backend.modules import generate_answer
from Backend.modules import call_model
from Backend.modules import _SYSTEM_PROMPT, _format_claim_batch

# Auth
from Backend.auth import auth_router
from Backend.auth.utils import get_current_user, get_current_user_optional
from Backend.database.models import (
    User,
    MessageRole,
    VerificationStatus,
    ClaimVerdict,
    SourceType,
)
from Backend.database.repositories import (
    ChatSessionRepository,
    MessageRepository,
    VerificationReportRepository,
    VerificationClaimRepository,
    VerificationEvidenceRepository,
)
from Backend.database.connection import get_session
import uuid

# FastAPI app instance
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from Backend.database.connection import init_db, close_db
    init_db()
    yield
    # Shutdown
    await close_db()

app = FastAPI(lifespan=lifespan)

# Include auth router
app.include_router(auth_router)

# -----------------------
# New request model for the chat endpoint
class ChatRequest(BaseModel):
    prompt: str
    model: str | None = None
    attachments: List[Dict] = []
    history: List[Dict] = []

# -----------------------
# Response model for the chat endpoint
class ChatResponsePayload(BaseModel):
    answer: str
    confidence: float
    status: str
    findings: List[Dict] = []
    totalClaimsCount: int | None = None
    verifiedClaimsCount: int | None = None
    flaggedFindingsCount: int | None = None
    summary: str | None = None
    chatSessionId: str | None = None


async def _persist_chat_data(
    user_id: uuid.UUID,
    prompt: str,
    answer_text: str,
    model: str,
    claims: List[Dict],
    enriched_report: List[Dict],
    aggregate_conf: float,
    overall_status: str,
    findings: List[Dict],
    escalation_rate: float,
) -> uuid.UUID:
    """Persist chat session, messages, and verification report to database.
    
    Returns the chat session ID.
    """
    async with get_session() as session:
        chat_repo = ChatSessionRepository(session)
        msg_repo = MessageRepository(session)
        report_repo = VerificationReportRepository(session)
        claim_repo = VerificationClaimRepository(session)
        evidence_repo = VerificationEvidenceRepository(session)

        # Create or get a chat session (use a simple approach: create new session for each chat)
        # In a more sophisticated implementation, we'd reuse sessions based on context
        chat_session = await chat_repo.create(
            user_id=user_id,
            title=prompt[:50] + ("..." if len(prompt) > 50 else ""),
            selected_model=model,
        )

        # Save user message
        user_msg = await msg_repo.create(
            session_id=chat_session.id,
            role=MessageRole.USER,
            content=prompt,
            model=model,
        )

        # Save assistant message
        assistant_msg = await msg_repo.create(
            session_id=chat_session.id,
            role=MessageRole.ASSISTANT,
            content=answer_text,
            model=model,
        )

        # Create verification report
        hallucination_detected = overall_status in ("potential_hallucination", "partially_reliable")
        report = await report_repo.create(
            message_id=assistant_msg.id,
            confidence_score=aggregate_conf,
            hallucination_detected=hallucination_detected,
            status=VerificationStatus.COMPLETED,
            summary=f"Aggregated confidence {aggregate_conf:.2f} (escalation rate {escalation_rate:.2%})",
        )

        # Prepare claims data for bulk creation
        claims_data = []
        for entry in enriched_report:
            claim_id = entry["id"]
            full_claim = next((c for c in claims if c["id"] == claim_id), None)
            if full_claim is None:
                continue
            verdict_str = entry.get("verdict", "insufficient_evidence")
            verdict = ClaimVerdict.SUPPORTED if verdict_str == "supported" else (
                ClaimVerdict.REFUTED if verdict_str == "refuted" else ClaimVerdict.INSUFFICIENT_EVIDENCE
            )
            evidence_snippets = [e.get("snippet", "") for e in full_claim.get("evidence", []) if isinstance(e, dict)]
            evidence_text = " ".join(evidence_snippets).strip()
            claims_data.append({
                "claim_text": entry.get("text", ""),
                "verdict": verdict,
                "confidence": entry.get("effective_confidence", entry.get("score", 0.5)),
                "evidence": evidence_text if evidence_text else None,
            })

        # Bulk create claims
        created_claims = await claim_repo.bulk_create(
            report_id=report.id,
            claims_data=claims_data,
        )

        # Create evidence for each claim
        for i, entry in enumerate(enriched_report):
            claim_id = entry["id"]
            full_claim = next((c for c in claims if c["id"] == claim_id), None)
            if full_claim is None or not full_claim.get("evidence"):
                continue
            created_claim = created_claims[i] if i < len(created_claims) else None
            if created_claim is None:
                continue
            evidence_list = []
            for ev in full_claim.get("evidence", []):
                if not isinstance(ev, dict):
                    continue
                evidence_list.append({
                    "source_title": ev.get("title", ""),
                    "source_url": ev.get("source", ""),
                    "evidence_snippet": ev.get("snippet", ""),
                    "source_type": SourceType.WEB,
                })
            if evidence_list:
                await evidence_repo.bulk_create(
                    claim_id=created_claim.id,
                    evidence_list=evidence_list,
                )

        return chat_session.id


# -----------------------
# New chat endpoint integrating answer generation and pipeline
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, current_user: User = Depends(get_current_user_optional)) -> ChatResponsePayload:
    """Generate an answer for the given prompt and run the hallucination detection pipeline.

    The frontend sends a JSON with the user prompt. This endpoint:
    1. Generates an answer using ``generate_answer`` (fallback placeholder if the Gemini API key is missing).
    2. Decomposes the answer into atomic claims.
    3. Retrieves evidence, verifies claims, performs graph‑aware enrichment, and aggregates confidence.
    4. Returns a payload matching the frontend ``ChatResponsePayload`` shape.
    """
    # 1. Generate answer (fallback returns an empty string when API key is missing)
    answer_obj = generate_answer(request.prompt, request.model)
    answer_text = answer_obj.get("answer_text")
    # Fallback: if answer generation failed (empty/None), provide a simple deterministic answer for common queries
    if not answer_text:
        import re
        # Very small knowledge base for capitals (extend as needed)
        _CAPITALS = {
            "france": "Paris",
            "germany": "Berlin",
            "spain": "Madrid",
            "italy": "Rome",
            "united kingdom": "London",
            "uk": "London",
            "usa": "Washington, D.C.",
            "united states": "Washington, D.C.",
        }
        # Extract possible country name after "capital of"
        m = re.search(r"capital of ([a-zA-Z\s]+)", request.prompt.lower())
        if m:
            country = m.group(1).strip()
            answer_text = _CAPITALS.get(country, "I don't have that information right now.")
        else:
            answer_text = "I couldn't determine an answer; please rephrase your question."


    # 2. Decompose answer into claims
    decomposition = call1_run(request.prompt, answer_text)
    claims = decomposition.get("claims", [])

    # 3. Retrieval (adds ``evidence`` field)
    claims = retrieve_for_claims(claims)

    # 4. Verification using OpenRouter models (Nemotron, GLM, Inkling)
    claims = verify_claims(claims)

    # 5. Phase 2 – graph‑aware enrichment (same as the original pipeline)
    similar_pairs = compute_claim_pair_similarities(claims, similarity_threshold=0.5)
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
    claims = propagate_claims(claims, edges)

    # 6. Residual detection and escalation
    residuals = identify_residual_claims(claims)
    escalated = escalate_residual_claims(claims, residuals)
    metrics.increment_escalated_claims(len(escalated))
    escalated_map = {e["id"]: e["escalated_verdict"] for e in escalated}
    for claim in claims:
        esc_verdict = escalated_map.get(claim["id"])
        if esc_verdict:
            claim["escalated_verdict"] = esc_verdict
    escalation_rate = len(escalated) / max(1, len(claims))

    # 7. Aggregation
    aggregation = aggregate_claims(claims)
    enriched_report = []
    for entry in aggregation["report"]:
        full_claim = next(c for c in claims if c["id"] == entry["id"])
        entry["effective_confidence"] = full_claim.get("effective_confidence", entry["score"])
        if full_claim.get("internal_consistency_failure"):
            entry["internal_consistency_failure"] = True
        enriched_report.append(entry)

    # 8. Build findings for the frontend
    status_map = {
        "supported": "verified",
        "refuted": "contradicted",
        "insufficient_evidence": "unsupported",
    }
    retrieval_status_map = {
        "supported": "verified_match",
        "refuted": "conflicting_evidence",
        "insufficient_evidence": "no_evidence_found",
    }
    # Count verified claims from enriched_report (verdict == "supported")
    verified_count = sum(1 for entry in enriched_report if entry.get("verdict") == "supported")
    findings = []
    for entry in enriched_report:
        claim_id = entry["id"]
        full_claim = next(c for c in claims if c["id"] == claim_id)
        verdict = entry.get("verdict", "insufficient_evidence")
        status = status_map.get(verdict, "unsupported")
        # Only include non-verified claims in findings
        if status == "verified":
            continue
        confidence = entry.get("effective_confidence", entry.get("score", 0.5))
        # Concatenate evidence snippets if available
        evidence_snippets = [e.get("snippet", "") for e in full_claim.get("evidence", []) if isinstance(e, dict)]
        evidence = " ".join(evidence_snippets).strip()
        source = {}
        if full_claim.get("evidence"):
            first = full_claim["evidence"][0]
            if isinstance(first, dict):
                source = {
                    "title": first.get("title", ""),
                    "url": first.get("source", ""),
                    "domain": first.get("source", ""),
                    "snippet": first.get("snippet", ""),
                }
        findings.append({
            "claim": entry.get("text", ""),
            "status": status,
            "confidence": confidence,
            "reason": "",
            "evidence": evidence,
            "source": source,
            "retrievalStatus": retrieval_status_map.get(verdict, "no_evidence_found"),
        })

    # 9. Determine overall status for the response
    aggregate_conf = aggregation.get("aggregate_confidence", 0.0)
    if aggregate_conf >= 0.85:
        overall_status = "verified"
    elif aggregate_conf >= 0.7:
        overall_status = "mostly_reliable"
    elif aggregate_conf >= 0.5:
        overall_status = "partially_reliable"
    else:
        overall_status = "potential_hallucination"

    # 10. Assemble the final payload
    response = ChatResponsePayload(
        answer=answer_text,
        confidence=aggregate_conf,
        status=overall_status,
        findings=findings,
        totalClaimsCount=len(enriched_report),
        verifiedClaimsCount=verified_count,
        flaggedFindingsCount=len(findings),
        summary=f"Aggregated confidence {aggregate_conf:.2f} (escalation rate {escalation_rate:.2%})",
    )

    # 11. Persist chat session, messages, and verification report (if user authenticated)
    chat_session_id: uuid.UUID | None = None
    if current_user is not None:

        chat_session_id = await _persist_chat_data(
            user_id=current_user.id,
            prompt=request.prompt,
            answer_text=answer_text,
            model=request.model or "unknown",
            claims=claims,
            enriched_report=enriched_report,
            aggregate_conf=aggregate_conf,
            overall_status=overall_status,
            findings=findings,
            escalation_rate=escalation_rate,
        )

    # 12. Assemble the final payload
    response = ChatResponsePayload(
        answer=answer_text,
        confidence=aggregate_conf,
        status=overall_status,
        findings=findings,
        totalClaimsCount=len(enriched_report),
        verifiedClaimsCount=verified_count,
        flaggedFindingsCount=len(findings),
        summary=f"Aggregated confidence {aggregate_conf:.2f} (escalation rate {escalation_rate:.2%})",
    )
    # Add chat session ID to response for frontend sync
    if chat_session_id is not None:
        response_dict = response.model_dump()
        response_dict["chatSessionId"] = str(chat_session_id)
        return response_dict
    return response

# Enable CORS for the frontend (development) and production.
# allow_origins=["*"] is incompatible with allow_credentials=True per CORS spec.
# Use specific origins. Default to Vite dev server origin; override via CORS_ORIGINS env var.
import os
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend assets when running in production.
# The static files are served directly from the `frontend_skepticai` folder,
# which contains the source entry point and assets. This works for development
# without a pre‑built Vite output.

class PipelineRequest(BaseModel):
    question: str
    answer_text: str

class PipelineResponse(BaseModel):
    aggregate_confidence: float
    report: list
    residual_claims: list
    llm_calls: int
    retrieval_calls: int
    estimated_cost_usd: float
    total_latency_seconds: float
    escalation_rate: float

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/database")
async def database_health():
    """Check database connectivity."""
    from Backend.database.connection import health_check as db_health_check
    is_healthy = await db_health_check()
    return {
        "status": "ok" if is_healthy else "error",
        "database": "connected" if is_healthy else "disconnected",
    }


@app.get("/health/verification")
def verification_health():
    """Check reachability of each OpenRouter verification model."""
    results = {}
    # Use a minimal claim batch for probing
    probe_claims = [{"id": "probe", "text": "test claim", "evidence": []}]
    user_prompt = _format_claim_batch(probe_claims)
    for model_id in VERIFICATION_MODEL_IDS:
        resp_text = call_model(model_id, _SYSTEM_PROMPT, user_prompt)
        if resp_text:
            # Try to parse verdicts
            import json, re
            json_match = re.search(r"\{.*\}", resp_text, re.DOTALL)
            json_str = json_match.group(0) if json_match else resp_text
            try:
                data = json.loads(json_str)
                if isinstance(data, dict) and "verdicts" in data:
                    results[model_id] = "ok"
                else:
                    results[model_id] = "unexpected_response"
            except Exception:
                results[model_id] = "parse_error"
        else:
            results[model_id] = "unreachable"
    return {"verification_models": results}


@app.get("/metrics")
def get_metrics():
    return {
        "llm_calls": metrics.llm_calls,
        "retrieval_calls": metrics.retrieval_calls,
        "estimated_cost_usd": metrics.estimate_cost(),
        "total_latency_seconds": metrics.get_total_latency(),
    }

# Phase 4 – observability endpoints
@app.get("/metrics/history")
def get_metrics_history():
    """Return a list of past run metrics for dashboard consumption."""
    return metrics.get_history()

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """Simple observability dashboard."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hallucination Detection Dashboard</title>
        <style>
            body {font-family: Arial, sans-serif; margin: 20px;}
            table {border-collapse: collapse; width: 100%;}
            th, td {border: 1px solid #ddd; padding: 8px; text-align: left;}
            th {background-color: #f2f2f2;}
        </style>
    </head>
    <body>
        <h1>Hallucination Detection Metrics Dashboard</h1>
        <p>Loading data...</p>
        <table id="metrics-table" style="display:none;">
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Aggregate Confidence</th>
                    <th>LLM Calls</th>
                    <th>Retrieval Calls</th>
                    <th>Escalated Claims</th>
                    <th>Escalation Rate</th>
                    <th>Estimated Cost (USD)</th>
                    <th>Total Latency (s)</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
        <script>
            fetch('/metrics/history')
                .then(r => r.json())
                .then(data => {
                    const table = document.getElementById('metrics-table');
                    const tbody = table.querySelector('tbody');
                    data.forEach(row => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `<td>${row.timestamp}</td>
                                        <td>${row.aggregate_confidence?.toFixed(3) ?? ''}</td>
                                        <td>${row.llm_calls}</td>
                                        <td>${row.retrieval_calls}</td>
                                        <td>${row.escalated_claims}</td>
                                        <td>${(row.escalation_rate*100).toFixed(1)}%</td>
                                        <td>${row.estimated_cost_usd?.toFixed(4) ?? ''}</td>
                                        <td>${row.total_latency_seconds?.toFixed(3) ?? ''}</td>`;
                        tbody.appendChild(tr);
                    });
                    document.querySelector('p').style.display = 'none';
                    table.style.display = '';
                });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/pipeline", response_model=PipelineResponse)
def run_pipeline(request: PipelineRequest):
    metrics.reset()
    # Step 1: Decompose and triage (Call 1)
    decomposition = call1_run(request.question, request.answer_text)
    claims = decomposition.get("claims", [])

    # Step 2: Retrieval (adds ``evidence`` field)
    claims = retrieve_for_claims(claims)

    # Step 3: Batched verification (adds ``verdict`` field)
    claims = verify_claims(claims)

    # -------------------------------------------------------------
    # Phase 2 – graph‑aware enrichment
    # -------------------------------------------------------------
    # 2.1 Compute claim‑pair similarities (embedding + entity overlap)
    similar_pairs = compute_claim_pair_similarities(claims, similarity_threshold=0.5)

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
    # Phase 3 – residual detection and escalation
    residuals = identify_residual_claims(claims)
    escalated = escalate_residual_claims(claims, residuals)
    # Record escalated count for observability
    metrics.increment_escalated_claims(len(escalated))
    # Merge escalated verdict into claims
    escalated_map = {e["id"]: e["escalated_verdict"] for e in escalated}
    for claim in claims:
        esc_verdict = escalated_map.get(claim["id"])
        if esc_verdict:
            claim["escalated_verdict"] = esc_verdict
    # Compute escalation rate for this request
    escalation_rate = len(escalated) / max(1, len(claims))

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

    # Prepare pipeline response data
    response_data = {
        "aggregate_confidence": aggregation["aggregate_confidence"],
        "report": enriched_report,
        "residual_claims": residuals,
        "llm_calls": metrics.llm_calls,
        "retrieval_calls": metrics.retrieval_calls,
        "estimated_cost_usd": metrics.estimate_cost(),
        "total_latency_seconds": metrics.get_total_latency(),
        "escalation_rate": escalation_rate,
    }
    # Record this run in metrics history for observability dashboard
    try:
        metrics.record_history({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "aggregate_confidence": aggregation["aggregate_confidence"],
            "llm_calls": metrics.llm_calls,
            "retrieval_calls": metrics.retrieval_calls,
            "escalated_claims": len(escalated),
            "escalation_rate": escalation_rate,
            "estimated_cost_usd": metrics.estimate_cost(),
            "total_latency_seconds": metrics.get_total_latency(),
        })
    except Exception:
        pass
    return response_data


# Chat history API endpoints
class ChatSessionResponse(BaseModel):
    id: str
    title: str
    createdAt: str
    updatedAt: str
    modelId: str
    messageCount: int

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str
    modelId: str | None = None
    analysis: dict | None = None


@app.get("/api/chats", response_model=list[ChatSessionResponse])
async def get_chats(current_user: User = Depends(get_current_user)) -> list[ChatSessionResponse]:
    """Get all chat sessions for the current user."""
    async with get_session() as session:
        chat_repo = ChatSessionRepository(session)
        sessions = await chat_repo.get_by_user(current_user.id)
        return [
            ChatSessionResponse(
                id=str(s.id),
                title=s.title,
                createdAt=s.created_at.isoformat(),
                updatedAt=s.updated_at.isoformat(),
                modelId=s.selected_model,
                messageCount=len(s.messages),
            )
            for s in sessions
        ]


@app.get("/api/chats/{chat_id}/messages", response_model=list[MessageResponse])
async def get_chat_messages(chat_id: str, current_user: User = Depends(get_current_user)) -> list[MessageResponse]:
    """Get all messages for a specific chat session."""
    import uuid
    chat_uuid = uuid.UUID(chat_id)
    async with get_session() as session:
        chat_repo = ChatSessionRepository(session)
        msg_repo = MessageRepository(session)
        
        # Verify the chat belongs to the current user
        chat = await chat_repo.get_by_id(chat_uuid)
        if not chat or chat.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        messages = await msg_repo.get_by_session(chat_uuid)
        return [
            MessageResponse(
                id=str(m.id),
                role=m.role.value,
                content=m.content,
                timestamp=m.created_at.isoformat(),
                modelId=m.model,
                analysis=m.verification_report and {
                    "confidence": m.verification_report.confidence_score,
                    "status": m.verification_report.status.value,
                    "summary": m.verification_report.summary,
                }
            )
            for m in messages
        ]


app.mount("/", StaticFiles(directory="frontend_skepticai", html=True), name="static")

# ---------------------------------------------------------------------------
from Backend.modules import escalate_residual_claims
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # When run directly, first process the dataset then start the API server.
    _process_dataset()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
