
from typing import Iterable

from google.genai.types import (
    Candidate,
    Content,
    FunctionResponse, 
    Part
)


class ComputerUseSession:
    """
    Represents a session of model-driven computer interactions.

    Maintains a list of `Content` objects representing user prompts,
    screenshots, model-generated candidates, and tool responses.
    """


    def __init__(
            self,
            user_prompt: str, 
            initial_screenshot: bytes
        ):
        """
        Initialize a new computer use session.

        Parameters
        ----------
        user_prompt : str
            Initial prompt from the user describing the tasks or queries.

        initial_screenshot : bytes
            Screenshot of the initial browser state encoded as PNG.
        """

        self._contents: list[Content] = [
            Content(
                role = "user",
                parts = [
                    Part(text = user_prompt),
                    Part.from_bytes(
                        data = initial_screenshot,
                        mime_type = "image/png"
                    )
                ]
            )
        ]


    @property
    def contents(
            self
        ) -> list[Content]:
        """
        Return the current list of contents in the session.

        Returns
        -------
        list of Content
            The chronological list of content objects representing
            user prompts, screenshots, model candidates, and tool 
            responses.
        """

        return self._contents


    def add_model_candidate(
            self, 
            candidate: Candidate
        ) -> None:
        """
        Append a model-generated candidate to the session contents.

        Parameters
        ----------
        candidate : Candidate
            Candidate object produced by the model, which may include
            generated text or function calls.
        """

        if candidate.content:
            self._contents.append(candidate.content)


    def add_function_responses(
            self,
            responses: Iterable[FunctionResponse]
        ) -> None:
        """
        Append function/tool responses to the session contents.

        Each response is wrapped into a Content object with role 'tool'.

        Parameters
        ----------
        responses : iterable of FunctionResponse
            Responses returned from executing model-instructed functions
            on the browser or other tools.
        """
        
        self._contents.append(
            Content(
                role = "tool",
                parts = [
                    Part(function_response = response) 
                    for response in responses
                ]
            )
        )