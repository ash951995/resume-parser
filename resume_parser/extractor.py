"""
Core extraction logic for the resume parser.

Scaffolded Wednesday (Week 3) - schema and basic extraction only.
Thursday adds: input validation + schema validation on output.
Friday adds: retry logic for malformed outputs + error handling.
(Following your existing Phase 1, Week 4 plan.)
"""

from .client import call_claude
from .schema import RESUME_EXTRACTION_TOOL


def extract_resume(resume_text: str) -> dict:
    """
    Extract structured data from raw resume text.

    TODO (Thu): validate resume_text isn't empty/too short before calling the API
    TODO (Thu): validate the returned dict actually matches the expected schema shape
    TODO (Fri): wrap in retry logic if the model returns something malformed
    TODO (Fri): log token usage / estimated cost per call
    """
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

    for block in response.content:
        if block.type == "tool_use":
            return block.input

    return {}  # shouldn't happen with tool_choice forcing the tool
