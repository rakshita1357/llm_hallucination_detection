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
# Build NLI inputs
nli_inputs = []
for pair in similar_pairs:
    c1_id = pair["claim1_id"]
    c2_id = pair["claim2_id"]
    c1_text = next(c["text"] for c in claims if c["id"] == c1_id)
    c2_text = next(c["text"] for c in claims if c["id"] == c2_id)
    nli_inputs.append({
        "claim1_id": c1_id,
        "claim1_text": c1_text,
        "claim2_id": c2_id,
        "claim2_text": c2_text,
    })

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
