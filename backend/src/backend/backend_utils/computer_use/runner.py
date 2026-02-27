
from playwright.async_api import Page
from google.genai import Client
from google.genai.types import (
    GenerateContentResponse,
    GenerateContentConfig,
    Candidate
)

from backend.backend_utils.common import SafeAsyncList
from backend.backend_utils.computer_use.session import ComputerUseSession
from backend.backend_utils.computer_use.parsing import is_final_response, extract_text
from backend.backend_utils.computer_use.functions import (
    execute_function_calls,
    get_function_responses
)


async def run_computer_use_loop(
        client: Client,
        page: Page,
        session: ComputerUseSession,
        config: GenerateContentConfig,
        result_list: list[dict[str, str]],
        max_iter: int = 10
    ) -> None:
    """"""

    for _ in range(max_iter):
        response: GenerateContentResponse = (
            client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=session.contents,
                config=config,
            )
        )

        candidate: Candidate = response.candidates[0]
        session.add_model_candidate(candidate)

        results = await execute_function_calls(
            candidate, 
            page,
            result_list
        )
        function_responses = await get_function_responses(
            page, 
            results, 
        )
        session.add_function_responses(function_responses)