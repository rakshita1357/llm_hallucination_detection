import json
from modules.call1_decomposition import call1_run
from modules.retrieval import retrieve_for_claims
from modules.call2_verification import call2_verify
from modules.claim_pair_similarity import compute_claim_pair_similarities
from modules.nli_cross_encoder import run_nli_on_claim_pairs
from modules.graph_propagation import propagate_claims
from modules.residual_claims import identify_residual_claims
from modules.escalation import escalate_residual_claims

question = "Test"
answer = "The sky is blue."
# Phase 1
claims = call1_run(question, answer).get('claims', [])
claims = retrieve_for_claims(claims)
claims = call2_verify(claims)
# Phase 2
similar_pairs = compute_claim_pair_similarities(claims)
inputs = [{
    "claim1_id": p["claim1_id"],
    "claim1_text": next(c["text"] for c in claims if c["id"] == p["claim1_id"]),
    "claim2_id": p["claim2_id"],
    "claim2_text": next(c["text"] for c in claims if c["id"] == p["claim2_id"]),
} for p in similar_pairs]
results = run_nli_on_claim_pairs(inputs)
edges = []
for res in results:
    if res["nli"] == "supports":
        edge_type = "depends_on"
    elif res["nli"] == "contradicts":
        edge_type = "contradicts"
    else:
        continue
    edges.append({"source_id": res["claim1_id"], "target_id": res["claim2_id"], "type": edge_type})
claims = propagate_claims(claims, edges)
# Phase 3
residuals = identify_residual_claims(claims)
escalated = escalate_residual_claims(claims, residuals)
print('Residuals:', residuals)
print('Escalated:', escalated)
