# Resume Parser (Project 1)

Extracts structured candidate data (contact info, skills, work history,
education) from unstructured resume text, using Claude's tool-use feature
to force schema-conformant output.

## Status: Week 3, Wednesday — scaffolded, extraction logic works but
validation, retry logic, and cost logging are not yet implemented
(coming Week 3 Thu/Fri).

## Setup

pip install -r requirements.txt

Copy .env.example to .env and add your real Anthropic API key.

## Usage

    from resume_parser import extract_resume
    result = extract_resume(resume_text)

## Design notes

- Schema (resume_parser/schema.py) is deliberately nested (work_history,
  education as arrays of objects) — more realistic than a flat schema,
  and the reason this project exists as a step up from the earlier
  ticket-classifier exercise.
- Uses tool_choice to force schema-conformant output (see Week 1 Friday's
  structured_extraction.py for the same underlying pattern).
- Security note (per Week 3's OWASP reading): resume text is untrusted
  input. If this were ever wired into a real ATS/database, the extracted
  output would need validation before being used downstream (see LLM01/LLM02
  notes) — not yet implemented, flagged here deliberately as a known gap.
