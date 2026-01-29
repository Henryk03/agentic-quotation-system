
import re

from playwright.async_api import (
    Page, 
    ElementHandle,
    TimeoutError as PlaywrightTimeoutError
)

from shared.playwright.page_utilities import find_elements_with_attr_pattern


async def detect_captcha(
        page: Page
    ) -> bool:
    """
    Detect the presence of captchas in the given webpage.

    Args:
        page (Page):
            The webpage in which the detection is performed.

    Returns:
        bool | str
        - `True` if at least a captcha is detected.
        - `False` if no captcha was detected.
    """

    captcha_text: re.Pattern[str] = re.compile(
        r"captcha|not robot|non robot",
        re.IGNORECASE
    )

    try:
        # we firstly check all the iframes that
        # could refer to a captcha
        #
        # note that the following chunk of code
        # could not catch all the iframes
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
        # some captchas may be hidden
        # into other html tags
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