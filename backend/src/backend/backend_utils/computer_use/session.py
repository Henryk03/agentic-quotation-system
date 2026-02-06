
from google.genai.types import (
    Content, 
    Part
)


class ComputerUseSession:
    """"""


    def __init__(
            self,
            user_prompt: str, 
            initial_screenshot: bytes
        ):

        self._contents: list[Content] = [
            Content(
                role="user",
                parts=[
                    Part(text=user_prompt),
                    Part.from_bytes(
                        data=initial_screenshot,
                        mime_type="image/png"
                    )
                ]
            )
        ]


    @property
    def contents(
            self
        ) -> list[Content]:
        """"""

        return self._contents


    def add_model_candidate(
            self, 
            candidate: Content
        ) -> None:
        """"""

        self._contents.append(candidate)


    def add_function_responses(
            self, 
            responses: list
        ) -> None:
        """"""
        
        self._contents.append(
            Content(
                role="user",
                parts=[Part(function_response=r) for r in responses]
            )
        )