"""Call 1 — Joint Decomposition, Triage, and Graph Edges.

Takes an LLM-generated answer (and optional original question) and returns
a validated structured JSON object containing atomic claims with self-rated
confidence and retrieval flags.

This module is deliberately modular and beginner-friendly. The LLM call is
isolated in `call1_run()` so it can be replaced with a real LLM invocation
without touching the rest of the pipeline.

Migrated to the modern `google-genai` SDK (via Backend.modules.genai_client)
with thinking_budget=0, so the full max_output_tokens budget goes to the
visible JSON output instead of being silently consumed by internal
"thinking" tokens (the root cause of earlier truncation/JSON-parse failures).
"""

from __future__ import annotations

import json
import os
import re
import time
from Backend.modules.free_signal import compute_claim_logprob_entropy
from Backend.modules.genai_client import generate as genai_generate, get_client as genai_get_client
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Tuple

# Threshold for flagging low-probability claims based on token logprob entropy (higher is worse).
# Can be tuned based on validation data.
LOGPROB_ENTROPY_THRESHOLD = 2.0  # Example threshold (average negative log‑probability)


from dotenv import load_dotenv

load_dotenv()

import spacy
from Backend.modules import metrics

# --- Load spaCy model (same as existing project) ---
try:
    _nlp = spacy.load("en_core_web_sm")
except OSError:
    # Fallback to a blank English model if the full model is not installed
    _nlp = spacy.blank("en")
    # Add a simple sentencizer to enable sentence segmentation
    if not _nlp.has_pipe("sentencizer"):
        _nlp.add_pipe("sentencizer")

GEMINI_MODEL_NAME = "gemini-2.5-flash"

# --- Uncertainty keywords that lower self-confidence ---
_LOW_CONFIDENCE_KEYWORDS = {
    "maybe", "perhaps", "possibly", "might", "could be", "it seems",
    "I think", "I believe", "as far as i know", "as far as i understand"
}

# --- Augmentation keywords that raise self-confidence ---
_HIGH_CONFIDENCE_KEYWORDS = {
    "definitely", "certainly", "always", "never", "proven", "verified",
    "established", "confirmed"
}


@dataclass
class Claim:
    """A single atomic claim with triage metadata."""

    id: str
    text: str
    self_confidence: float  # in [0, 1]
    needs_retrieval: bool
    search_query: Optional[str] = None
    # Token-level free signal: average negative log‑probability (entropy) for the claim
    logprob_entropy: float = 0.0


def _compute_self_confidence(text: str) -> float:
    """Heuristic self-confidence score in [0, 1].

    - Starts at 0.5 (neutral)
    - Increased if high-confidence keywords are present
    - Decreased if low-confidence / uncertain keywords are present
    """
    text_lower = text.lower().strip()

    score = 0.5

    # Boost for high-confidence markers
    for kw in _HIGH_CONFIDENCE_KEYWORDS:
        if kw.lower() in text_lower:
            score = min(1.0, score + 0.15)

    # Penalize for uncertain language (case-insensitive check)
    for kw in _LOW_CONFIDENCE_KEYWORDS:
        if kw.lower() in text_lower:
            score = max(0.0, score - 0.2)

    # Short, declarative sentences about factual topics get a slight boost
    if re.match(r"^[A-Z][a-z\s]+[.!?]$", text.strip()) and len(text.split()) <= 20:
        score = min(1.0, score + 0.1)

    return round(score, 2)


def _generate_search_query(claim_text: str) -> str:
    """Create a simple search query from a claim by taking the core noun phrase."""
    # Simple: just return the claim text trimmed to a reasonable query length
    # In a real system, this would use NER/entity extraction
    query = claim_text.strip()
    # Trim if very long (keep first ~20 words)
    words = query.split()
    if len(words) > 20:
        query = " ".join(words[:20])
    return query


def _extract_atomic_claims_spacy(text: str) -> List[str]:
    """Extract atomic claims using the existing spaCy pipeline.

    Reuses the project's existing `modules.atomic_claim_extractor.split_into_atomic_claims`
    logic inline to avoid unnecessary imports.
    """
    # Clause-based splitters (same as existing)
    CLAUSE_SPLITTERS = [
        " and ", " while ", " but ", " because ", " although ",
        " since ", " whereas "
    ]

    claims = [text]

    for splitter in CLAUSE_SPLITTERS:
        temp_claims = []
        for claim in claims:
            split_parts = claim.split(splitter)
            for part in split_parts:
                cleaned = part.strip()
                if len(cleaned.split()) > 3:
                    temp_claims.append(cleaned)
        claims = temp_claims

    # Further split by sentence boundaries using spaCy
    doc = _nlp(" ".join(claims))
    final_claims = []
    for sent in doc.sents:
        s = sent.text.strip()
        if len(s.split()) > 3:
            final_claims.append(s)

    return final_claims


