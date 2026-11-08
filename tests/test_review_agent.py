from types import SimpleNamespace

from src.utils.llm_response import extract_response_text


def test_extract_response_text_from_content_blocks():
    response = SimpleNamespace(content=[
        {"type": "text", "text": "Dear Jane,"},
        {"type": "image", "data": "ignored"},
        {"type": "text", "text": "Best regards"},
    ])

    assert extract_response_text(response) == "Dear Jane,\nBest regards"


def test_extract_response_text_from_string():
    response = SimpleNamespace(content="  Reviewed draft  ")

    assert extract_response_text(response) == "Reviewed draft"
