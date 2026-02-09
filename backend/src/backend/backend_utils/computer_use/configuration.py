
from google import genai
from google.genai import types


async def generate_content_config(
        system_prompt: str | None = None,
        excluded_functions: list[str] | None = None
    ) -> genai.types.GenerateContentConfig:
    """"""

    return genai.types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[
            types.Tool(
                computer_use=types.ComputerUse(
                    environment=types.Environment.ENVIRONMENT_BROWSER,
                    excluded_predefined_functions=excluded_functions
                )
            )
        ]
    )