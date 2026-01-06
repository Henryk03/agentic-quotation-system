
import re
import bs4
import asyncio
from google import genai
from google.genai import types
from src.prompts import USER_PROMPT
from google.genai.types import Content, Part
from utils.provider.base_provider import BaseProvider
from utils.browser.login_manager import AsyncBrowserContextMaganer
from utils.common.lists import SafeAsyncList
from utils.computer_use.functions import (
    execute_function_calls,
    get_function_responses
)
from playwright.async_api import (
    async_playwright,
    Page,
    TimeoutError as PlaywrightTimeoutError
)


async def search_products(
        products: list[str]
    ) -> str:
    """
    Perform web search for each product in the given list.

    Args:
        products (list[str]):
            A list of product names or keywords to search for.

    Returns:
        str:
            A formatted string containing the information found 
            for each product.
    """

    # this import is necessary in order to have the registry
    # populated by the subclasses of `BaseProvider`
    from utils.provider import providers
    
    web_search_results_list = SafeAsyncList()

    async with async_playwright() as apw:

        browser_context_manager = AsyncBrowserContextMaganer(apw)
        provider_page = []

        for provider in BaseProvider.registry.values():
            context = await browser_context_manager.ensure_provider_context(
                provider
            )
            provider_page.append(
                (provider, await context.new_page())
            )

        await asyncio.gather(
            *(__search_in_website(
                provider, 
                page,
                products, 
                web_search_results_list) for provider, page in provider_page
            )
        )

        # clean up
        for _, page in provider_page:
            await AsyncBrowserContextMaganer.close_page_resources(page)

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
        - `str` with the error message if the something went wrong.
    """

    await page.goto(provider.url)
    await page.wait_for_load_state("load")

    # insert here the aria-labels of the 
    # textboxes used to search a product
    search_texts = re.compile(
        r"cerca (per attributo|un prodotto)|ricerca|search",
        re.IGNORECASE
    )
    
    for item in products:

        item = item.strip()
        try:
            await page.get_by_role("textbox", name=search_texts).fill(item)
            await page.keyboard.press("Enter")

            found = await __wait_for_any_selector(page, provider.result_container)
            if not found:
                formatted_block = await __format_block(
                    provider,
                    [f"Nessun risultato trovato per '{item}'."] 
                )
                await result_list.add(formatted_block)

                # let's check the next item...
                continue

        except Exception as e:
            return f"Unexpected error while searching '{item}': {e}"
        
        await __wait_for_any_selector(page, provider.title_classes)
        await __wait_for_all_selectors(page, provider.availability_classes)
        await __wait_for_any_selector(page, provider.price_classes)

        html = await page.content()
        soup = bs4.BeautifulSoup(html, "html.parser")

        product_container = soup.select_one(found)
        if not product_container:
            continue
        
        product_name = await __select_text(
            product_container, 
            provider.title_classes
        )
    
        product_availability = await __select_all_text(
            product_container,
            provider.availability_classes
        )
        
        product_price = await __select_text(
            product_container,
            provider.price_classes
        )

        formatted_block = await __format_block(
            provider,
            [
                product_name,
                product_availability,
                product_price
            ]            
        )

        await result_list.add(formatted_block)


async def search_products_with_computer_use(
        product_list: list[str],
        website: str
    ) -> str:
    """
    Navigates the given website to search for products based on a user's request.
    The function simulates realistic browsing behavior, visits the specified site,
    analyzes the provided product list, and returns a synthesized summary of the
    discovered information.

    Args:
        user_request (str):
            A natural-language description of what the user wants to find.

        website (str):
            The URL of the website to navigate and inspect.

        products (list[str]):
            A list of product names or identifiers to look for on the website.

    Returns:
        str:
            A textual summary describing the results of the product search 
            performed on the site.
    """

    _, _, page = await AsyncBrowserContextMaganer.create_browser_context(
        headless=False,
        start_url="https://google.com"
    )

    try:
        client = genai.Client()

        generate_content_config = genai.types.GenerateContentConfig(
            tools=[
                types.Tool(
                    computer_use=types.ComputerUse(
                        environment=types.Environment.ENVIRONMENT_BROWSER
                    )
                )
            ]
        )

        initial_screenshot = await page.screenshot(type="png")

        products = "\n".join(f"- {p}" for p in product_list)

        prompt_filled = USER_PROMPT.format(
            products_list=products,
            website=website
        )

        contents = [
            Content(
                role="user",
                parts=[
                    Part(text=prompt_filled),
                    Part.from_bytes(data=initial_screenshot, mime_type='image/png')
                ]
            )
        ]

        max_iter = 10
        for i in range(max_iter):
            model_response = client.models.generate_content(
                model='gemini-2.5-computer-use-preview-10-2025',
                contents=contents,
                config=generate_content_config,
            )

            candidate = model_response.candidates[0]
            contents.append(candidate)

            has_function_calls = any(
                part.function_call for part in candidate.content.parts
            )

            if not has_function_calls:
                response_text = " ".join(
                    [part.text for part in candidate.content.parts if part.text]
                )
                break

            results = execute_function_calls(candidate, page)
            function_responses = get_function_responses(page, results)

            contents.append(
                Content(
                    role="user",
                    parts=[
                        Part(function_response=fr) for fr in function_responses
                    ]
                )
            )

    finally:
        await AsyncBrowserContextMaganer.close_page_resources(page)
        return response_text



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
    ) -> None:
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

    selectors = await __normalize_selectors(selectors)
    
    for sel in selectors:
        elem = tag.select_one(sel)
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
    availability_alt_texts = re.compile(
        r"aggiungi al carrello|add to cart", 
        re.IGNORECASE
    )

    texts: list[str] = []

    if isinstance(selectors, dict):
        for state, sel_list in selectors.items():
            for sel in sel_list:
                for elem in tag.select(sel):
                    text = elem.get_text(strip=True)
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
        provider: BaseProvider,
        lines: list[str]
    ):
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
            f"{provider.name.upper()}",
            *lines
        ]
    )
