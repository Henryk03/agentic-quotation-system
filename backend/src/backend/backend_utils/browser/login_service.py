
from playwright.async_api import (
    BrowserContext,
    Page,
    StorageState,
    async_playwright,
)

from backend.backend_utils.browser import AsyncBrowserContextMaganer

from shared.provider.base_provider import BaseProvider
from shared.provider.registry import get_provider


async def execute_autologin(
        store: str,
        username: str,
        password: str
    ) -> tuple[bool, StorageState | None]:
    """
    Attempt automatic login for a provider and return its storage state.

    A new browser context is created, the provider's login
    routine is executed, and if successful, the authenticated
    storage state is extracted from the context.

    Parameters
    ----------
    store : str
        Identifier of the provider to authenticate against.

    username : str
        Username used for authentication.

    password : str
        Password used for authentication.

    Returns
    -------
    tuple of (bool, StorageState or None)
        A tuple containing:

        - A boolean indicating whether login succeeded.
        - The authenticated ``StorageState`` if successful,
          otherwise ``None``.

    Raises
    ------
    Exception
        Propagates any unexpected errors raised during
        browser initialization or provider interaction.
    """

    manager: AsyncBrowserContextMaganer
    page: Page
    context: BrowserContext

    success: bool = False
    storage_state: StorageState | None = None
    store_instance: BaseProvider = get_provider(
        store
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

            return (
                success, 
                storage_state
            )

    return (
        success,
        storage_state
    )


async def validate_credentials(
        store: str,
        username: str, 
        password: str
    ) -> tuple[bool, StorageState | None, str | None]:
    """
    Validate user credentials for a provider.

    The function attempts automatic login using the provided
    credentials. If authentication succeeds, the resulting
    storage state is returned. Otherwise, an error message
    is provided.

    Parameters
    ----------
    store : str
        Identifier of the provider to authenticate against.

    username : str
        Username used for authentication.

    password : str
        Password used for authentication.

    Returns
    -------
    tuple of (bool, StorageState or None, str or None)
        A tuple containing:

        - A boolean indicating whether authentication succeeded.
        - The authenticated `StorageState` if successful,
          otherwise `None`.
        - An error message if authentication fails,
          otherwise `None`.

    Raises
    ------
    Exception
        Propagates unexpected errors during browser
        initialization or login execution.
    """

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
        

async def validate_state(
        store: str,
        state: StorageState
    ) -> bool:
    """
    Validate whether a stored authentication state is 
    still valid.

    A new browser context is created using the provided
    storage state. The provider-specific login check
    is executed to determine whether the session is
    still authenticated.

    Parameters
    ----------
    store : str
        Identifier of the provider whose state is being 
        validated.

    state : StorageState
        Previously stored Playwright authentication state.

    Returns
    -------
    bool
        `True` if the session is still authenticated,
        otherwise `False`.

    Raises
    ------
    Exception
        Propagates unexpected errors during browser
        initialization or provider interaction.
    """

    manager: AsyncBrowserContextMaganer

    success: bool = False
    page: Page | None = None

    store_instance: BaseProvider = get_provider(
        provider_name = store
    )

    async with async_playwright() as apw:
        manager = AsyncBrowserContextMaganer(apw)

        _, _, page = await manager.create_browser_context(
            state,
            start_url = store_instance.url
        )

        success = await store_instance.is_logged_in(
            page
        )

    return success