
import re
import asyncio
import platform
from exceptions import LoginFailedException
from utils import BaseProvider
from typing import Optional, Callable
from re import Pattern
from pathlib import Path
from playwright.async_api import (
    Playwright, 
    Browser, 
    BrowserContext, 
    Page, 
    ElementHandle,
    TimeoutError as PlaywrightTimeoutError
)


LOG_IN_STATES_DIR = Path("./logins")
LOG_IN_STATES_DIR.mkdir(exist_ok=True)


class AsyncLoginManager:
    """
    Class to manage asynchronous log-in actions in websites
    
    Attributes:
        apw (Playwright):
            An asynchronous playwright context manager.
    """


    # mutex semaphore for managing asyncronous manual log-ins
    _manual_login_lock = asyncio.Lock()


    def __init__(self, playwright: Playwright):
        self.apw = playwright
    

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


    async def __launch_browser(self, headless: bool) -> Browser:
        """
        Return a `Browser` istance according to the working OS:

        * macOS: Safari
        * Linux: Firefox
        * Windows: Google Chrome

        Args:
            headless (bool):
                Boolean value that specifies whether the 
                interaction with the browser is headless or not.

        Returns:
            Browser
        """

        match platform.system().lower():
            case "darwin":
                return await self.apw.webkit.launch(headless=headless)
            case "linux":
                return await self.apw.firefox.launch(headless=headless)
            case "windows":
                return await self.apw.chromium.launch(headless=headless)


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

        captcha_text = re.compile(
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
                    url = frame.url or ""
                    if re.search(captcha_text, url):
                        return True
        except PlaywrightTimeoutError:
            pass
        except Exception as e:
            return f"Unexpected error: {e}"

        try:
            # some captchas may be hidden into
            # other html tags
            tag_texts = [
                "div",
                "img",
                "li"
            ]

            results = await AsyncLoginManager.__find_elements_with_attr_pattern(
                page,
                tag_texts,
                captcha_text,
                early_end=True
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
            regex: Pattern[str],
            early_end: Optional[bool] = False
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

            early_end (Optional[bool]):
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

            matches = []
            elements = await webpage.query_selector_all(tag)

            async def check_elem(element: ElementHandle) -> Optional[ElementHandle]:
                """
                Check if the given element contains any attribute that
                satisfy the regular expression.

                Returns:
                    - `None` if the element's attribute(s) don't satisfy the regex.
                    - `ElementHandle` otherwise.
                """

                attributes = await element.evaluate(
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
                results = await asyncio.gather(
                    *(check_elem(e) for e in elements)
                )

                for r in results:
                   if r is not None:
                       matches.append(r)

                return matches
            else:
                # short execution
                tasks = [
                    asyncio.create_task(check_elem(e))
                    for e in elements
                ]

                while tasks:
                    done, pending = await asyncio.wait(
                        tasks, 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    for t in done:
                        result = t.result()
                        if result:
                            matches.append(result)

                            for p in pending:
                                p.cancel()

                            return matches
    
                    tasks = list(pending)

                return matches
        
        tag_results = await asyncio.gather(*(check_tag(tag) for tag in html_tags))
        tag_results = [elem for sublist in tag_results for elem in sublist]

        return tag_results

        
    async def ensure_context(
            self,
            provider: BaseProvider
        ) -> BrowserContext:
        """
        Return an instanse of `BrowserContext` to be used to navigate the 
        given provider's website. It may require the user to manual logging-in
        into the website for various reasons:
         
        - There is not an existing state for the website.
        - The already existing state is expired.
        - The given provider does not have an auto login function.

        Args:
            provider (Providers):
                The provider for whom a log-in is required.

        Returns:
            BrowserContext
        """

        state_path = AsyncLoginManager.__state_path(provider)

        state_path_exists = state_path.exists()
        login_required = provider.login_required

        # manual log-in if state path is absent and log-in is required
        if not state_path_exists and login_required:
            return await self.__manual_login(provider, state_path)
        
        # otherwise...
        browser = await self.__launch_browser(headless=True)
        context = await browser.new_context(
            storage_state=state_path if state_path_exists else None
        )
        page = await context.new_page()

        await page.goto(provider.url)
        await AsyncLoginManager.__close_popup(provider, page)

        if not state_path_exists:
            await context.storage_state(path=state_path)

        logged_in = await AsyncLoginManager.__is_logged_in(provider, page)
        
        if logged_in or not login_required:
            await page.close()
            return context
        
        # the `auto_login` is used when the context is present, but expired
        if await provider.has_auto_login():
            if await self.detect_captcha(page):
                await page.close()
                await context.close()
                await browser.close()
                return await self.__manual_login(provider, state_path)
            
            try:
                await provider.auto_login(page)
                await page.wait_for_load_state("networkidle")

                if await self.__is_logged_in(provider, page):
                    # ensure the new context
                    await context.storage_state(path=state_path)
                    return context
            except:
                pass

        # manual fallback
        await page.close()
        await context.close()
        await browser.close()
        return await self.__manual_login(provider, state_path)
        

    async def __manual_login(
            self,
            provider: BaseProvider,
            state_path: Path
        ) -> BrowserContext | str:
        """
        Launch a non-headless browser to manually logging-in
        into the provider's website and returns a `BrowserContext`
        istance.

        Args:
            provider (Provider):
                The provider whose website require a log-in.

            state_path (Path):
                The path to the directory containig the given
                provider's website state file.

        Returns:
            BrowserContext:
                If nothing went wrong during the log-in.
        
        Raises:
            LoginFailedException:
                If the log-in fails for any reason.
        """

        async with self._manual_login_lock:
            browser = await self.__launch_browser(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(provider.url)
            await AsyncLoginManager.__close_popup(provider, page)

            if await AsyncLoginManager.__wait_until_logged_in(
                provider=provider,
                page=page,
                check_func=AsyncLoginManager.__is_logged_in,
                timeout=30000
            ):
                await context.storage_state(path=state_path)
                await page.close()

                return context
            else:
                await page.close()
                await context.close()
                await browser.close()

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
            logout_texts = re.compile(
                r"(?:log|sign)[-\s]?out",
                re.IGNORECASE
            )

            results = await AsyncLoginManager.__find_elements_with_attr_pattern(
                page,
                provider.logout_selectors,
                logout_texts,
                early_end=True
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
        check_func: Callable[[BaseProvider, Page], bool],
        timeout: Optional[float] = 15000,
        interval: Optional[float] = 500
        ) -> bool:
        """
        Wait until the user is logged-in into the given
        provider's website.

        Args:
            provider (BaseProvider):
                A provider for whom a log-in is required.

            page (Page):
                A page at the given provider's website.

            check_func (Callable[[BaseProvider, Page], bool]):
                A function used to check if the user is logged-in
                into the website.

            timeout (Optional[float]):
                The time given (in milliseconds) to the user to 
                fulfill the log-in. Default is 15000 ms.

            interval (Optional[float]):
                The time (in milliseconds) between one check
                and another. Default is 500 ms.

        Returns:
            bool:
            - `True` if the log-in has been successfully fulfilled 
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

        decline_texts = re.compile(
            (
                "rifiuta|rifiuto|declina|decline|refuse|deny|reject"
                "necessary|essential only|essenziali|chiudi|chiudere"
                "close|\u00d7|\u0078"
            ),
            re.IGNORECASE
        )

        accept_texts = re.compile(
            "accetta|accettare|accept",
            re.IGNORECASE
        )

        for sel in provider.popup_selectors:
            try:
                elements = page.locator(sel)
                count = await elements.count()
                accept_cookie = None
                for i in range(count):
                    elem = elements.nth(i)
                    if await elem.is_visible():
                        # we return the text content or an empty string, 
                        # cause the if-statemente could fail with a NoneType
                        text = await elem.text_content() or ""
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