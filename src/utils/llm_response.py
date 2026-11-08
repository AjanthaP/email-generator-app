from typing import Any


def extract_response_text(response: Any) -> str:
    """Extract text from string or multimodal LangChain response content."""
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts = [
            block["text"]
            for block in content
            if isinstance(block, dict) and isinstance(block.get("text"), str)
        ]
        return "\n".join(text_parts).strip()
    return str(content).strip() if content is not None else ""
