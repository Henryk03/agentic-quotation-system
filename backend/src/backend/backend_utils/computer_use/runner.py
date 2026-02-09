
from google import genai
from google.genai.types import Content, Candidate
from playwright.async_api import Page

from backend.backend_utils.computer_use.session import ComputerUseSession
from backend.backend_utils.computer_use.parsing import is_final_response, extract_text
from backend.backend_utils.computer_use.functions import (
    execute_function_calls,
    get_function_responses
)


async def run_computer_use_loop(
        client: genai.Client,
        page: Page,
        session: ComputerUseSession,
        config: genai.types.GenerateContentConfig,
        max_iter: int = 10
    ) -> str | None:

    for _ in range(max_iter):
        response: genai.types.GenerateContentResponse = (
            client.models.generate_content(
                model="gemini-2.5-computer-use-preview-10-2025",
                contents=session.contents,
                config=config,
            )
        )

        print(f"COMPUTER USE: risposta dall'IA {response}")

        candidate: Candidate = response.candidates[0]
        session.add_model_candidate(candidate)

        if is_final_response(candidate):
            return extract_text(candidate)

        results = await execute_function_calls(candidate, page)
        print(f"COMPUTER USE: risultati {results}")
        function_responses = await get_function_responses(page, results)
        session.add_function_responses(function_responses)

    return None