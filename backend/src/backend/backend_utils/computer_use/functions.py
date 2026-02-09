
import asyncio
from typing import Any

from playwright.async_api import Page
from google.genai import types
from google.genai.types import (
    Candidate,
    FunctionCall
)


async def denormalize_x(
        x: int,
        screen_width: int
    ) -> int:
    """Convert normalized x coordinate (0-1000) to actual pixel coordinate."""

    return int(x / 1000 * screen_width)


async def denormalize_y(
        y: int,
        screen_height: int
    ) -> int:
    """Convert normalized y coordinate (0-1000) to actual pixel coordinate."""

    return int(y / 1000 * screen_height)


async def execute_function_calls(
        candidate: Candidate,
        page: Page
    ) -> list[tuple[str, dict]]:
    """"""

    results: list[tuple[str, dict]] = []
    function_calls: list[FunctionCall] = []

    page_viewport: dict[str, int] = await page.evaluate(
        """
        () => ({
            width: window.innerWidth,
            height: window.innerHeight
        })
        """
    )

    for part in candidate.content.parts:
        if part.function_call:
            function_calls.append(part.function_call)

    for function_call in function_calls:
        action_result: dict = {}
        fname: str | None = function_call.name
        args: dict[str, Any] | None = function_call.args

        try:
            match fname:
                case "click_at":
                    actual_x: int = await denormalize_x(args["x"], page_viewport["width"])
                    actual_y: int = await denormalize_y(args["y"], page_viewport["height"])

                    await asyncio.sleep(1)
                    await page.mouse.click(actual_x, actual_y)

                case "type_text_at":
                    actual_x = await denormalize_x(args["x"], page_viewport["width"])
                    actual_y = await denormalize_y(args["y"], page_viewport["height"])

                    text: str = args["text"]
                    press_enter: bool = args["press_enter"]

                    await page.mouse.click(actual_x, actual_y)

                    await page.keyboard.press("ControlOrMeta+A")
                    await asyncio.sleep(1)
                    await page.keyboard.press("Backspace")

                    await page.keyboard.type(text, delay=500)
                    await asyncio.sleep(1)
                    
                    if press_enter:
                        await page.keyboard.press("Enter")

                case "wait_5_seconds":
                    await asyncio.sleep(5)

                case "go_back":
                    await asyncio.sleep(1)
                    await page.go_back()

                case "go_forward":
                    await asyncio.sleep(1)
                    await page.go_forward()

                case _:
                    print("Non so fare questa azione ancora...")

            await page.wait_for_load_state("networkidle", timeout=10)

        except Exception as e:
            action_result = {"error": str(e)}

        results.append((fname, action_result))

    return results


async def get_function_responses(
        page: Page,
        results: list[tuple[str, dict]]
    ) -> list[types.FunctionResponse]:
    """"""

    screenshot_bytes = await page.screenshot(type="png")
    current_url = page.url
    function_responses = []

    for name, result in results:
        response_data = {"url": current_url}
        response_data.update(result)

        function_responses.append(
            types.FunctionResponse(
                name=name,
                response=response_data,
                parts=[
                    types.FunctionResponsePart(
                        inline_data=types.FunctionResponseBlob(
                            mime_type="image/png",
                            data=screenshot_bytes)
                    )
                ]
            )
        )

    return function_responses