def _call_llm_decompose(question: str, answer_text: str) -> Optional[Dict[str, Any]]:
    """Call the LLM to decompose the answer into atomic claims.

    Sends the question and answer to Gemini with a structured prompt
    requesting atomic claims in JSON format. Returns the parsed result,
    or None if the call fails or the API key is not available.
    """
    if genai_get_client() is None:
        return None

    system_prompt = """You are an AI assistant tasked with decomposing an LLM-generated answer into atomic, independently verifiable claims.

For each claim, provide:
- id: a unique identifier (e.g., "c1", "c2", ...)
- text: the claim text (atomic and independently verifiable)
- self_confidence: a numeric confidence score in [0, 1] representing your confidence that the claim is true (0 = not confident at all, 1 = very confident)
- needs_retrieval: true if this claim requires external verification/fact-checking, false otherwise
- search_query: a search query to find evidence for the claim (only if needs_retrieval is true)

Rules:
1. Claims must be atomic and independently verifiable (no "and", "but", "or" connecting multiple ideas in one claim).
2. self_confidence must be a decimal number between 0 and 1 inclusive.
3. needs_retrieval must be a boolean (true/false).
4. If needs_retrieval is true, provide a search_query string; if needs_retrieval is false, set search_query to null.
5. Output MUST be a valid JSON object with a single key "claims" mapping to an array of claim objects.
6. Do not include any reasoning, explanation, or text outside the JSON.

Format your response as a single JSON object:
{"claims": [{"id": "c1", "text": "...", "self_confidence": 0.8, "needs_retrieval": true, "search_query": "..."}]}
"""

    user_prompt = f"""Original question: {question if question else "(not provided)"}

LLM-generated answer: {answer_text}

Decompose this answer into atomic claims following the format above.
"""

    try:
        metrics.increment_llm_calls()
        start = time.perf_counter()
        response = genai_generate(
            model=GEMINI_MODEL_NAME,
            prompt=system_prompt + "\n\n" + user_prompt,
            temperature=0.0,
            max_output_tokens=4096,
            thinking_budget=0,
        )
        elapsed = time.perf_counter() - start
        metrics.add_latency(elapsed)

        if response is None:
            return None

        content = response.text or ""
        try:
            print(f"[CALL1 DEBUG] finish_reason: {response.candidates[0].finish_reason}")
            print(f"[CALL1 DEBUG] usage_metadata: {response.usage_metadata}")
        except Exception as _dbg_e:
            print(f"[CALL1 DEBUG] could not read finish_reason/usage: {_dbg_e!r}")
        print(f"[CALL1 DEBUG] raw response.text repr: {content!r}")

        # Strip markdown code fences (```json ... ``` or ``` ... ```) if present,
        # since Gemini sometimes wraps JSON output in them regardless of the
        # "no text outside JSON" instruction in the prompt.
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
            cleaned = re.sub(r"```\s*$", "", cleaned)
            cleaned = cleaned.strip()

        # Find the JSON block in the response
        json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = cleaned

        parsed = json.loads(json_str)

        # Validate that we have the expected structure
        if isinstance(parsed, dict) and "claims" in parsed and isinstance(parsed["claims"], list):
            return parsed
        else:
            return None

    except Exception as e:
        # Log the error but return None to trigger fallback
        print(f"[CALL1 LLM DECOMPOSE FAILED] {e!r}")
        return None


