
import re
import asyncio
from typing import Coroutine, Any

from google import genai
from langchain_core.runnables import RunnableConfig
from bs4 import (
    BeautifulSoup,
    ResultSet,
    Tag
)
from playwright.async_api import (
    async_playwright,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError
)

from backend.backend_utils.common import SafeAsyncList
from backend.backend_utils.exceptions import LoginFailedException
from backend.backend_utils.browser import (
    AsyncBrowserContextMaganer, 
    init_chrome_page
)
from backend.agent.prompts import (
    USER_PROMPT, 
    COMPUTER_USE_SYSTEM_PROMPT
)
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
        config: RunnableConfig,
        products: list[str],
        providers: list[str],
        limit_per_product: int = 1
    ) -> str:
    """
    Searches for multiple products across specified providers.

    This function iterates through the list of products and retrieves details
    from each provider, respecting a maximum number of results for each 
    individual product search.

    Args:
        config (RunnableConfig): 
            Configuration for the LangChain runnable, containing callbacks, 
            tags, and other execution metadata.

        products (list[str]): 
            A list of product names, models, or keywords to investigate.

        providers (list[str]): 
            A list of platforms, websites, or data sources to include in 
            the search.

        limit_per_product (int): 
            The maximum number of search results to retrieve for each item 
            in the products list.

    Returns:
        str: 
            A concatenated and formatted string containing the aggregated 
            search results, structured for easy parsing or LLM consumption.
    """
    
    session_id: str | None
    web_search_results_list: SafeAsyncList
    browser_context_manager: AsyncBrowserContextMaganer

    async with async_playwright() as apw:
        session_id = config.get("configurable", {}).get("client_id", None)
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
                            web_search_results_list,
                            limit_per_product
                        )
                    )

            except ProviderNotSupportedException:
                page = await init_chrome_page(apw, provider)
                pages_to_close.append(page)

                tasks.append(
                    __search_with_computer_use(
                        provider,
                        page,
                        products,
                        web_search_results_list,
                        limit_per_product
                    )
                )

            except LoginFailedException as lfe:
                print(str(lfe))
                await web_search_results_list.add(
                    await __format_block(provider, str(lfe))
                )

            except Exception as e:
                await web_search_results_list.add(
                    await __format_block(provider, str(e))
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
        result_list: SafeAsyncList,
        limit_per_product: int = 1
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
        
        for item in products:

            item: str = item.strip()

            if not item:
                continue

            try:
                await page.get_by_role(
                    "textbox", 
                    name=provider.search_texts
                ).fill(
                    item
                )
                await page.keyboard.press("Enter")

                found: str | None = await __wait_for_any_selector(
                    page, 
                    provider.result_container
                )

                if not found:
                    formatted_block = await __format_block(
                        provider.name,
                        f"No result found for '{item}'."
                    )
                    await result_list.add(formatted_block)

                    # let's check the next item...
                    continue
            
                _ = await __wait_for_any_selector(
                    page, 
                    provider.title_classes
                )
                _ = await __wait_for_all_selectors(
                    page, 
                    provider.availability_classes
                )
                _ = await __wait_for_any_selector(
                    page, 
                    provider.price_classes
                )

                html: str = await page.content()
                soup: BeautifulSoup = BeautifulSoup(html, "html.parser")

                product_containers: ResultSet[Tag] = soup.select(
                    found, 
                    limit = limit_per_product
                )
                
                if not product_containers:
                    continue

                titles: list[str]
                availabilities: list[str]
                prices: list[str]
                links: list[str]
                
                titles, availabilities, prices, links = (
                    await asyncio.gather(
                        __select_text(
                            product_containers, 
                            provider.title_classes
                        ),
                        __select_all_text(
                            product_containers,
                            provider.availability_classes,
                            provider.availability_texts
                        ),
                        __select_text(
                            product_containers,
                            provider.price_classes
                        ),
                        __extract_attribute_from_selectors(
                            product_containers,
                            provider.product_link_selectors,
                           ["href"] 
                        )
                    )
                )

                products_data: list[dict[str, str]] = []

                for name, avail, price, link in zip(
                    titles, 
                    availabilities, 
                    prices,
                    links
                ):
                    products_data.append({
                        "name": name,
                        "availability": avail,
                        "price": price,
                        "link": link
                    })

                await result_list.add(
                    await __format_block(
                        provider.name,
                        products_data            
                    )
                )

            except Exception as e:
                await result_list.add(
                    await __format_block(
                        provider.name,
                        f"Error searching '{item}': {e}"
                    )
                )

    except Exception as e:
        await result_list.add(
            await __format_block(
                provider.name,
                f"Fatal error: {str(e)}"
            )
        )


async def __search_with_computer_use(
        provider_url: str,
        page: Page,
        products: list[str],
        result_list: SafeAsyncList,
        limit_per_product: int = 1
    ) -> None:
    """"""

    response_text: str | None = None
    excluded_functions: list[str] = [
        "drag_and_drop", 
        "open_web_browser",
        "navigate"
    ]

    try:
        client: genai.Client = genai.Client()

        config: genai.types.GenerateContentConfig = (
            await generate_content_config(
                COMPUTER_USE_SYSTEM_PROMPT,
                excluded_functions
            )
        )

        initial_screenshot: bytes = await page.screenshot(
            type="png"
        )

        formatted_products: str = "\n".join(
            f"- {p}" for p in products
        )

        prompt_filled: str = USER_PROMPT.format(
            products = formatted_products,
            store = provider_url,
            items_per_product = limit_per_product
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
                provider_url,
                f"Error: {str(e)}"
            )
        )

    finally:
        if response_text:
            await result_list.add(
                await __format_block(
                    provider_url,
                    response_text
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
        tags: ResultSet[Tag],
        selectors: list[str] | dict
    ) -> list[str]:
    """
    Extract text content from the first element matching any of the
    provided selectors.

    Args:
        tag (ResultSet[Tag]):
            The BeautifulSoup tag to search within.

        selectors (list[str] | AvailabilityDict):
            A list of CSS selectors or an `AvailabilityDict` containing
            'available' and 'not_available' lists of selectors.

    Returns:
        str:
            The text of the first matching element, stripped of whitespace,
            or "N/A" if no element matches.
    """

    results: list[str] = []

    norm_selectors: list[str] = await __normalize_selectors(selectors)
    
    for sel in norm_selectors:
        for tag in tags:
            elem: Tag | None = tag.select_one(sel)

            if elem:
                results.append(str(elem))

            else: 
                results.append("N/A")
        
    return results


async def __select_all_text(
        tags: list[Tag],
        selectors: list[str] | dict,
        availability_alt_texts: re.Pattern[str] | None
    ) -> list[str]:
    """"""

    results: list[str] = []

    for tag in tags:
        texts: list[str] = []

        if isinstance(selectors, dict):
            for state, sel_list in selectors.items():
                for sel in sel_list:
                    for elem in tag.select(sel):
                        text: str = elem.get_text(strip=True)

                        if availability_alt_texts and state == "available":
                            if re.search(availability_alt_texts, text):
                                text = "Available"
                        
                        if text:
                            texts.append(text)
        else:
            for sel in selectors:
                for elem in tag.select(sel):
                    text = elem.get_text(strip=True)

                    if text:
                        texts.append(text)

        results.append(", ".join(texts) if texts else "N/A")

    return results


async def __extract_attribute_from_selectors(
        tags: ResultSet[Tag],
        selectors: list[str] | None,
        priority_attributes: list[str]
    ) -> list[str]:
    """"""

    results: list[str] = []

    if not selectors:
        return ["N/A"] * len(tags)

    for tag in tags:
        found_val: str = "N/A"

        for sel in selectors:
            container: Tag | None = tag.select_one(sel)
            
            if container:
                candidates: list[Tag] = [container] + container.find_all(True)
                
                for cand in candidates:
                    for attr in priority_attributes:
                        if cand.has_attr(attr):
                            val = cand.get(attr)

                            if val:
                                found_val = str(val)
                                break

                    if found_val != "N/A": 
                        break
            
            if found_val != "N/A": 
                break
            
        results.append(found_val)

    return results


async def __format_block(
        provider_name: str,
        products: list[dict[str, str]] | str
    ) -> str:
    """
    Format a block of text with the provider name followed by
    formatted product details.

    Args:
        provider_name (str):
            The name of the provider.

        products (list[dict[str, str]]):
            A list of dictionaries, each containing product info
            (e.g., 'name', 'price', 'availability').

    Returns:
        str:
            A single string with the provider name in uppercase,
            followed by the product details joined with " | ".
    """
    
    if isinstance(products, list):
        formatted_lines: list[str] = []

        for p in products:
            line = " | ".join([
                provider_name.upper(),
                p.get("name", "N/A"),
                p.get("availability", "N/A"),
                p.get("price", "N/A"),
                p.get("link", "N/A")
            ])

            formatted_lines.append(line)
    
        return "\n".join(formatted_lines)
    
    else:
        return " | ".join(
            [provider_name.upper(), products]
        )