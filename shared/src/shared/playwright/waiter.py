
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
    Wait until the user is logged in on a webpage.

    The function repeatedly calls `check_func` on the given
    Playwright page until it returns True or the timeout expires.

    Parameters
    ----------
    page : Page
        A Playwright page representing the website where login occurs.

    check_func : Callable[[Page], Awaitable[bool]]
        An async function that checks if the user is logged in.
        Should return True when login is detected, False otherwise.

    timeout : float, optional
        Maximum time to wait for login in milliseconds. Default is 15000 ms.

    interval : float, optional
        Interval between checks in milliseconds. Default is 500 ms.

    Returns
    -------
    bool
        True if login was detected within the timeout, False otherwise.

    Notes
    -----
    - The function uses asyncio sleep to wait between checks.
    - Time measurement is based on asyncio event loop's internal clock.
    """

    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    start: float = loop.time()

    while True:
        if await check_func(page):
            return True
        
        if (loop.time() - start) * 1000 > timeout:
            return False
        
        await asyncio.sleep(interval / 1000)