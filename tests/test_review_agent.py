from types import SimpleNamespace

from src.agents.review import ReviewAgent


def test_extract_response_text_from_content_blocks():
    response = SimpleNamespace(content=[
        {"type": "text", "text": "Dear Jane,"},
        {"type": "image", "data": "ignored"},
        {"type": "text", "text": "Best regards"},
    ])

    assert ReviewAgent._extract_response_text(response) == "Dear Jane,\nBest regards"


def test_extract_response_text_from_string():
    response = SimpleNamespace(content="  Reviewed draft  ")

    assert ReviewAgent._extract_response_text(response) == "Reviewed draft"
