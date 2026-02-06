
import re
import asyncio
from typing import Coroutine, Any

import bs4
from google import genai
from google.genai import types
from google.genai.types import Content, Part
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError
)

from backend.backend_utils.common import SafeAsyncList
from backend.backend_utils.exceptions import LoginFailedException
from backend.backend_utils.browser import AsyncBrowserContextMaganer
from backend.agent.prompts import USER_PROMPT, COMPUTER_USE_SYSTEM_PROMPT
from backend.backend_utils.computer_use import (
    ComputerUseSession,
    run_computer_use_loop,
    generate_content_config
)

from shared.provider.base_provider import BaseProvider
from shared.provider.registry import get_provider
from shared.exceptions import ProviderNotSupportedException
from shared.playwright.page_utilities import close_page_resources


async def search_products(
        session_id: str | None, 
        products: list[str],
        providers: list[str]
    ) -> str:
    """
    Perform web search for each product in the given list.

    Args:
        products (list[str]):
            A list of product names or keywords to search for.

        providers (list[str]):
            A list of specific provider names where the search 
            should be restricted.

    Returns:
        str:
            A formatted string containing the information found 
            for each product.
    """
    
    web_search_results_list: SafeAsyncList
    browser_context_manager: AsyncBrowserContextMaganer

    async with async_playwright() as apw:
        web_search_results_list = SafeAsyncList()
        browser_context_manager = AsyncBrowserContextMaganer(apw, session_id)

        tasks: list[Coroutine[Any, Any, Any]] = []
        pages_to_close: list[Page] = []

        for provider in providers:
            try:
                provider_instance: BaseProvider = get_provider(provider)

                context: BrowserContext | None = (
                    await browser_context_manager.ensure_provider_context(
                        session_id,
                        provider_instance
                    )
                )
                
                if context:
                    page: Page = await context.new_page()
                    pages_to_close.append(page)

                    tasks.append(
                        __search_in_website(
                            provider_instance,
                            page,
                            products,
                            web_search_results_list
                        )
                    )

            except ProviderNotSupportedException:
                _, _, page = await browser_context_manager.create_browser_context(
                    start_url="https://google.com"
                )
                pages_to_close.append(page)

                tasks.append(
                    __search_with_computer_use(
                        provider,
                        page,
                        products,
                        web_search_results_list
                    )
                )

            except LoginFailedException as lfe:
                await web_search_results_list.add(
                    await __format_block(provider, [str(lfe)])
                )

        await asyncio.gather(*tasks)

        # clean up
        for page in pages_to_close:
            await close_page_resources(page)

    web_search_results_str = "\n\n".join(
        [result for result in await web_search_results_list.get_all()]
    )

    return web_search_results_str

  
async def __search_in_website(
        provider: BaseProvider,
        page: Page,
        products: list[str],
        result_list: SafeAsyncList
    ) -> None | str:
    """
    Perform web actions on the given provider's website to gather informations 
    about the given products. These informations are then inserted into the given
    `result_list`.

    Args:
        provider (BaseProvider):
            A provider for the products.

        page (Page):
            A webpage used to search for the products.

        products (list[str]):
            A list containig all the products to be searched on the website.
            
        result_list (SafeAsyncList):
            A list that will contain the scraping's results as strings.

    Returns:
        None | str
        - `None` if no problem was encountered during the execution.
    """

    try:
        await page.goto(provider.url)
        await page.wait_for_load_state("load")

        # insert here the aria-labels of the 
        # textboxes used to search a product
        search_texts = re.compile(
            r"cerca (per attributo|un prodotto)|ricerca|search",
            re.IGNORECASE
        )
        
        for item in products:

            item: str = item.strip()

            if not item:
                continue

            try:
                await page.get_by_role("textbox", name=search_texts).fill(item)
                await page.keyboard.press("Enter")

                found: str | None = await __wait_for_any_selector(
                    page, 
                    provider.result_container
                )

                if not found:
                    formatted_block = await __format_block(
                        provider.name,
                        [f"No result found for '{item}'."] 
                    )
                    await result_list.add(formatted_block)

                    # let's check the next item...
                    continue
            
                await __wait_for_any_selector(page, provider.title_classes)
                await __wait_for_all_selectors(page, provider.availability_classes)
                await __wait_for_any_selector(page, provider.price_classes)

                html = await page.content()
                soup = bs4.BeautifulSoup(html, "html.parser")

                product_container = soup.select_one(found)
                
                if not product_container:
                    continue
                
                product_name, product_availability, product_price = (
                    await asyncio.gather(
                        __select_text(
                            product_container, 
                            provider.title_classes
                        ),
                        __select_all_text(
                            product_container,
                            provider.availability_classes
                        ),
                            __select_text(
                            product_container,
                            provider.price_classes
                        )
                    )
                )

                await result_list.add(
                    await __format_block(
                        provider.name,
                        [
                            product_name,
                            product_availability,
                            product_price
                        ]            
                    )
                )

            except Exception as e:
                await result_list.add(
                    await __format_block(
                        provider.name,
                        [f"Error searching '{item}': {e}"] 
                    )
                )

    except Exception as e:
        await result_list.add(
            await __format_block(
                provider.name,
                [f"Fatal error: {str(e)}"]
            )
        )