def _fallback_rule_based(question: str, answer_text: str, token_logprobs: Optional[List[float]] = None, offsets: Optional[List[Tuple[int, int]]] = None) -> Dict[str, Any]:
    """Fallback rule-based decomposition using spaCy + heuristic confidence.

    Used when the LLM call fails or is not available.
    """
    # 1. Extract atomic claims using spaCy-based splitter
    raw_claims = _extract_atomic_claims_spacy(answer_text)

    # 2. Build Claim objects with triage metadata
    claims: List = []
    for i, claim_text in enumerate(raw_claims, start=1):
        confidence = _compute_self_confidence(claim_text)
        # Always retrieve evidence for factual claims; self_confidence influences
        # verification weighting, not retrieval gating.
        needs_retrieval = True
        search_query = _generate_search_query(claim_text)

        claim = Claim(
            id=f"c{i}",
            text=claim_text,
            self_confidence=confidence,
            needs_retrieval=needs_retrieval,
            search_query=search_query,
        )
        # Compute token logprob entropy for the claim (if token data available)
        entropy = compute_claim_logprob_entropy(
            claim_text=claim_text,
            answer_text=answer_text,
            token_logprobs=token_logprobs or [],
            offsets=offsets or [],
        )
        # Set the computed entropy (rounded to two decimals)
        claim.logprob_entropy = round(entropy, 2)
        # Override retrieval flag if entropy exceeds threshold (high uncertainty)
        if entropy > LOGPROB_ENTROPY_THRESHOLD:
            claim.needs_retrieval = True

        claims.append(claim)

    # 3. Validate and serialize to dict
    result = {"claims": [asdict(c) for c in claims]}

    # Schema validation: ensure all required fields are present and correct type
    for c in result["claims"]:
        assert isinstance(c["id"], str), f"Claim id must be str, got {type(c['id'])}"
        assert isinstance(c["text"], str), f"Claim text must be str, got {type(c['text'])}"
        assert isinstance(c["self_confidence"], float), f"self_confidence must be float, got {type(c['self_confidence'])}"
        assert 0.0 <= c["self_confidence"] <= 1.0, f"self_confidence must be in [0,1], got {c['self_confidence']}"
        assert isinstance(c["needs_retrieval"], bool), f"needs_retrieval must be bool, got {type(c['needs_retrieval'])}"
        if c["needs_retrieval"]:
            assert c["search_query"] is not None, "search_query must be present when needs_retrieval is True"

    return result


def call1_run(question: str, answer_text: str, token_logprobs: Optional[List[float]] = None, offsets: Optional[List[Tuple[int, int]]] = None) -> Dict[str, Any]:
    """Run Call 1: decomposition + triage.

    Attempts to use an LLM to decompose the answer into atomic claims with
    self-rated confidence and retrieval flags. Falls back to a rule-based
    heuristic (spaCy + keyword scoring) if the LLM call fails or the API key
    is not available.

    Args:
        question: The original user question (may be empty if not available).
        answer_text: The LLM-generated answer to decompose.

    Returns:
        A dict matching the expected Call 1 JSON schema (additional fields may be present):
        {
            "claims": [
                {
                    "id": "c1",
                    "text": "...",
                    "self_confidence": 0.8,
                    "needs_retrieval": true,
                    "search_query": "...",
                    "logprob_entropy": 1.23  # average negative log‑probability (optional)
                },
                ...
            ]
        }
    """
    if not answer_text or not answer_text.strip():
        return {"claims": []}

    # 1. Try LLM-based decomposition with a single retry on failure/malformed output
    llm_result = None
    for _attempt in range(2):
        llm_result = _call_llm_decompose(question, answer_text)
        if llm_result is not None:
            break
        # retry on None result
    if llm_result is not None:
        # LLM call succeeded - validate and return
        # Ensure the result has the expected schema
        claims = llm_result.get("claims", [])
        # Validate each claim has required fields
        valid_claims = []
        for c in claims:
            if not isinstance(c, dict):
                continue
            try:
                # Ensure all required fields are present and correct type
                claim_id = c.get("id", f"c{len(valid_claims) + 1}")
                claim_text = c.get("text", "")
                self_confidence = float(c.get("self_confidence", 0.5))
                needs_retrieval = bool(c.get("needs_retrieval", False))
                search_query = c.get("search_query")  # may be None or str

                # Constrain self_confidence to [0, 1]
                self_confidence = max(0.0, min(1.0, self_confidence))

                # search_query must be present when needs_retrieval is True
                if needs_retrieval and search_query is None:
                    search_query = f"search for: {claim_text}"

                valid_claims.append({
                    "id": str(claim_id),
                    "text": str(claim_text),
                    "self_confidence": round(self_confidence, 2),
                    "needs_retrieval": needs_retrieval,
                    "search_query": search_query,
                })
            except (ValueError, TypeError, KeyError):
                # Skip malformed claim entries
                continue
        # Compute logprob entropy for each claim (if token logprobs are provided)
        # token_logprobs and offsets may be None; compute_claim_logprob_entropy handles empty inputs.
        for vc in valid_claims:
            entropy = compute_claim_logprob_entropy(
                claim_text=vc["text"],
                answer_text=answer_text,
                token_logprobs=token_logprobs or [],
                offsets=offsets or [],
            )
            vc["logprob_entropy"] = round(entropy, 2)
            if entropy > LOGPROB_ENTROPY_THRESHOLD:
                vc["needs_retrieval"] = True

        if valid_claims:
            return {"claims": valid_claims}

    # 2. Fall back to rule-based heuristic
    return _fallback_rule_based(question, answer_text, token_logprobs, offsets)


# --- Simple CLI for manual testing ---
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m modules.call1_decomposition '<answer_text>' [ '<question>' ]")
        sys.exit(1)

    answer = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else ""

    output = call1_run(question, answer)
    print(json.dumps(output, indent=2))
