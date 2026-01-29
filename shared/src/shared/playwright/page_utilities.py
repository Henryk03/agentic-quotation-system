
import re
import asyncio

from playwright.async_api import (
    Browser, 
    BrowserContext, 
    Page, 
    ElementHandle,
)


async def find_elements_with_attr_pattern(
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

    async def check_tag(
            tag: str
        ) -> list[ElementHandle]:
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

        async def check_elem(
                element: ElementHandle
            ) -> ElementHandle | None:
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
       

async def close_page_resources(
        page: Page
    ) -> None:
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