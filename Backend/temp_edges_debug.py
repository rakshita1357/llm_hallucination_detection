from modules.call1_decomposition import call1_run
from modules.retrieval import retrieve_for_claims
from modules.call2_verification import call2_verify
from modules.claim_pair_similarity import compute_claim_pair_similarities
from modules.nli_cross_encoder import run_nli_on_claim_pairs

question = ""
answer = "The sky is blue. The sky is red."
# Phase 1
claims = call1_run(question, answer).get('claims', [])
claims = retrieve_for_claims(claims)
claims = call2_verify(claims)
# Phase 2 similarity
similar_pairs = compute_claim_pair_similarities(claims)
print('similar_pairs:', similar_pairs)
# NLI inputs
nli_inputs = [{
    "claim1_id": p["claim1_id"],
    "claim1_text": next(c["text"] for c in claims if c["id"] == p["claim1_id"]), ""),
    "claim2_id": p["claim2_id"],
    "claim2_text": next(c["text"] for c in claims if c["id"] == p["claim2_id"]),
} for p in similar_pairs]

nli_results = run_nli_on_claim_pairs(nli_inputs)
print('nli_results:', nli_results)
# Build edges
edges = []
for res in nli_results:
    if res["nli"] == "supports":
        edge_type = "depends_on"
    elif res["nli"] == "contradicts":
        edge_type = "contradicts"
    else:
        continue
    edges.append({"source_id": res["claim1_id"], "target_id": res["claim2_id"], "type": edge_type})
print('edges:', edges)
