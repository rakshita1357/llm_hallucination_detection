import pandas as pd
from modules.atomic_claim_extractor import extract_atomic_claims

# Load dataset
df = pd.read_json("data/raw/sample_dataset.json")

# Generate atomic claims
df["atomic_claims"] = df["llm_response"].apply(extract_atomic_claims)

# Save output
df.to_json(
    "data/processed/atomic_claims_dataset.json",
    orient="records",
    indent=4
)

print("Atomic claim extraction completed!")