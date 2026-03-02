
import asyncio
import re

from playwright.async_api import (
    Browser,
    BrowserContext,
    ElementHandle,
    Locator,
    Page,
)


async def find_elements_with_attr_pattern(
        webpage: Page,
        html_tags: list[str], 
        regex: re.Pattern[str],
        early_end: bool | None = False
    ) -> list[ElementHandle]:
    """
    Find all HTML elements whose attributes match a given 
    regex pattern.

    Parameters
    ----------
    webpage : Page
        The Playwright page object in which the HTML tags 
        are searched.

    html_tags : list[str]
        A list of HTML tag names to inspect.

    regex : re.Pattern[str]
        Regular expression pattern used to filter element 
        attributes.

    early_end : bool, optional
        If `True`, return immediately after finding the 
        first match. Default is `False` (collect all matching 
        elements).

    Returns
    -------
    list[ElementHandle]
        A list of ElementHandle objects corresponding to matched elements.
    """

    async def check_tag(
            tag: str
        ) -> list[ElementHandle]:
        """
        Check all elements of a given tag for attributes 
        matching the regex.

        Parameters
        ----------
        tag : str
            HTML tag name.

        Returns
        -------
        list[ElementHandle]
            List of elements whose attributes match the regex.
        """

        matches: list[ElementHandle] = []
        elements: list[ElementHandle] = (
            await webpage.query_selector_all(tag)
        )

        async def check_elem(
                element: ElementHandle
            ) -> ElementHandle | None:
            """
            Check if a single element contains any attribute 
            matching the regex.

            Parameters
            ----------
            element : ElementHandle
                The element to inspect.

            Returns
            -------
            ElementHandle | None
                The element if it matches, None otherwise.
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
            # -------------------- long execution --------------------
            results: list[ElementHandle | None] = await asyncio.gather(
                *(check_elem(e) for e in elements)
            )

            for r in results:
                if r is not None:
                    matches.append(r)

            return matches
        
        else:
            # -------------------- short execution -------------------
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

                        await asyncio.gather(
                            *pending, 
                            return_exceptions = True
                        )

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
       

async def close_page_resources(
        page: Page
    ) -> None:
    """
    Close Playwright resources associated with a page.

    This includes the page itself, its browser context, and
    the underlying browser. Errors during cleanup are ignored.

    Parameters
    ----------
    page : Page
        The Playwright page to close.
    """

    try:
        context: BrowserContext = page.context
        browser: Browser | None = context.browser

        await page.close()
        await context.close()
        await browser.close() if browser else None

    except:
        pass


async def close_popups(
        popup_selectors: list[str],
        page: Page
    ) -> None:
    """
    Close pop-ups for cookies or ads on a webpage.

    By default, attempts to reject cookies if possible; 
    otherwise accepts them. Any pop-ups that cannot be 
    processed are skipped silently.

    Parameters
    ----------
    popup_selectors : list[str]
        A list of CSS selectors identifying potential pop-ups.

    page : Page
        The Playwright page object to operate on.

    Returns
    -------
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

    for sel in popup_selectors:
        try:
            elements: Locator = page.locator(sel)
            count: int = await elements.count()
            accept_cookie: Locator | None = None

            for i in range(count):
                elem: Locator = elements.nth(i)

                if await elem.is_visible():
                    text: str = await elem.text_content() or ""

                    if re.search(decline_texts, text):
                        await elem.click()

                    elif re.search(accept_texts, text):
                        accept_cookie = elem

            if (
                (accept_cookie is not None) 
                and 
                (await accept_cookie.is_visible())
            ):
                await accept_cookie.click()
                
        except:
            continue

    await page.keyboard.press("Escape")