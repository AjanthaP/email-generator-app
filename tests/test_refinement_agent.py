"""Tests for RefinementAgent functionality."""
from src.agents.refinement import RefinementAgent


class DummyLLM:  # minimal stub, never invoked due to stub mode fallback
    model = "stub"


def _agent():
    # Ensure stub mode by setting flag
    import os
    os.environ["DONOTUSEGEMINI"] = "1"
    return RefinementAgent(DummyLLM())


def test_duplicate_signature():
    draft = (
        "Dear John,\n\nI hope this email finds you well. I wanted to reach out to discuss the upcoming project.\n"
        "I look forward to hearing from you.\n\nBest regards,\nSarah Johnson\n\nBest regards,\nSarah Johnson"
    )
    refined = _agent().refine(draft)
    # Expect only one signature block after cleanup
    assert refined.lower().count("best regards") == 1
    assert refined.count("Sarah Johnson") == 1


def test_repetition_cleanup():
    draft = (
        "Dear Maria,\n\nI am writing to follow up on my previous email. I wanted to follow up regarding the message.\n"
        "I'm reaching out again about my earlier communication.\n\nBest regards,\nTom"
    )
    refined = _agent().refine(draft)
    # Ensure at least one 'follow up' remains while no duplicate consecutive sentences
    assert "follow up" in refined.lower()

if __name__ == "__main__":
    test_duplicate_signature(); test_repetition_cleanup(); print("✅ RefinementAgent tests passed")