async def __search_with_computer_use(
        provider: str,
        page: Page,
        products: list[str],
        result_list: SafeAsyncList
    ) -> None:
    """"""

    response_text: str | None = None

    try:
        client = genai.Client()

        config: genai.types.GenerateContentConfig = (
            await generate_content_config(COMPUTER_USE_SYSTEM_PROMPT)
        )

        initial_screenshot: bytes = await page.screenshot(type="png")

        formatted_products: str = "\n".join(f"- {p}" for p in products)

        prompt_filled: str = USER_PROMPT.format(
            products=formatted_products,
            store=provider
        )

        session: ComputerUseSession = ComputerUseSession(
            prompt_filled,
            initial_screenshot
        )

        response_text = await run_computer_use_loop(
            client,
            page,
            session,
            config
        )

    except Exception as e:
        await result_list.add(
            await __format_block(
                provider,
                [f"Error: {str(e)}"]
            )
        )

    finally:
        if response_text:
            await result_list.add(
                await __format_block(
                    provider,
                    [response_text]
                )
            )



async def __normalize_selectors(
        selectors: list[str] | dict
    ) -> list[str]:
    """
    Normalize the input selectors into a single list.

    If `selectors` is an `AvailabilityDict`, all values are flattened
    into one list. If it is already a list, it is returned unchanged.

    Examples:
        {"a": [1, 2], "b": [3]} -> [1, 2, 3]
        [1, 2, 3] -> [1, 2, 3]
    """

    if isinstance(selectors, dict):
        return [item for lst in selectors.values() for item in lst]

    return selectors


async def __wait_for_any_selector(
        page: Page,
        selectors: list[str] | dict,
        timeout: float = 2000
    ) -> str | None:
    """
    Wait for the first selector to appear on the page.

    Args:
        page (Page):
            The Playwright page to search on.

        selectors (list[str] | AvailabilityDict):
            CSS selectors or an AvailabilityDict of selectors.

        timeout (float, optional):
            Maximum time to wait for each selector in milliseconds.
            Default is 2000 ms.

    Returns:
        str | None:
            The first selector that becomes visible, or None if
            none are found within the timeout.
    """

    selectors = await __normalize_selectors(selectors)

    for sel in selectors:
        try:
            await page.wait_for_selector(
                selector=sel,
                state="visible",
                timeout=timeout
            )
            return sel
        except PlaywrightTimeoutError:
            continue

    # no selector has been found
    return None


async def __wait_for_all_selectors(
        page: Page,
        selectors: list[str] | dict,
        timeout: float = 2000
    ) -> bool:
    """
    Wait for all specified selectors to appear on the page.

    Args:
        page (Page):
            The Playwright page to search on.

        selectors (list[str] | AvailabilityDict):
            CSS selectors or an AvailabilityDict of selectors.

        timeout (float, optional):
            Maximum time to wait for each selector in milliseconds.
            Default is 2000 ms.

    Returns:
        bool:
            True if all selectors became visible within the timeout,
            False otherwise.
    """

    selectors = await __normalize_selectors(selectors)

    try:
        await asyncio.gather(
            *(page.wait_for_selector(
                selector=sel,
                state="visible",
                timeout=timeout) for sel in selectors
            )
        )
        return True
    
    except PlaywrightTimeoutError:
        return False


async def __select_text(
        tag: bs4.element.Tag,
        selectors: list[str] | dict
    ) -> str:
    """
    Extract text content from the first element matching any of the
    provided selectors.

    Args:
        tag (bs4.element.Tag):
            The BeautifulSoup tag to search within.

        selectors (list[str] | AvailabilityDict):
            A list of CSS selectors or an AvailabilityDict containing
            'available' and 'not_available' lists.

    Returns:
        str:
            The text of the first matching element, stripped of whitespace,
            or "N/A" if no element matches.
    """

    norm_selectors: list[str] = await __normalize_selectors(selectors)
    
    for sel in norm_selectors:
        elem: bs4.Tag | None = tag.select_one(sel)

        if elem:
            return elem.get_text(strip=True)
        
    return "N/A"


async def __select_all_text(
        tag: bs4.element.Tag,
        selectors: list[str] | dict
    ) -> str:
    """
    Extract and concatenate text content from all elements matching
    the given selectors.

    If `selectors` is an `AvailabilityDict`, both "available" and 
    "not_available" selectors are processed. When an element matches
    an "available" selector but has no text, the fallback "Disponibile"
    is used as text.

    Args:
        tag (Tag): 
            A BeautifulSoup tag to search within.

        selectors (list[str] | AvailabilityDict): 
            A list of CSS selectors or an AvailabilityDict
            containing 'available' and 'not_available' lists.

    Returns:
        str:
            A string containing the concatenated text of all matched
            elements, separated by newlines.
    """

    # in some websites the availability of a product
    # is espressed only as a button that let the user buy
    # that product.
    availability_alt_texts: re.Pattern[str] = re.compile(
        r"aggiungi al carrello|add to cart", 
        re.IGNORECASE
    )

    texts: list[str] = []

    if isinstance(selectors, dict):
        state: str
        sel_list: list[str]

        for state, sel_list in selectors.items():
            for sel in sel_list:
                for elem in tag.select(sel):
                    text: str = elem.get_text(strip=True)

                    if re.search(availability_alt_texts, text) and state == "available":
                        text = "Disponibile"

                    if text:
                        texts.append(text)

    else:
        for sel in selectors:
            for elem in tag.select(sel):
                text = elem.get_text(strip=True)

                if text:
                    texts.append(text)

    return ", ".join(texts)


async def __format_block(
        provider_name: str,
        lines: list[str]
    ) -> str:
    """
    Format a block of text with the provider name followed by
    a list of content lines.

    Args:
        provider (BaseProvide):
            The provider whose name will appear at the start of 
            the block.

        lines (list[str]):
            A list of strings to include after the provider name.

    Returns:
        str:
            A single string with the provider name in uppercase,
            followed by the lines joined with " | ".
    """

    return " | ".join(
        [
            f"{provider_name.upper()}",
            *lines
        ]
    )