
import asyncio

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    StorageState
)

from shared.provider.base_provider import BaseProvider
from shared.provider.registry import get_provider
from shared.playwright.waiter import wait_until_logged_in
from shared.playwright.page_utilities import close_page_resources


async def run_manual_login(
        provider: str,
        url: str
    ) -> StorageState | None:
    """"""

    provider_instance: BaseProvider = get_provider(provider)

    if provider_instance.url != url:
        raise ValueError(
            f"URL mismatch: expected {provider_instance.url}, got {url}"
        )
    
    browser: Browser | None = None
    context: BrowserContext | None = None
    page: Page | None = None

    try:
        async with async_playwright() as apw:
            browser = await apw.chromium.launch(
                headless=False, 
                channel="chrome"
            )
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(url)

            if await wait_until_logged_in(
                page=page,
                check_func=provider_instance.is_logged_in,
                timeout=120000
            ):
                storage: StorageState = await context.storage_state()
                await asyncio.sleep(1)
                await close_page_resources(page)

                return storage
            
            await close_page_resources(page)
            return None
            
    except:
        if browser:
            await browser.close()

        raise