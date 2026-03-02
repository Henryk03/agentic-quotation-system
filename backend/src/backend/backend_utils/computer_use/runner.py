

from playwright.async_api import Page
from google.genai import Client
from google.genai.types import (
    GenerateContentResponse, 
    GenerateContentConfig, 
    Candidate
)

from backend.backend_utils.computer_use.session import ComputerUseSession
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
    """
    Run an iterative loop where the model interacts with the 
    browser.

    In each iteration, the model generates content using the 
    provided session contents and configuration. The resulting 
    candidate is used to perform browser actions, and results 
    are recorded and added to the session.

    Parameters
    ----------
    client : Client
        Google GenAI client used to generate content.

    page : Page
        Playwright page instance used to execute browser actions.

    session : ComputerUseSession
        Object maintaining the conversation and action history.

    config : GenerateContentConfig
        Configuration specifying system prompts, tools, and allowed 
        functions.

    result_list : list of dict
        List where product results are appended after execution.

    max_iter : int, optional
        Maximum number of iterations to run the loop. Defatult to 
        10.

    Returns
    -------
    None
        The function modifies the session and result_list in-place.
    """

    for _ in range(max_iter):
        response: GenerateContentResponse = (
            client.models.generate_content(
                model = "gemini-3-flash-preview",
                contents = session.contents,
                config = config,
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