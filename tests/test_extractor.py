"""
Test skeleton - fill in properly during Week 4 (validation/testing pass).
For now, one smoke test to confirm the scaffold actually runs end to end.
"""

from resume_parser import extract_resume

SAMPLE_RESUME = """
Sarah Chen
sarah.chen@email.com | (555) 123-4567

SKILLS: Python, AWS, Kubernetes, LangChain


EDUCATION
B.S. Computer Science, University of Sydney, 2015
"""


def test_extract_resume_smoke_test():
    result = extract_resume(SAMPLE_RESUME)
    assert result["name"] == "Sarah Chen"
    assert ".net" in result["skills"]
    assert len(result["work_history"]) >= 1
    assert len(result["education"]) >= 1


if __name__ == "__main__":
    test_extract_resume_smoke_test()
    print("Smoke test passed.")
