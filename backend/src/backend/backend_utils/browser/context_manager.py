
import asyncio
from pathlib import Path

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    StorageState,
)

from backend.backend_utils.exceptions import (
    LoginFailedException,
    ManualFallbackException
)
from backend.config import settings
from backend.database.engine import AsyncSessionLocal
from backend.database.repositories import (
    CredentialsRepository,
    LoginContextRepository,
)

from shared.playwright.page_utilities import close_page_resources
from shared.playwright.waiter import wait_until_logged_in
from shared.provider.base_provider import BaseProvider


if settings.CLI_MODE:
    BACKEND_ROOT = Path(__file__).resolve().parents[4]

    LOG_IN_STATES_DIR = BACKEND_ROOT / ".logins"
    LOG_IN_STATES_DIR.mkdir(0o700, exist_ok=True)


class AsyncBrowserContextMaganer:
    """
    Class to manage asynchronous login actions in websites
    
    Attributes:
        async_playwright (Playwright):
            An asynchronous playwright context manager.
    """


    # mutex semaphore for managing asyncronous manual logins
    _manual_login_lock = asyncio.Lock()


    def __init__(
            self,
            playwright: Playwright, 
            client_id: str | None = None
        ):

        self.async_playwright = playwright
        self.client_id = client_id


    @staticmethod
    def is_cli_mode() -> bool:
        """"""

        return settings.CLI_MODE
    

    @staticmethod
    def is_headless_mode() -> bool:
        """"""

        return settings.HEADLESS


    @staticmethod
    def __state_path(
            provider: BaseProvider
        ) -> Path:
        """
        Return the `Path` to the given provider's state file.

        Args:
            provider (Providers):
                A provider of professional items.

        Returns:
            Path
        """

        return LOG_IN_STATES_DIR / f"{provider.name.lower()}_state.json"
    

    @staticmethod
    async def __get_current_state(
            client_id: str | None,
            provider: BaseProvider
        ) -> Path | StorageState | None:
        """"""

        if AsyncBrowserContextMaganer.is_cli_mode():
            path: Path = AsyncBrowserContextMaganer.__state_path(provider)

            return path if path.exists() else None

        else:
            async with AsyncSessionLocal() as db:
                ctx: StorageState | None

                if client_id:
                    ctx = await LoginContextRepository.get_context(
                        db,
                        client_id,
                        provider.name
                    )
                    
                    return ctx

                else:
                    return None

    
    @staticmethod
    async def __save_current_state(
            client_id: str | None,
            provider: BaseProvider,
            context: BrowserContext
        ) -> None:
        """"""

        state: StorageState = await context.storage_state()

        if AsyncBrowserContextMaganer.is_cli_mode():
            # you are free to store/upsert the 
            # credentials where you want :)
            pass

        else:
            async with AsyncSessionLocal() as db:
                if client_id:
                    await LoginContextRepository.upsert_context(
                        db,
                        client_id,
                        provider.name,
                        state
                    )
    

    @staticmethod
    async def __get_creds_by_mode(
            client_id: str | None,
            provider: BaseProvider
        ) -> tuple[str | None, str | None]:
        """"""

        username: str | None = None
        password: str | None = None

        if not AsyncBrowserContextMaganer.is_cli_mode():
            async with AsyncSessionLocal() as db:
                if client_id:
                    username, password = await CredentialsRepository.get_credentials(
                        db,
                        client_id,
                        provider.name
                    )

        else:
            # you are free to store the credentials 
            # for a website where you want :)
            pass

        return (username, password)


    async def create_browser_context(
            self,
            state: Path | StorageState | None = None,
            start_url: str | None = None,
            headless: bool = True
        ) -> tuple[Browser, BrowserContext, Page]:
        """
        Create a new browser, context, and page.

        Args:
            headless (bool):
                Whether to launch the browser in headless mode.

            storage_state (Path | None):
                Path to existing storage state to load.

            start_url (str | None):
                URL to navigate to immediately after page creation.

        Returns:
            tuple[Browser, BrowserContext, Page]:
                The browser, its context, and the page.
        """

        browser: Browser
        context: BrowserContext
        page: Page

        browser = await self.async_playwright.chromium.launch(
            headless = (
                headless 
                if not headless else AsyncBrowserContextMaganer.is_headless_mode()
            )
        )

        storage_state_param: Path | StorageState | None = None

        if state:
            if isinstance(state, Path):
                if state.exists():
                    storage_state_param = state

            else:
                storage_state_param = state

        context = await browser.new_context(
            storage_state = storage_state_param
        )

        page = await context.new_page()

        if start_url:
            await page.goto(start_url)

        return browser, context, page
    

    async def __prepare_provider_context(
            self,
            provider: BaseProvider,
            state: Path | StorageState | None,
            headless: bool
        ) -> tuple[Browser, BrowserContext, Page]:
        """
        Create and initialize a new browser context for the given provider.

        This method launches a new Chromium browser instance, loads the
        provider's website, applies an existing authentication state if
        available, and saves the state for future sessions if it does not
        already exist. It also automatically closes any initial pop-ups
        that may appear after navigation.

        Args:
            provider (BaseProvider):
                The provider whose website should be opened.

            state_path (Path):
                Path to the file containing the stored browser state
                (cookies, local storage, etc.).

        Returns:
            tuple[Browser, BrowserContext, Page]:
                A tuple containing the created browser instance,
                the initialized browser context, and the opened page.
        """

        browser: Browser
        context: BrowserContext
        page: Page

        browser, context, page = await self.create_browser_context(
            state = state,
            start_url = provider.url,
            headless = headless
        )

        await provider.close_all_popups(page)

        return browser, context, page
    

    async def __ensure_autologin_context(
            self,
            client_id: str | None,
            provider: BaseProvider
        ) -> BrowserContext | None:
        """"""

        if (
            not provider.has_auto_login() 
            and 
            provider.login_required
        ):
            raise LoginFailedException(
                provider, 
                (
                    "The provider requires login, but the autologin "
                    "implementation is missing or not supported."
                )
            )
        
        state: Path | StorageState | None = None
        context: BrowserContext | None = None
        page: Page | None = None
        
        state = await AsyncBrowserContextMaganer.__get_current_state(
            client_id,
            provider
        )

        _, context, page = await self.__prepare_provider_context(
            provider = provider,
            state = state,
            headless = True
        )

        try:
            if (
                await provider.is_logged_in(page) 
                or 
                not provider.login_required
            ):
                await page.close()
                return context

            if await provider.has_captcha(page):
                raise LoginFailedException(
                    provider, 
                    (
                        "Authentication blocked by CAPTCHA: automated access "
                        "is restricted by the provider's security policies."
                    )
                )

            username, password = (
                await AsyncBrowserContextMaganer.__get_creds_by_mode(
                    client_id,
                    provider
                )
            )

            if not all((username, password)):
                raise LoginFailedException(
                    provider, 
                    (
                        "No valid credentials found for the selected store. "
                        "Please verify your settings and try again."
                    )
                )

            if not await provider.auto_login(page, username, password):
                raise LoginFailedException(
                    provider, 
                    (
                        "Autologin process failed. This may be due to incorrect "
                        "credentials or unexpected UI changes on the provider's website."
                    )
                )

            await self.__save_current_state(
                client_id,
                provider,
                context
            )

            await page.close()
            return context

        except Exception:
            if page:
                await close_page_resources(page)

            raise


    async def __ensure_standard_context(
            self,
            client_id: str | None,
            provider: BaseProvider
        ) -> BrowserContext | None:
        """"""

        state: Path | StorageState | None = (
            await AsyncBrowserContextMaganer.__get_current_state(
                client_id,
                provider
            )
        )

        context: BrowserContext | None = None
        page: Page | None = None

        try:
            if not state and provider.login_required:
                raise ManualFallbackException(provider)

            _, context, page = await self.__prepare_provider_context(
                provider,
                state,
                True
            )

            if (
                await provider.is_logged_in(page) 
                or 
                not provider.login_required
            ):
                await page.close()
                return context

            if provider.has_auto_login():
                if await provider.has_captcha(page):
                    raise ManualFallbackException(provider)

                username, password = await AsyncBrowserContextMaganer.__get_creds_by_mode(
                    client_id,
                    provider
                )

                if await provider.auto_login(page, username, password):
                    await self.__save_current_state(
                        client_id,
                        provider,
                        context
                    )
                    await page.close()
                    return context


            raise ManualFallbackException(provider)

        except ManualFallbackException:
            if page:
                await close_page_resources(page)

            try:
                if not state:
                    await self.__manual_login(provider)
                    _, context, _ = await self.__prepare_provider_context(
                        provider,
                        state,
                        True
                    )

            except:
                raise LoginFailedException(provider)
                
        return context


    async def ensure_provider_context(
            self,
            client_id: str | None,
            provider: BaseProvider
        ) -> BrowserContext | None:
        """
        Return an instanse of `BrowserContext` to be used to navigate the 
        given provider's website. It may require the user to manual logging-in
        into the website for various reasons:
         
        - There is not an existing state for the website.
        - The already existing state is expired.
        - The given provider does not have an auto login function.

        Args:
            provider (Providers):
                The provider for whom a login is required.

        Returns:
            BrowserContext | None
        """

        if not settings.CLI_MODE:
            return await self.__ensure_autologin_context(
                client_id,
                provider
            )
        
        return await self.__ensure_standard_context(
            None,
            provider
        ) 


    async def __manual_login(
            self,
            provider: BaseProvider
        ) -> None:
        """
        Open a non-headless browser so the user can manually perform
        the authentication on the provider's website. When the login is
        completed, the method ensures that a valid browser context is
        created and ready to be used for navigating the provider's site,
        storing its authenticated state in the given path.

        Args:
            provider (Provider):
                The provider whose website requires manual authentication.

        Returns:
            None
        
        Raises:
            LoginFailedException:
                Raised if the login cannot be completed or the context
                cannot be initialized correctly.
        """

        state_path: Path = AsyncBrowserContextMaganer.__state_path(provider)

        context: BrowserContext | None = None
        page: Page | None = None

        async with self._manual_login_lock:
            _, context, page = await self.__prepare_provider_context(
                provider=provider,
                state=state_path,
                headless=False
            )

            if await wait_until_logged_in(
                page=page,
                check_func=provider.is_logged_in,
                timeout=30000
            ):
                await context.storage_state(path=state_path)
                await close_page_resources(page)

            else:
                await close_page_resources(page)
                raise LoginFailedException(provider)