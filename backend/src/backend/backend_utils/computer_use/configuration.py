
from typing import Callable, Any

from google import genai
from google.genai import types


def generate_content_config(
        client: genai.Client,
        system_prompt: str | None = None,
        excluded_functions: list[str] | None = None,
        custom_functions: list[Callable[..., Any]] | None = None
    ) -> genai.types.GenerateContentConfig:
    """"""

    all_tools: list[Any] = []

    browser_tool = types.Tool(
        computer_use=types.ComputerUse(
            environment=types.Environment.ENVIRONMENT_BROWSER,
            excluded_predefined_functions=excluded_functions
        )
    )

    all_tools.append(browser_tool)

    if custom_functions:
        custom_functions_declarations = [
            types.FunctionDeclaration.from_callable(
                client=client, 
                callable=func
            ) for func in custom_functions
        ]

        all_tools.append(
            types.Tool(function_declarations=custom_functions_declarations)
        )

    return genai.types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=all_tools
    )