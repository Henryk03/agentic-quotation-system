
import re
import bs4
import asyncio
from providers import PROVIDER_MAP, Providers
from log_in_manager import AsyncLoginManager
from utils import BaseProvider
from playwright.async_api import (
    async_playwright,
    Page,
    TimeoutError as PlaywrightTimeoutError
)


async def scrape_products(products: list[str]) -> list[str]:
    """
    Perform web scraping for each product in the given list. Every product is scraped off
    each provider's website.

    Args:
        products (list[str]):
            A list of product names or keywords to search for.

    Returns:
        list[str]:
            A list of scrape results, where each element is a formatted `str` containing 
            the scraped information for a product.
    """
    
    web_search_results_list = []

    async with async_playwright() as apw:

        login_manager = AsyncLoginManager(apw)
        browser_context_pages = []

        for provider in Providers:
            context = await login_manager.ensure_context(
                await __get_provider(provider)
            )
            browser_context_pages.append(
                (provider, await context.new_page())
            )

        await asyncio.gather(
            *(__scrape_website(
                provider, 
                page,
                products, 
                web_search_results_list) for provider, page in browser_context_pages
            )
        )

    web_search_results_str = "\n\n".join([result for result in web_search_results_list])

    return web_search_results_str

  
async def __scrape_website(
        provider_enum: Providers,
        page: Page,
        products: list[str],
        result_list: list[str]
    ) -> None | str:
    """
    Perform web actions on the given provider's website to gather informations 
    about the given products. These informations are then inserted into the given
    `result_list`.

    Args:
        provider (Providers):
            A provider for the products.

        page (Page):
            A webpage used to search for the products.

        products (list[str]):
            A list containig all the products to be searched on the website.
            
        result_list (list[str]):
            A list that will contain the scraping's results as strings.

    Returns:
        None | str
        - `None` if no problem was encountered during the execution.
        - `str` with the error message if the something went wrong.
    """

    provider = await __get_provider(provider_enum)

    await page.goto(provider.url)
    await page.wait_for_load_state("load")

    search_texts = re.compile(
        r"ricerca|cerca per attributo|search",
        re.IGNORECASE
    )
    
    for item in products:

        item = item.strip()

        try:
            await page.get_by_role("textbox", name=search_texts).fill(item)
            await page.keyboard.press("Enter")

            found = await __wait_for_any_selector(page, provider.result_container)
            if not found:
                result_list.append(
                    await __format_block(
                        provider=provider,
                        lines=[f"Nessun risultato trovato per '{item}'."] 
                    )  
                )
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

        result_list.append(
            await __format_block(
                provider,
                [product_name, product_availability, f"Prezzo: {product_price}"]
            )
        )


async def __get_provider(provider_enum: Providers) -> BaseProvider:
    """"""

    provider_class = PROVIDER_MAP.get(provider_enum)
    if not provider_class:
        raise ValueError(f"Provider {provider_enum.name} not supported.")

    return provider_class() 


async def __wait_for_any_selector(
        page: Page,
        selectors: list[str],
        timeout: float = 2000
    ) -> str | None:
    """"""

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
        selectors: list[str],
        timeout: float = 2000
    ) -> None:
    """"""

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
        selectors: list[str]
    ) -> str:
    """"""
    
    for sel in selectors:
        elem = tag.select_one(sel)
        if elem:
            return elem.get_text(strip=True)
        
    return "N/A"


async def __select_all_text(
        tag: bs4.element.Tag,
        selectors: list[str]
    ) -> str:
    """"""

    availability_text = ""

    for sel in selectors:
        elems = tag.select(sel)
        if elems:
            for e in elems:
                availability_text += e.get_text(strip=True)
                availability_text += "\n"
    
    return availability_text


async def __format_block(
        provider: Providers,
        lines: list[str]
):
    """"""

    header = f"{'=' * 20} {provider.name.upper()} {'=' * 20}"
    footer = "=" * (len(provider.name) + 42)
    return "\n".join([header, *lines, footer])