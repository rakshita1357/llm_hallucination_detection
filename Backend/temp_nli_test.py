from modules.nli_cross_encoder import run_nli_on_claim_pairs

pairs = [{
    "claim1_id": "c1",
    "claim1_text": "The sky is blue.",
    "claim2_id": "c2",
    "claim2_text": "The sky is red."
}]

print(run_nli_on_claim_pairs(pairs))
