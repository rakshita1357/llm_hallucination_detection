import sys
sys.path.insert(0, '.')
from Backend.modules.openrouter_client import call_model

system_prompt = """You are an AI assistant that verifies factual claims based on provided evidence.
For each claim you must output a JSON object with the following schema:
{"verdicts": [{"id": <claim_id>, "verdict": <one of "supported", "refuted", "insufficient_evidence">}, ...]}

Follow these rules:
1. Use only the evidence supplied for a claim when deciding the verdict.
2. If the evidence directly supports the claim, output "supported".
3. If the evidence directly contradicts the claim, output "refuted".
3. If the evidence is missing, ambiguous, or does not address the claim, output "insufficient_evidence".
5. Do not fabricate evidence – rely solely on the snippets given."""

user_prompt = """ID: c1
Claim: The capital of France is Paris.
Evidence:
- Paris is the capital of France."""

resp = call_model('nvidia/nemotron-3-ultra-550b-a55b:free', system_prompt, user_prompt)
print('Nemotron response:', resp)