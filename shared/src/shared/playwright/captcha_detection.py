
import re

from playwright.async_api import (
    ElementHandle,
    Page, 
    TimeoutError as PlaywrightTimeoutError
)

from shared.playwright.page_utilities import find_elements_with_attr_pattern


async def detect_captcha(
        page: Page
    ) -> bool:
    """
    Detect the presence of captchas on a webpage.

    This function searches for captchas by inspecting iframe URLs and 
    specific HTML elements that may indicate captcha challenges.

    Parameters
    ----------
    page : Page
        The Playwright page object representing the webpage to inspect.

    Returns
    -------
    bool
        - `True` if a captcha is detected.
        - `False` if no captcha is found.

    Notes
    -----
    Detection is heuristic and may produce false positives or negatives.
    Some captchas embedded in non-standard HTML may not be detected.
    """

    captcha_text: re.Pattern[str] = re.compile(
        r"captcha|not robot|non robot",
        re.IGNORECASE
    )

    try:
        await page.wait_for_selector("iframe", timeout=1000)
        for frame in page.frames:
            if frame is not page.main_frame:
                url: str = frame.url or ""

                if re.search(captcha_text, url):
                    return True
                
    except PlaywrightTimeoutError:
        pass

    except Exception:
        return True

    try:
        tag_texts: list[str] = [
            "div",
            "img",
            "li"
        ]

        results: list[ElementHandle] = (
            await find_elements_with_attr_pattern(
                page,
                tag_texts,
                captcha_text,
                early_end=True
            )
        )

        if results == []:
            return False
        
        else:
            return True

    except: 
        return True