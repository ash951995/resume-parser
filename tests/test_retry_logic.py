"""
Tests for retry logic - uses mocking so we can simulate malformed outputs
and API errors without burning real API calls or needing network access.
"""

from unittest.mock import patch
import anthropic
from resume_parser.extractor import extract_resume
from resume_parser.validators import ValidationError
import pytest


GOOD_RESULT = {
    "name": "Sarah Chen", "email": "sarah@email.com", "phone": "555-1234",
    "skills": ["Python", "AWS"],
    "work_history": [{"company": "Atlassian", "title": "Engineer", "start_date": "2020", "end_date": "Present"}],
    "education": [{"institution": "USyd", "degree": "B.S. CS"}],
}

BAD_RESULT = {"name": "Sarah Chen"}  # missing required fields


def test_rejects_bad_input_without_calling_api():
    # Input validation should fail fast, before any API call happens
    with pytest.raises(ValidationError):
        extract_resume("")


@patch("resume_parser.extractor._call_model")
def test_succeeds_immediately_with_good_output(mock_call):
    mock_call.return_value = GOOD_RESULT
    result = extract_resume("A" * 200)
    assert result == GOOD_RESULT
    assert mock_call.call_count == 1  # no retry needed


@patch("resume_parser.extractor._call_model")
def test_retries_on_validation_failure_then_succeeds(mock_call):
    # First call returns bad data, second call (after correction feedback) succeeds
    mock_call.side_effect = [BAD_RESULT, GOOD_RESULT]
    result = extract_resume("A" * 200)
    assert result == GOOD_RESULT
    assert mock_call.call_count == 2

    # Confirm the second call actually received correction feedback
    second_call_args = mock_call.call_args_list[1]
    assert "correction_note" in second_call_args.kwargs or len(second_call_args.args) > 1


@patch("resume_parser.extractor._call_model")
def test_gives_up_after_max_retries_but_returns_flagged_result(mock_call):
    mock_call.return_value = BAD_RESULT  # always bad, every attempt
    result = extract_resume("A" * 200)
    assert "_validation_issues" in result
    assert mock_call.call_count == 3  # MAX_RETRIES


@patch("resume_parser.extractor._call_model")
@patch("resume_parser.extractor.time.sleep")  # don't actually wait during tests
def test_retries_on_rate_limit_error(mock_sleep, mock_call):
    # RateLimitError needs a real-ish response object with a .request attribute -
    # a bare MagicMock satisfies that without needing an actual HTTP response.
    from unittest.mock import MagicMock
    fake_response = MagicMock()
    fake_response.request = MagicMock()

    rate_limit_error = anthropic.RateLimitError(
        message="rate limited", response=fake_response, body=None
    )
    mock_call.side_effect = [rate_limit_error, GOOD_RESULT]
    result = extract_resume("A" * 200)
    assert result == GOOD_RESULT
    mock_sleep.assert_called_once()  # confirms backoff was actually applied