
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
    LOG_IN_STATES_DIR.mkdir(0o700, exist_ok = True)


class AsyncBrowserContextMaganer:
    """
    Manage authenticated Playwright browser contexts for providers.

    The class handles authentication workflows across different
    execution modes (CLI and non-CLI), supporting:

    - Persistent storage state reuse
    - Automatic login using stored credentials
    - Manual login fallback when required
    - Safe concurrent manual login handling

    Parameters
    ----------
    playwright : Playwright
        Initialized asynchronous Playwright instance.

    client_id : str or None, optional
        Identifier used to retrieve and persist user-specific
        authentication state and credentials.
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
        """
        Return whether the application is running in CLI mode.

        Returns
        -------
        bool
            `True` if CLI mode is enabled in the configuration,
            otherwise `False`.
        """

        return settings.CLI_MODE
    

    @staticmethod
    def is_headless_mode() -> bool:
        """
        Return whether headless browser execution is enabled.

        Returns
        -------
        bool
            `True` if headless mode is enabled in the configuration,
            otherwise `False`.
        """

        return settings.HEADLESS


    @staticmethod
    def __state_path(
            provider: BaseProvider
        ) -> Path:
        """
        Build the filesystem path for a provider's stored login state.

        Parameters
        ----------
        provider : BaseProvider
            Provider whose authentication state file is requested.

        Returns
        -------
        pathlib.Path
            Path pointing to the provider-specific JSON storage file.
        """

        return LOG_IN_STATES_DIR / f"{provider.name.lower()}_state.json"
    

    @staticmethod
    async def __get_current_state(
            client_id: str | None,
            provider: BaseProvider
        ) -> Path | StorageState | None:
        """
        Retrieve the persisted authentication state for a provider.

        Depending on the execution mode:

        - In CLI mode, the state is loaded from a local file path.
        - In non-CLI mode, the state is retrieved from the database.

        Parameters
        ----------
        client_id : str or None
            Identifier used to fetch user-specific stored state
            when running in non-CLI mode.

        provider : BaseProvider
            Provider whose authentication state is requested.

        Returns
        -------
        Path or StorageState or None
            A filesystem path to a stored state (CLI mode),
            a Playwright `StorageState` object (database mode),
            or `None` if no state is available.
        """

        if AsyncBrowserContextMaganer.is_cli_mode():
            path: Path = AsyncBrowserContextMaganer.__state_path(provider)

            return path if path.exists() else None

        else:
            async with AsyncSessionLocal() as db:
                ctx: StorageState | None

                if client_id:
                    ctx = await LoginContextRepository.get_storage_state(
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
        """"
        Persist the current browser context authentication state.

        Depending on the execution mode:

        - In CLI mode, state persistence can be implemented
        using filesystem storage.
        - In non-CLI mode, the state is stored in the database
        and committed.

        Parameters
        ----------
        client_id : str or None
            Identifier used to associate the state with a user
            in non-CLI mode.

        provider : BaseProvider
            Provider for which the state is being saved.

        context : BrowserContext
            Playwright browser context whose storage state
            should be persisted.

        Returns
        -------
        None
        """

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
                    await db.commit()
    

    @staticmethod
    async def __get_creds_by_mode(
            client_id: str | None,
            provider: BaseProvider
        ) -> tuple[str | None, str | None]:
        """
        Retrieve stored credentials for a provider.

        Depending on the execution mode:

        - In non-CLI mode, credentials are fetched from the database.
        - In CLI mode, credential retrieval must be implemented
        externally.

        Parameters
        ----------
        client_id : str or None
            Identifier used to retrieve user-specific credentials.

        provider : BaseProvider
            Provider whose credentials are requested.

        Returns
        -------
        tuple of (str or None, str or None)
            A tuple containing `(username, password)`.
            Returns `(None, None)` if no credentials are found.
        """

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
        Create a new browser instance, context, and page.

        If a valid storage state is provided, it is applied
        to the new browser context.

        Parameters
        ----------
        state : Path or StorageState or None, optional
            Existing authentication state to load into the
            browser context. If a `Path` is provided, it must
            exist to be used.

        start_url : str or None, optional
            URL to navigate to immediately after page creation.

        headless : bool, optional
            Whether to launch the browser in headless mode.
            The effective value may depend on configuration.

        Returns
        -------
        tuple of (Browser, BrowserContext, Page)
            The launched browser instance, its context,
            and the newly created page.
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
        Initialize a browser context for a specific provider.

        The method launches a browser, applies any available
        authentication state, navigates to the provider's URL,
        and closes initial pop-ups if present.

        Parameters
        ----------
        provider : BaseProvider
            Provider whose website should be opened.

        state : Path or StorageState or None
            Existing authentication state to load into the
            browser context.

        headless : bool
            Whether to launch the browser in headless mode.

        Returns
        -------
        tuple of (Browser, BrowserContext, Page)
            The browser instance, initialized context,
            and active page.
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
            client_id: str,
            provider: BaseProvider
        ) -> BrowserContext | None:
        """
        Ensure a valid authenticated browser context using automatic 
        login.

        The method attempts to:

        1. Load an existing stored authentication state.
        2. Verify whether the user is already logged in.
        3. Perform automatic login using stored credentials if necessary.
        4. Persist the updated authentication state.

        If login is required but unsupported or blocked (e.g., CAPTCHA),
        a `LoginFailedException` is raised.

        Parameters
        ----------
        client_id : str
            Identifier used to retrieve stored credentials
            and authentication state.

        provider : BaseProvider
            Provider requiring authentication.

        Returns
        -------
        BrowserContext or None
            An authenticated browser context ready for use.

        Raises
        ------
        LoginFailedException
            If automatic authentication fails or is not supported.
        """

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
                        "Authentication blocked by CAPTCHA: automated "
                        "access is restricted by the provider's security "
                        "policies."
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
                        "No valid credentials found for the selected "
                        "store. Please verify your settings and try again."
                    )
                )

            if not await provider.auto_login(page, username, password):
                raise LoginFailedException(
                    provider, 
                    (
                        "Autologin process failed. This may be due "
                        "to incorrect credentials or unexpected UI "
                        "changes on the provider's website."
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

                username, password = (
                    await AsyncBrowserContextMaganer.__get_creds_by_mode(
                        client_id,
                        provider
                    )
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
        Ensure and return an authenticated browser context
        for the specified provider.

        The authentication strategy depends on the execution mode:

        - In non-CLI mode, automatic login is attempted.
        - In CLI mode, standard initialization with manual
        fallback is used.

        Manual login may be required when no valid stored state
        exists, the state has expired, or automatic login
        is unsupported.

        Parameters
        ----------
        client_id : str or None
            Identifier used to retrieve stored credentials
            and authentication state.

        provider : BaseProvider
            Provider whose website requires an authenticated context.

        Returns
        -------
        BrowserContext or None
            Authenticated browser context ready for navigation.

        Raises
        ------
        LoginFailedException
            If authentication cannot be completed successfully.
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
        Perform manual authentication for a provider.

        A non-headless browser is opened to allow the user
        to authenticate interactively. Upon successful login,
        the authenticated storage state is persisted.

        A mutex lock ensures that only one manual login
        process can run concurrently.

        Parameters
        ----------
        provider : BaseProvider
            Provider requiring manual authentication.

        Returns
        -------
        None

        Raises
        ------
        LoginFailedException
            If authentication is not completed successfully
            within the allowed timeout.
        """

        state_path: Path = (
            AsyncBrowserContextMaganer.__state_path(provider)
        )

        context: BrowserContext | None = None
        page: Page | None = None

        async with self._manual_login_lock:
            _, context, page = await self.__prepare_provider_context(
                provider = provider,
                state = state_path,
                headless = False
            )

            if await wait_until_logged_in(
                page = page,
                check_func = provider.is_logged_in,
                timeout = 30000
            ):
                await context.storage_state(path = state_path)
                await close_page_resources(page)

            else:
                await close_page_resources(page)
                raise LoginFailedException(provider)