"""
Tool schema for structured resume extraction.

This is deliberately more complex than the flat schema used in
structured_extraction.py and ticket_classifier.py — nested arrays and
objects (work_history, education) are the real-world case, and are
what this project is meant to prove out.
"""

RESUME_EXTRACTION_TOOL = {
    "name": "extract_resume_data",
    "description": "Extract structured candidate information from resume text.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Candidate's full name"},
            "email": {"type": "string", "description": "Candidate's email address, or empty string if not found"},
            "phone": {"type": "string", "description": "Candidate's phone number, or empty string if not found"},
            "skills": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of skills/technologies mentioned",
            },
            "work_history": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "company": {"type": "string"},
                        "title": {"type": "string"},
                        "start_date": {"type": "string", "description": "e.g. 'Jan 2020' or '2020'"},
                        "end_date": {"type": "string", "description": "e.g. 'Mar 2023', or 'Present' if current role"},
                        "description": {"type": "string", "description": "Brief summary of role, or empty string"},
                    },
                    "required": ["company", "title", "start_date", "end_date"],
                },
            },
            "education": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "institution": {"type": "string"},
                        "degree": {"type": "string"},
                        "graduation_year": {"type": "string", "description": "e.g. '2015', or empty string if not found"},
                    },
                    "required": ["institution", "degree"],
                },
            },
        },
        "required": ["name", "email", "phone", "skills", "work_history", "education"],
    },
}
