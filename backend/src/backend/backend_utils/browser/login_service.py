
from playwright.async_api import (
    async_playwright,
    StorageState,
    BrowserContext, 
    Page
)

from backend.backend_utils.browser import AsyncBrowserContextMaganer

from shared.provider.base_provider import BaseProvider
from shared.provider.registry import get_provider


async def validate_credentials(
        store: str,
        username: str, 
        password: str
    ) -> tuple[bool, StorageState | None, str | None]:
    """"""

    manager: AsyncBrowserContextMaganer

    success: bool = False
    storage_state: StorageState | str | None = None
    error_message: str | None = None

    context: BrowserContext | None = None
    page: Page | None = None

    store_instance: BaseProvider = get_provider(
        provider_name = store
    )

    async with async_playwright() as apw:
        manager = AsyncBrowserContextMaganer(apw)

        _, context, page = await manager.create_browser_context(
            start_url = store_instance.url
        )

        success = await store_instance.auto_login(
            page,
            username,
            password
        )

        if success:
            storage_state = await context.storage_state()

            return (success, StorageState(storage_state), None)
        
        else:
            error_message = "Invalid credentials."

            return (success, None, error_message)