"""
Cost/token logging for the resume parser.

Tracks input/output tokens and estimated cost per call, plus a running
cumulative total across a session. Pricing is per-million-tokens, matching
Anthropic's published rates - update PRICING if rates change.
"""

import json
import os
from datetime import datetime, timezone

# Per-million-token pricing (USD). Update if Anthropic's rates change.
PRICING = {
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "claude-sonnet-5": {"input": 2.00, "output": 10.00},  # intro pricing through Aug 31 2026
}

LOG_FILE = "cost_log.jsonl"  # one JSON object per line - easy to append, easy to parse later


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate the USD cost of a single call given its token usage."""
    rates = PRICING.get(model)
    if rates is None:
        # Unknown model - don't silently return 0, that would hide real cost
        raise ValueError(f"No pricing data for model '{model}' - add it to PRICING before using this model.")

    input_cost = (input_tokens / 1_000_000) * rates["input"]
    output_cost = (output_tokens / 1_000_000) * rates["output"]
    return input_cost + output_cost


def log_call(model: str, input_tokens: int, output_tokens: int, purpose: str = "") -> dict:
    """
    Log one API call's token usage and estimated cost.
    Appends to LOG_FILE (creates it if it doesn't exist) and returns the
    logged entry so the caller can also print/use it immediately.
    """
    cost = estimate_cost(model, input_tokens, output_tokens)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": round(cost, 6),
        "purpose": purpose,
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def get_session_total() -> dict:
    """Read the log file and return cumulative totals - useful for a
    'how much have I spent so far' check during a work session."""
    if not os.path.exists(LOG_FILE):
        return {"total_calls": 0, "total_input_tokens": 0, "total_output_tokens": 0, "total_cost_usd": 0.0}

    total_calls = 0
    total_input = 0
    total_output = 0
    total_cost = 0.0

    with open(LOG_FILE) as f:
        for line in f:
            entry = json.loads(line)
            total_calls += 1
            total_input += entry["input_tokens"]
            total_output += entry["output_tokens"]
            total_cost += entry["estimated_cost_usd"]

    return {
        "total_calls": total_calls,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_cost_usd": round(total_cost, 6),
    }