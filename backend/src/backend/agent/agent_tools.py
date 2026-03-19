
import asyncio
import re
from typing import Any, Callable, Coroutine

from bs4 import BeautifulSoup, ResultSet, Tag
from google import genai
from langchain_core.runnables import RunnableConfig
from playwright.async_api import (
    async_playwright,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)
from backend.agent.prompts import (
    COMPUTER_USE_SYSTEM_PROMPT,
    USER_PROMPT,
)
from backend.backend_utils.browser import (
    AsyncBrowserContextMaganer,
    init_chrome_page,
)
from backend.backend_utils.common import SafeAsyncList
from backend.backend_utils.computer_use import (
    ComputerUseSession,
    generate_content_config,
    run_computer_use_loop,
    save_product,
)
from backend.backend_utils.exceptions import LoginFailedException
from backend.config import settings

from shared.exceptions import ProviderNotSupportedException
from shared.playwright.page_utilities import close_page_resources
from shared.provider.base_provider import BaseProvider
from shared.provider.registry import get_provider


async def search_products(
        config: RunnableConfig,
        products: list[str]
    ) -> str:
    """
    Searches for multiple products across the selected providers.

    This function iterates through the list of products and retrieves 
    details from each provider, respecting a maximum number of results 
    for each individual product search.

    Parameters
    ----------
    config : langchain_core.runnables.RunnableConfig 
        Configuration for the LangChain runnable, containing callbacks, 
        tags, and other execution metadata.

    products : list[str] 
        A list of product names, models, or keywords to investigate.

    Returns
    -------
    str
        A concatenated and formatted string containing the aggregated 
        search results, structured for easy parsing or LLM consumption.
    """
    
    client_id: str | None
    selected_stores: list[str] | None
    limit_per_product: int = 1

    web_search_results_list: SafeAsyncList
    browser_context_manager: AsyncBrowserContextMaganer

    async with async_playwright() as apw:
        client_id = (
            config
            .get("configurable", {})
            .get("client_id", None)
        )
        selected_stores = (
            config
            .get("configurable", {})
            .get("selected_stores", None)
        )
        limit_per_product = (
            config
            .get("configurable", {})
            .get("items_per_store", 1)
        )

        if not selected_stores:
            return (
                "No store is currently selected. To perform a "
                "search, please choose at least one store using "
                "the 'Select Store' button in the sidebar."
            )
        
        web_search_results_list = SafeAsyncList()
        browser_context_manager = AsyncBrowserContextMaganer(
            apw, 
            client_id
        )

        tasks: list[Coroutine[Any, Any, Any]] = []
        pages_to_close: list[Page] = []

        for store in selected_stores:
            try:
                provider_instance: BaseProvider = get_provider(
                    store
                )

                context: BrowserContext | None = (
                    await browser_context_manager.ensure_provider_context(
                        client_id,
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
                page = await init_chrome_page(
                    apw,
                    settings.HEADLESS
                )
                pages_to_close.append(page)

                tasks.append(
                    __search_with_computer_use(
                        store,
                        page,
                        products,
                        web_search_results_list,
                        limit_per_product
                    )
                )

            except LoginFailedException as lfe:
                await web_search_results_list.add(
                    await __format_block(store, str(lfe))
                )

            except Exception as e:
                await web_search_results_list.add(
                    await __format_block(store, str(e))
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
    ) -> None:
    """
    Search one or more products on a provider's website and append
    formatted result blocks to a shared asynchronous result container.

    The function navigates to the provider homepage, performs a search
    for each non-empty product string, waits for the results to load,
    extracts up to `limit_per_product` matches, and formats the
    collected data (title, availability, price, link) into structured
    blocks.

    Errors occurring during individual product searches are captured
    and appended to `result_list` without interrupting the overall
    execution flow.

    Parameters
    ----------
    provider : BaseProvider
        Concrete provider implementation responsible for defining
        the target URL and all selectors required to perform
        search and data extraction.

    page : playwright.async_api.Page
        Initialized Playwright page instance used for navigation,
        interaction, and HTML retrieval.

    products : list of str
        Collection of product names or search queries.
        Leading and trailing whitespace is removed.
        Empty strings are ignored.

    result_list : SafeAsyncList
        Asynchronous thread-safe container where formatted
        result blocks (successes or errors) are appended.

    limit_per_product : int, optional
        Maximum number of result entries extracted for each
        product query. Default is 1.

    Returns
    -------
    None
        The function does not return a value. It mutates
        `result_list` by appending formatted entries.

    Raises
    ------
    None
        Exceptions are handled internally. Any error is
        converted into a formatted message and appended
        to `result_list`.s
    """

    try:
        await page.goto(provider.url)
        await provider.close_all_popups(page)
        await page.wait_for_load_state("load")
        
        for item in products:
            item: str = item.strip()

            if not item:
                continue

            try:
                for inputbox in ["textbox", "combobox", "searchbox"]:
                    try:
                        await page.get_by_role(
                            inputbox, 
                            name = provider.search_texts
                        ).fill(
                            item,
                            timeout = 500
                        )
                        await page.keyboard.press("Enter")
                        break

                    except PlaywrightTimeoutError:
                        continue

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

                    continue
            
                _ = await __wait_for_any_selector(
                    page, 
                    provider.title_classes
                )
                _ = await __wait_for_all_selectors(
                    page, 
                    dict(provider.availability_classes)
                )
                _ = await __wait_for_any_selector(
                    page, 
                    provider.price_classes
                )

                await page.wait_for_load_state("load")

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
                            dict(provider.availability_classes),
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
                    if link[0] == "/":
                        link = provider.url + link

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
    """
    Search for products on a website using an AI-driven computer-use 
    loop and append formatted results to a shared asynchronous container.

    This function initializes a generative AI client configured for
    browser-based interaction, builds a prompt describing the requested
    products, and executes a computer-use session that interacts with
    the provided Playwright page. Extracted product data is collected
    into `products_data` and formatted before being appended to
    `result_list`.

    If no product information is gathered, a fallback message is added
    instead. All exceptions are silently handled to prevent interruption
    of the calling workflow.

    Parameters
    ----------
    provider_url : str
        Base URL of the target website. Used in the generated prompt
        and in result formatting.

    page : playwright.async_api.Page
        Initialized Playwright page instance used as the execution
        environment for the computer-use loop.

    products : list of str
        List of product names or search queries to be included
        in the generated prompt.

    result_list : SafeAsyncList
        Asynchronous thread-safe list where formatted
        result blocks are appended.

    limit_per_product : int, optional
        Maximum number of items requested per product in the
        generated prompt. Default is 1.

    Returns
    -------
    None
        The function does not return a value. It appends
        formatted results (or a fallback message) to `result_list`.

    Raises
    ------
    None
        All exceptions are suppressed internally. Failures
        result in an empty `products_data` collection,
        triggering a fallback message.

    Notes
    -----
    The function relies on an AI-driven interaction loop rather than
    deterministic DOM scraping. The quality and completeness of the
    results depend on the model's ability to correctly interpret and
    navigate the webpage.
    """

    products_data: list[dict[str, str]] = []

    excluded_functions: list[str] = [
        "drag_and_drop", 
        "open_web_browser",
        "key_combination"
    ]
    custom_functions: list[Callable[..., Any]] = [
        save_product
    ]

    try:
        client: genai.Client = genai.Client()

        config: genai.types.GenerateContentConfig = (
            generate_content_config(
                client,
                COMPUTER_USE_SYSTEM_PROMPT,
                excluded_functions,
                custom_functions
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

        await run_computer_use_loop(
            client,
            page,
            session,
            config,
            products_data
        )

    except:
        pass

    finally:
        if products_data:
            await result_list.add(
                await __format_block(
                    provider_url,
                    products_data
                )
            )

        else:
            await result_list.add(
                await __format_block(
                    provider_url,
                    "No result found for any of the products."
                )
            )


async def __normalize_selectors(
        selectors: list[str] | dict
    ) -> list[str]:
    """
    Normalize a selector container into a flat list of CSS selectors.

    If `selectors` is a dictionary, all its values are flattened
    into a single list. If it is already a list, it is returned
    unchanged.

    Parameters
    ----------
    selectors : list of str or dict
        Either a list of CSS selectors or a dictionary mapping
        arbitrary keys to lists of selectors.

    Returns
    -------
    list of str
        A flat list containing all selectors.

    Notes
    -----
    The function does not validate selector syntax. It only
    normalizes the container structure.
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
    Wait until at least one selector becomes visible on the page.

    Selectors are normalized into a flat list and tested sequentially.
    The first selector that reaches the `visible` state within
    the given timeout is returned.

    Parameters
    ----------
    page : playwright.async_api.Page
        Playwright page instance used for DOM querying.

    selectors : list of str or dict
        CSS selectors or a dictionary whose values are lists
        of CSS selectors.

    timeout : float, optional
        Maximum time (in milliseconds) to wait for each
        selector. Default is 2000.

    Returns
    -------
    str or None
        The first selector that becomes visible, or `None`
        if none are found within the timeout.

    Raises
    ------
    None
        Timeout errors are handled internally.
    """

    selectors = await __normalize_selectors(selectors)

    for sel in selectors:
        try:
            await page.wait_for_selector(
                selector = sel,
                state = "visible",
                timeout = timeout
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
    Wait until all provided selectors become visible.

    Selectors are normalized into a flat list and awaited
    concurrently using `asyncio.gather`.

    Parameters
    ----------
    page : playwright.async_api.Page
        Playwright page instance used for DOM querying.

    selectors : list of str or dict
        CSS selectors or a dictionary whose values are lists
        of CSS selectors.

    timeout : float, optional
        Maximum time (in milliseconds) to wait for each
        selector. Default is 2000.

    Returns
    -------
    bool
        `True` if all selectors become visible within
        the timeout, `False` if at least one times out.

    Raises
    ------
    None
        Timeout errors are captured and converted into
        a `False` return value.
    """

    norm_selectors: list[str] = await __normalize_selectors(
        selectors
    )

    try:
        await asyncio.gather(
            *(page.wait_for_selector(
                selector = sel,
                state = "visible",
                timeout = timeout) for sel in norm_selectors
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
    Extract HTML string representations from tags using 
    selectors.

    For each normalized selector and each tag in `tags`,
    the function searches for the first matching element.
    If found, the string representation of the element
    is appended to the result list. Otherwise, `"N/A"`
    is appended.

    Parameters
    ----------
    tags : bs4.element.ResultSet[bs4.element.Tag]
        Collection of BeautifulSoup tags representing
        product containers.

    selectors : list of str or dict
        CSS selectors or a dictionary whose values are lists
        of CSS selectors.

    Returns
    -------
    list of str
        A list containing extracted element strings or
        `"N/A"` placeholders.

    Notes
    -----
    The function returns the raw string representation
    of matched elements, not their stripped text content.
    """

    results: list[str] = []

    norm_selectors: list[str] = await __normalize_selectors(selectors)
    
    for sel in norm_selectors:
        for tag in tags:
            elem: Tag | None = tag.select_one(sel)

            results.append(
                elem.text.strip() 
                if elem 
                else "N/A"
            )
        
    return results


async def __select_all_text(
        tags: list[Tag],
        selectors: list[str] | dict,
        availability_alt_texts: re.Pattern[str] | None
    ) -> list[str]:
    """
    Extract and aggregate text content from tags using selectors.

    For each tag, all matching elements for the given selectors
    are collected. Extracted text values are stripped and joined
    into a comma-separated string. If no text is found for a tag,
    `"N/A"` is returned for that entry.

    If `selectors` is a dictionary, each key represents a
    semantic state (e.g., availability category). When
    `availability_alt_texts` is provided and the state is
    `"available"`, matching text can be normalized to
    `"Available"`.

    Parameters
    ----------
    tags : list of bs4.element.Tag
        List of BeautifulSoup tags representing product containers.

    selectors : list of str or dict
        CSS selectors or a dictionary mapping state labels
        to lists of selectors.

    availability_alt_texts : re.Pattern[str] or None
        Optional regular expression used to normalize
        availability text.

    Returns
    -------
    list of str
        One aggregated string per input tag.
    """

    results: list[str] = []

    for tag in tags:
        texts: list[str] = []

        if isinstance(selectors, dict):
            for state, sel_list in selectors.items():
                for sel in sel_list:
                    for elem in tag.select(sel):
                        text: str = elem.get_text(strip = True)

                        if availability_alt_texts and state == "available":
                            if re.search(availability_alt_texts, text):
                                text = "Available"
                        
                        if text:
                            texts.append(text)
        else:
            for sel in selectors:
                for elem in tag.select(sel):
                    text = elem.get_text(strip = True)

                    if text:
                        texts.append(text)

        results.append(", ".join(texts) if texts else "N/A")

    return results


async def __extract_attribute_from_selectors(
        tags: ResultSet[Tag],
        selectors: list[str] | None,
        priority_attributes: list[str]
    ) -> list[str]:
    """
    Extract prioritized attribute values from nested selectors.

    For each tag, selectors are evaluated in order. The first
    matching container is searched (including all its descendants)
    for the first available attribute listed in
    `priority_attributes`.

    Parameters
    ----------
    tags : bs4.element.ResultSet[bs4.element.Tag]
        Collection of BeautifulSoup tags representing
        product containers.

    selectors : list of str or None
        CSS selectors used to locate candidate elements.
        If `None` or empty, `"N/A"` is returned for all tags.

    priority_attributes : list of str
        Ordered list of attribute names to search for
        (e.g., `["href", "data-url"]`).

    Returns
    -------
    list of str
        Extracted attribute values or `"N/A"` if none
        are found for a given tag.

    Notes
    -----
    Selectors and attributes are evaluated in priority order.
    The first valid value found terminates the search
    for that tag.
    """

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
    Format product data into a provider-prefixed text block.

    If `products` is a list of dictionaries, each entry
    is formatted as a single line with fields separated
    by `" | "` and prefixed by the uppercased provider name.

    If `products` is a string, it is treated as a message
    and formatted as a single provider-prefixed line.

    Parameters
    ----------
    provider_name : str
        Name of the provider. It is converted to uppercase
        in the output.

    products : list of dict[str, str] or str
        Either a list of product dictionaries containing
        keys such as `"name"`, `"availability"`,
        `"price"`, and `"link"`, or a plain message string.

    Returns
    -------
    str
        A formatted string containing one or more lines
        ready for aggregation or display.
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