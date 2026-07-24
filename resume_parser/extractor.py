"""
Core extraction logic for the resume parser.

Scaffolded Wednesday (Week 3) - schema and basic extraction only.
Thursday adds: input validation + schema validation on output. (DONE)
Friday adds: retry logic for malformed outputs + error handling. (DONE)
(Following your existing Phase 1, Week 4 plan.)
"""

import time
import anthropic

from .client import call_claude
from .schema import RESUME_EXTRACTION_TOOL
from .validators import validate_input, validate_output, ValidationError

MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 2  # doubles each retry: 2s, 4s, 8s


def _call_model(resume_text: str, correction_note: str = "") -> dict:
    """One raw call to the model, optionally with a correction note appended
    (used when retrying after a validation failure)."""
    user_content = f"Extract structured data from this resume:\n\n{resume_text}"
    if correction_note:
        user_content += f"\n\nNote: your previous attempt had issues - {correction_note}. Please correct them."

    response = call_claude(
        messages=[{"role": "user", "content": user_content}],
        system="You are a resume parsing assistant. Extract candidate information accurately. "
               "If a field genuinely isn't present, use an empty string or empty array rather than guessing.",
        tools=[RESUME_EXTRACTION_TOOL],
        tool_choice={"type": "tool", "name": "extract_resume_data"},
        max_tokens=1500,
    )

    for block in response.content:
        if block.type == "tool_use":
            return block.input
    return {}


def extract_resume(resume_text: str) -> dict:
    """
    Extract structured data from raw resume text.

    Raises ValidationError if input fails basic sanity checks (not retried -
    a genuinely empty/too-long input won't fix itself on retry).

    Retries on:
      - API errors (rate limits, transient failures) - exponential backoff, no feedback needed.
      - Output validation failures - retries WITH the specific issues fed back
        to the model, so it can actually self-correct rather than guessing blindly again.

    If still invalid after MAX_RETRIES, returns the best available result with
    an added "_validation_issues" key rather than raising - a partially-valid
    result is often still useful, and the caller can decide what to do with it.
    """
    validate_input(resume_text)  # not retried - a bad input stays bad

    correction_note = ""
    last_result = {}
    last_issues = []

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = _call_model(resume_text, correction_note)
        except anthropic.RateLimitError:
            wait = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
            print(f"Rate limited (attempt {attempt}/{MAX_RETRIES}) - waiting {wait}s before retry.")
            time.sleep(wait)
            continue
        except anthropic.APIConnectionError:
            wait = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
            print(f"Connection error (attempt {attempt}/{MAX_RETRIES}) - waiting {wait}s before retry.")
            time.sleep(wait)
            continue
        except anthropic.APIStatusError as e:
            # 4xx errors (e.g. bad auth) won't fix themselves on retry - fail fast
            if 400 <= e.status_code < 500:
                raise
            wait = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
            print(f"API error {e.status_code} (attempt {attempt}/{MAX_RETRIES}) - waiting {wait}s.")
            time.sleep(wait)
            continue

        issues = validate_output(result)
        last_result, last_issues = result, issues

        if not issues:
            return result  # success - no need to retry

        if attempt < MAX_RETRIES:
            correction_note = "; ".join(issues)
            print(f"Validation failed (attempt {attempt}/{MAX_RETRIES}): {correction_note}")

    # Exhausted retries - return the best attempt, flagged rather than silently accepted
    last_result["_validation_issues"] = last_issues
    return last_result