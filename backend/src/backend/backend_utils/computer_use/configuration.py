
from typing import Any, Callable

from google import genai
from google.genai import types


def generate_content_config(
        client: genai.Client,
        system_prompt: str | None = None,
        excluded_functions: list[str] | None = None,
        custom_functions: list[Callable[..., Any]] | None = None
    ) -> genai.types.GenerateContentConfig:
    """
    Build a configuration object for Google Generative AI 
    content generation.

    The configuration includes system instructions, pre-defined
    tools for browser automation, and optionally user-provided
    custom functions.

    Parameters
    ----------
    client : genai.Client
        The initialized Google GenAI client used to generate
        function declarations for custom functions.

    system_prompt : str or None, optional
        System-level instructions to guide the model behavior.
        Default is None.

    excluded_functions : list of str or None, optional
        Names of pre-defined functions to exclude from
        the model's accessible toolset. Default is None.

    custom_functions : list of callable or None, optional
        Python callables that will be exposed to the model as
        function declarations. Default is None.

    Returns
    -------
    genai.types.GenerateContentConfig
        A configuration object containing system instructions
        and all included tools (browser + optional custom functions).

    Notes
    -----
    - The browser tool is always included, with its environment
      set to `ENVIRONMENT_BROWSER`.
    - Custom functions, if provided, are converted to
      `FunctionDeclaration` instances before being added.
    """

    all_tools: list[Any] = []

    browser_tool = types.Tool(
        computer_use = types.ComputerUse(
            environment = types.Environment.ENVIRONMENT_BROWSER,
            excluded_predefined_functions = excluded_functions
        )
    )

    all_tools.append(browser_tool)

    if custom_functions:
        custom_functions_declarations = [
            types.FunctionDeclaration.from_callable(
                client = client, 
                callable = func
            ) for func in custom_functions
        ]

        all_tools.append(
            types.Tool(
                function_declarations = custom_functions_declarations
            )
        )

    return genai.types.GenerateContentConfig(
        system_instruction = system_prompt,
        tools = all_tools
    )