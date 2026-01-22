
import re
import asyncio
from pathlib import Path
from typing import Callable, Awaitable

from playwright.async_api import (
    Playwright, 
    Browser, 
    BrowserContext, 
    Page, 
    ElementHandle,
    StorageState,
    Locator,
    TimeoutError as PlaywrightTimeoutError
)

from backend.config import settings
from backend.database.engine import SessionLocal
from backend.database.repositories import credential_repo
from backend.database.repositories import browser_context_repo
from backend.backend_utils.signals.login_required import LoginRequiredSignal
from backend.backend_utils.exceptions import (
    LoginFailedException,
    ManualFallbackException
)

from shared.provider.base_provider import BaseProvider


if settings.CLI_MODE:
    BACKEND_ROOT = Path(__file__).resolve().parents[4]

    LOG_IN_STATES_DIR = BACKEND_ROOT / ".logins"
    LOG_IN_STATES_DIR.mkdir(0o600, exist_ok=True)

SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 900


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
            session_id: str | None = None
        ):

        self.async_playwright = playwright
        self.session_id = session_id


    @staticmethod
    def is_cli_mode() -> bool:
        """"""

        return settings.CLI_MODE
    

    @staticmethod
    def is_headless_mode() -> bool:
        """"""

        return settings.HEADLESS


    @staticmethod
    def __state_path(provider: BaseProvider) -> Path:
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
    def __get_current_state(
            session_id: str | None,
            provider: str
        ) -> tuple[Path | StorageState | str | None, str | None]:
        """"""

        if AsyncBrowserContextMaganer.is_cli_mode():
            path: Path = AsyncBrowserContextMaganer.__state_path(provider)
            return path, None if path.exists() else None

        else:
            with SessionLocal() as db:
                ctx: StorageState | str | None
                rsn: str | None

                if session_id:
                    ctx, rsn = browser_context_repo.get_browser_context(
                        db,
                        session_id,
                        provider
                    )
                    return ctx, rsn

                else:
                    return None, None

    
    @staticmethod
    async def __save_current_state(
        session_id: str | None,
        provider: str,
        context: BrowserContext
    ) -> None:
        """"""

        state_dict: StorageState = await context.storage_state()

        if AsyncBrowserContextMaganer.is_cli_mode():
            pass        # fare caso per CLI

        else:
            with SessionLocal() as db:
                if session_id:
                    browser_context_repo.upsert_browser_context(
                        db,
                        session_id,
                        provider,
                        state_dict,
                        None
                    )


    @staticmethod
    async def __handle_failure(
            provider: BaseProvider, 
            reason: str | None = None
        ) -> None | LoginRequiredSignal:
        """"""

        if AsyncBrowserContextMaganer.is_cli_mode():
            raise ManualFallbackException(provider, reason)
        
        return LoginRequiredSignal(provider.name, provider.url, reason)
    

    @staticmethod
    async def __get_creds_by_mode(
            session_id: str | None,
            provider: str
        ) -> dict[str, str] | None:
        """"""

        credentials: dict[str, str] | None = None

        if not AsyncBrowserContextMaganer.is_cli_mode():
            with SessionLocal() as db:
                if session_id:
                    credentials = credential_repo.get_credentials(
                        db,
                        session_id,
                        provider
                    )

        else:
            pass    # fare caso per cli

        return credentials

    
    @staticmethod
    async def close_page_resources(page: Page) -> None:
        """
        Clean up Playwright resources associated with the given page.

        This function attempts to close the page, its browser context,
        and the underlying browser instance. Any errors encountered during 
        the cleanup process are silently ignored to ensure that resource 
        disposal does not interrupt the caller's execution flow.
        """

        try:
            context: BrowserContext = page.context
            browser: Browser | None = context.browser

            await page.close()
            await context.close()
            await browser.close() if browser else None

        except:
            pass


    @staticmethod
    async def detect_captcha(page: Page) -> bool | str:
        """
        Detect the presence of captchas in the given webpage.

        Args:
            page (Page):
                The webpage in which the detection is performed.

        Returns:
            bool | str
            - `True` if at least a captcha is detected.
            - `False` if no captcha was detected.
            - `str` with an error message if something went wrong.
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

        except Exception as e:
            return f"Unexpected error: {str(e)}"

        try:
            # some captchas may be hidden
            # into other html tags
            tag_texts: list[str] = [
                "div",
                "img",
                "li"
            ]

            results: list[ElementHandle] = (
                await AsyncBrowserContextMaganer.__find_elements_with_attr_pattern(
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


    @staticmethod  
    async def __find_elements_with_attr_pattern(
            webpage: Page,
            html_tags: list[str], 
            regex: re.Pattern[str],
            early_end: bool | None = False
        ) -> list[ElementHandle]:
        """
        Finds all attributes of the HTML tags given in the list that match
        the pattern specified by the regular expression. Finally, it returns
        a list containing all the tags that match the pattern.

        Args:
            webpage (Page):
                The webpage in which the html tag could be found.

            html_tags (list[str]):
                A list containing the html tags whose attributes could 
                satisfy the pattern.

            regex (Pattern[str]):
                The pattern used to filter the html tags.

            early_end (bool | None):
                A boolean value that specifies whether the execution
                must stop right after the first tag is inserted into
                the result list. Default is `False`.

                - `True` for the short execution.
                - `False` for all the tags to be inserted into the result list.

        Returns:
            list[ElementHandle]
        """

        async def check_tag(tag: str) -> list[ElementHandle]:
            """
            Check all the tags equal to the given tag and whose attribute(s) 
            satisfy the regular expression.

            Args:
                tag (str):
                    A HTML tag.

            Returns:
                list[ElementHandle]:
                    A list containing all the tags whose attribute(s)
                    satisfy the regex.
            """

            matches: list[ElementHandle] = []
            elements: list[ElementHandle] = await webpage.query_selector_all(tag)

            async def check_elem(element: ElementHandle) -> ElementHandle | None:
                """
                Check if the given element contains any attribute that
                satisfy the regular expression.

                Returns:
                    - `None` if the element's attribute(s) don't satisfy the regex.
                    - `ElementHandle` otherwise.
                """

                attributes: dict[str, str] = await element.evaluate(
                    "(node) => {"
                        "const obj = {};"
                        "for(const attr of node.attributes){"
                            "obj[attr.name] = attr.value;"
                        "}"
                        "return obj;"
                    "}"
                )

                for attr_value in attributes.values():
                    if re.search(regex, attr_value):
                        return element
        
                return None
        
            if not early_end:
                # long execution
                results: list[ElementHandle | None] = await asyncio.gather(
                    *(check_elem(e) for e in elements)
                )

                for r in results:
                   if r is not None:
                       matches.append(r)

                return matches
            else:
                # short execution
                tasks: list[asyncio.Task[ElementHandle | None]] = [
                    asyncio.create_task(check_elem(e))
                    for e in elements
                ]

                done: set[asyncio.Task[ElementHandle | None]]
                pending: set[asyncio.Task[ElementHandle | None]]

                while tasks:
                    done, pending = await asyncio.wait(
                        tasks, 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    for t in done:
                        try:
                            result: ElementHandle | None = t.result()
                        except:
                            result = None

                        if result:
                            matches.append(result)

                            for p in pending:
                                p.cancel()

                            await asyncio.gather(*pending, return_exceptions=True)

                            return matches
    
                    tasks = list(pending)

                return matches
        
        tag_results: list[list[ElementHandle]] = await asyncio.gather(
            *(check_tag(tag) for tag in html_tags)
        )
        final_tag_results: list[ElementHandle] = [
            elem for sublist in tag_results for elem in sublist
        ]

        return final_tag_results


    async def create_browser_context(
        self,
        state: Path | StorageState | str | None = None,
        start_url: str | None = None
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
            headless=AsyncBrowserContextMaganer.is_headless_mode()
        )

        storage_state_param = None

        if not state:
            if isinstance(state, Path):
                if state.exists():
                    storage_state_param = state

            else:
                storage_state_param = state

        context = await browser.new_context(
            storage_state=storage_state_param,
            viewport={
                "width": SCREEN_WIDTH,
                "height": SCREEN_HEIGHT
            }
        )

        page = await context.new_page()

        if start_url:
            await page.goto(start_url)

        return browser, context, page
    

    async def __prepare_provider_context(
            self,
            provider: BaseProvider,
            state: Path | StorageState | str | None
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
            state=state,
            start_url=provider.url
        )

        await AsyncBrowserContextMaganer.__close_popup(
            provider,
            page
        )

        return browser, context, page


    async def ensure_provider_context(
            self,
            session_id: str | None,
            provider: BaseProvider
        ) -> BrowserContext | LoginRequiredSignal:
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
            BrowserContext
        """

        state: Path | StorageState | str | None
        fail_reason: str | None

        state, fail_reason = AsyncBrowserContextMaganer.__get_current_state(
            session_id,
            provider
        )

        if state == "LOGIN_FAILED":
            raise LoginFailedException(provider, fail_reason)

        context: BrowserContext | None = None
        page: Page | None = None

        try:
            if not state and provider.login_required:
                failure = AsyncBrowserContextMaganer.__handle_failure(
                    provider, 
                    "MISSING_STATE"
                )
                
                if isinstance(failure, LoginRequiredSignal):
                    return failure

            _, context, page = await self.__prepare_provider_context(
                provider,
                state
            )

            logged_in = await AsyncBrowserContextMaganer.__is_logged_in(
                provider,
                page
            ) 
            
            if logged_in or not provider.login_required:
                await page.close()
                return context
            
            if await provider.has_auto_login():
                if await self.detect_captcha(page):
                    raise ManualFallbackException(
                        provider,
                        "CAPTCHA_DETECTED"
                    )
                    
                credentials = await AsyncBrowserContextMaganer.__get_creds_by_mode(
                    session_id,
                    provider
                )
                
                await provider.auto_login(page, credentials)
                await page.wait_for_load_state("networkidle")

                if await self.__is_logged_in(provider, page):
                    await self.__save_current_state(
                        session_id,
                        provider,
                        context
                    )
                    await AsyncBrowserContextMaganer.close_page_resources(
                        page
                    )

                    return context
                    
            raise ManualFallbackException(provider)             
        
        except (ManualFallbackException, Exception) as e:
            if page:
                await AsyncBrowserContextMaganer.close_page_resources(
                    page
                )

            if AsyncBrowserContextMaganer.is_cli_mode():
                try:
                    if isinstance(state, Path):
                        await self.__manual_login(provider, state)
                        _, context, _ = await self.__prepare_provider_context(
                            provider=provider,
                            state=state
                        )

                except:
                    raise LoginFailedException(provider)

                if context:
                    return context
            
            return LoginRequiredSignal(provider, str(e))


    async def __manual_login(
            self,
            provider: BaseProvider,
            state_path: Path
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

            state_path (Path):
                Path where the authenticated browser state should be saved.

        Returns:
            None
        
        Raises:
            LoginFailedException:
                Raised if the login cannot be completed or the context
                cannot be initialized correctly.
        """

        context: BrowserContext | None = None
        page: Page | None = None

        async with self._manual_login_lock:
            if isinstance(state_path, Path):
                _, context, page = await self.__prepare_provider_context(
                    provider=provider,
                    state=state_path
                )

            if await AsyncBrowserContextMaganer.__wait_until_logged_in(
                provider=provider,
                page=page,
                check_func=AsyncBrowserContextMaganer.__is_logged_in,
                timeout=30000
            ):
                await context.storage_state(path=state_path)
                await self.close_page_resources(page)
            else:
                await self.close_page_resources(page)
                raise LoginFailedException(provider)


    @staticmethod
    async def __is_logged_in(
        provider: BaseProvider,
        page: Page
        ) -> bool:
        """
        Check if the user is logged-in into the website in
        the given webpage.

        Args:
            provider (BaseProvider):
                A provider of professional items.

            page (Page):
                A page at the given provider's website.

        Returns:
            bool
            - `True` if the user is logged-in.
            - `False` otherwise.
        """

        # if not provider.login_required:
        #     return False

        try:
            logout_texts: re.Pattern[str] = re.compile(
                r"(?:log|sign)[- ]?out",
                re.IGNORECASE
            )

            results: list[ElementHandle] = (
                await AsyncBrowserContextMaganer.__find_elements_with_attr_pattern(
                    page,
                    provider.logout_selectors,
                    logout_texts,
                    early_end=True
                )
            )

            if results == []:
                return False
            
            else:
                return True
            
        except:
            pass

        return False
    

    @staticmethod
    async def __wait_until_logged_in(
        provider: BaseProvider,
        page: Page,
        check_func: Callable[[BaseProvider, Page], Awaitable[bool]],
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
        start = asyncio.get_event_loop().time()

        while True:
            if await check_func(provider, page):
                return True
            
            if (asyncio.get_event_loop().time() - start) * 1000 > timeout:
                return False
            
            # sleep accepts seconds as parameter
            await asyncio.sleep(interval / 1000)


    @staticmethod
    async def __close_popup(
        provider: BaseProvider,
        page: Page
        ) -> None:
        """
        Close all pop-ups related to cookies and advertising in a webpage. 
        By default all the cookies are rejected if possible, otherwise they are accepted.

        Args:
            provider (BaseProvider):
                A provider of professional items.

            page (Page):
                A page at the given provider's website.

        Returns:
            None
        """

        decline_texts: re.Pattern[str] = re.compile(
            (
                "rifiuta|rifiuto|declina|decline|refuse|deny|reject"
                "necessary|essential only|essenziali|chiudi|chiudere"
                "close|\u00d7|\u0078"
            ),
            re.IGNORECASE
        )

        accept_texts: re.Pattern[str] = re.compile(
            "accetta|accettare|accept",
            re.IGNORECASE
        )

        for sel in provider.popup_selectors:
            try:
                elements: Locator = page.locator(sel)
                count: int = await elements.count()
                accept_cookie: Locator | None = None

                for i in range(count):
                    elem: Locator = elements.nth(i)

                    if await elem.is_visible():
                        # we return the text content or an empty string, 
                        # cause the if-statemente could fail with a NoneType
                        text: str = await elem.text_content() or ""

                        if re.search(decline_texts, text):
                            await elem.click()

                        elif re.search(accept_texts, text):
                            accept_cookie = elem

                # we click on accept when there is no reject button
                if (accept_cookie is not None) and (await accept_cookie.is_visible()):
                    await accept_cookie.click()
                    
            except:
                continue

        # in order to get rid of those pop-ups that 
        # do not contain ASCII safe characters
        await page.keyboard.press("Escape")