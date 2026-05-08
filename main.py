import pandas as pd
from modules.claim_extractor import extract_claims

# Load dataset
df = pd.read_json("data/raw/sample_dataset.json")

# Extract claims
df["generated_claims"] = df["llm_response"].apply(extract_claims)

# Save results
df.to_json(
    "data/processed/claims_dataset.json",
    orient="records",
    indent=4
)

print("Claim extraction completed!\n")

print(df[["llm_response", "generated_claims"]].head())