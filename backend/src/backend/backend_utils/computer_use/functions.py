
import platform

from playwright.async_api import Page
from google.genai import types
from google.genai.types import Candidate


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

    results = []
    function_calls = []

    page_viewport = await page.evaluate(
        """
        () => ({
            innerWidth: window.innerWidth,
            innerHeight: window.innerHeight
        })
        """
    )

    for part in candidate.content.parts:
        if part.function_call:
            function_calls.append(part.function_call)

    for function_call in function_calls:
        action_result = {}
        fname = function_call.name
        args = function_call.args

        try:
            match fname:
                case "open_web_browser":
                    pass

                case "click_at":
                    actual_x = await denormalize_x(args["x"], page_viewport["width"])
                    actual_y = await denormalize_y(args["y"], page_viewport["height"])

                    await page.mouse.click(actual_x, actual_y)

                case "type_text_at":
                    actual_x = await denormalize_x(args["x"], page_viewport["width"])
                    actual_y = await denormalize_y(args["y"], page_viewport["height"])

                    text = args["text"]

                    press_enter = args.get("press_enter", False)

                    await page.mouse.click(actual_x, actual_y)

                    if platform.system().lower() == "darwin":
                        await page.keyboard.press("Command+A")

                    else:
                        await page.keyboard.press("Meta+A")

                    await page.keyboard.press("Backspace")

                    await page.keyboard.type(text)
                    
                    if press_enter:
                        await page.keyboard.press("Enter")

                case _:
                    print("Non so fare questa azione ancora...")

            await page.wait_for_load_state("networkidle")

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