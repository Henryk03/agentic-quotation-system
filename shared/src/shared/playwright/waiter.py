
import asyncio
from typing import Callable, Awaitable

from playwright.async_api import Page


async def wait_until_logged_in(
        page: Page,
        check_func: Callable[[Page], Awaitable[bool]],
        timeout: float = 15000,
        interval: float = 500
    ) -> bool:
    """
    Wait until the user is logged-in into the given
    provider's website.

    Args:
        provider (BaseProvider):
            A provider for whom a login is required.

        page (Page):
            A page at the given provider's website.

        check_func (Callable[[BaseProvider, Page], bool]):
            A function used to check if the user is logged-in
            into the website.

        timeout (float | None):
            The time given (in milliseconds) to the user to 
            fulfill the login. Default is 15000 ms.

        interval (float | None):
            The time (in milliseconds) between one check
            and another. Default is 500 ms.

    Returns:
        bool:
        - `True` if the login has been successfully fulfilled 
            within the timeout.
        - `False` otherwise.
    """

    # we start to record the time passed
    # since the beginning of the `while` loop
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    start: float = loop.time()

    while True:
        if await check_func(page):
            return True
        
        if (loop.time() - start) * 1000 > timeout:
            return False
        
        # sleep accepts seconds as parameter
        await asyncio.sleep(interval / 1000)