
from google.genai.types import Content


def is_final_response(
        candidate: Content
    ) -> bool:
    """"""

    return not any(
        part.function_call for part in candidate.content.parts
    )


def extract_text(
        candidate: Content
    ) -> str:
    """"""
    
    return " ".join(
        part.text for part in candidate.content.parts if part.text
    )