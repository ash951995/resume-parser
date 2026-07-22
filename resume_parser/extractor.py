"""
Core extraction logic for the resume parser.

Scaffolded Wednesday (Week 3) - schema and basic extraction only.
Thursday adds: input validation + schema validation on output. (DONE)
Friday adds: retry logic for malformed outputs + error handling.
(Following your existing Phase 1, Week 4 plan.)
"""

from .client import call_claude
from .schema import RESUME_EXTRACTION_TOOL
from .validators import validate_input, validate_output, ValidationError


def extract_resume(resume_text: str) -> dict:
    """
    Extract structured data from raw resume text.

    Raises ValidationError if input fails basic sanity checks.
    Returns a dict with an added "_validation_issues" key if the model's
    output doesn't fully match the expected schema - callers can decide
    whether to use the partial result or treat it as a failure.

    TODO (Fri): wrap in retry logic if the model returns something malformed
    TODO (Fri): log token usage / estimated cost per call
    """
    # Input validation - defend against wasted/malicious calls before hitting the API
    validate_input(resume_text)

    response = call_claude(
        messages=[
            {"role": "user", "content": f"Extract structured data from this resume:\n\n{resume_text}"}
        ],
        system="You are a resume parsing assistant. Extract candidate information accurately. "
               "If a field genuinely isn't present, use an empty string or empty array rather than guessing.",
        tools=[RESUME_EXTRACTION_TOOL],
        tool_choice={"type": "tool", "name": "extract_resume_data"},
        max_tokens=1500,
    )

    result = {}
    for block in response.content:
        if block.type == "tool_use":
            result = block.input
            break

    # Output validation - defend against LLM02/LLM05 (Improper Output Handling):
    # never trust the model's output structure blindly before it's used downstream.
    issues = validate_output(result)
    if issues:
        result["_validation_issues"] = issues

    return result