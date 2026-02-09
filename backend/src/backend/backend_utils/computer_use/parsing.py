
from google.genai.types import Candidate


def is_final_response(
        candidate: Candidate
    ) -> bool:
    """"""

    return not any(
        part.function_call for part in candidate.content.parts
    )


def extract_text(
        candidate: Candidate
    ) -> str:
    """"""
    
    return " ".join(
        part.text for part in candidate.content.parts if part.text
    )