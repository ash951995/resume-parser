"""
Input and output validation for the resume parser.

Directly addresses this week's OWASP reading:
- Input validation: basic cost/sanity control before calling the API.
- Output validation: defends against LLM02/LLM05 (Improper Output Handling)
  by never trusting the model's output structure blindly before it's used
  downstream (e.g. inserted into a database, displayed in a UI).
"""


class ValidationError(Exception):
    """Raised when input or output fails validation."""
    pass


MIN_INPUT_LENGTH = 50       # below this, there's nothing useful to extract
MAX_INPUT_LENGTH = 20_000   # cost control - roughly a very long multi-page resume


def validate_input(resume_text: str) -> None:
    """Validate raw resume text before sending it to the API. Raises ValidationError on failure."""
    if not resume_text or not resume_text.strip():
        raise ValidationError("Resume text is empty.")

    if len(resume_text) < MIN_INPUT_LENGTH:
        raise ValidationError(
            f"Resume text is too short ({len(resume_text)} chars) to contain meaningful data."
        )

    if len(resume_text) > MAX_INPUT_LENGTH:
        raise ValidationError(
            f"Resume text is too long ({len(resume_text)} chars) - exceeds {MAX_INPUT_LENGTH} char limit. "
            "Consider truncating or splitting before extraction."
        )


REQUIRED_TOP_LEVEL_FIELDS = {
    "name": str,
    "email": str,
    "phone": str,
    "skills": list,
    "work_history": list,
    "education": list,
}

REQUIRED_WORK_HISTORY_FIELDS = {"company", "title", "start_date", "end_date"}
REQUIRED_EDUCATION_FIELDS = {"institution", "degree"}


def validate_output(data: dict) -> list[str]:
    """
    Validate the model's extracted output against the expected schema shape.

    Returns a list of validation issues (empty list = fully valid).
    Deliberately returns issues rather than raising immediately - callers
    decide whether a partially-valid result is still usable, or whether to
    retry (Friday's task builds on this).
    """
    issues = []

    if not isinstance(data, dict):
        return [f"Expected a dict, got {type(data).__name__}"]

    # Check top-level required fields and types
    for field, expected_type in REQUIRED_TOP_LEVEL_FIELDS.items():
        if field not in data:
            issues.append(f"Missing required field: '{field}'")
            continue
        if not isinstance(data[field], expected_type):
            issues.append(
                f"Field '{field}' has wrong type: expected {expected_type.__name__}, "
                f"got {type(data[field]).__name__}"
            )

    # Check nested work_history entries
    if isinstance(data.get("work_history"), list):
        for i, entry in enumerate(data["work_history"]):
            if not isinstance(entry, dict):
                issues.append(f"work_history[{i}] is not a dict")
                continue
            missing = REQUIRED_WORK_HISTORY_FIELDS - entry.keys()
            if missing:
                issues.append(f"work_history[{i}] missing fields: {missing}")

    # Check nested education entries
    if isinstance(data.get("education"), list):
        for i, entry in enumerate(data["education"]):
            if not isinstance(entry, dict):
                issues.append(f"education[{i}] is not a dict")
                continue
            missing = REQUIRED_EDUCATION_FIELDS - entry.keys()
            if missing:
                issues.append(f"education[{i}] missing fields: {missing}")

    # Flag suspicious placeholder-looking values (a common hallucination pattern
    # when a field is genuinely missing from the source text)
    suspicious_values = {"n/a", "unknown", "not provided", "not specified", "none", ""}
    if data.get("name", "").strip().lower() in suspicious_values:
        issues.append("'name' field looks like a placeholder rather than a real extracted value")

    return issues