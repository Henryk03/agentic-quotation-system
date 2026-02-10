
from re import Pattern

import requests
from playwright.async_api import (
    Page,
    ElementHandle
)

from shared.playwright.captcha_detection import detect_captcha
from shared.shared_utils.common.dictionaries import AvailabilityDict
from shared.playwright.page_utilities import (
    find_elements_with_attr_pattern,
    close_popups
)


class BaseProvider:
    """
    Base class representing a provider and its optional login logic.

    Provider instances are registered explicitly through a central
    registry. Each provider defines how products are searched, how
    results are parsed, and whether authentication is required to
    access the website.

    Attributes:
        availability_classes (AvailabilityDict):
            CSS classes or selectors used to detect product availability.

        availability_pattern (Pattern[str] | None):
            Regular expression used to identify availability based on specific 
            actionable text (e.g., "Add to cart"). If `None`, availability is 
            determined solely via CSS classes.

        login_required (bool):
            Indicates whether authentication is required to browse
            the provider's site.

        logout_selectors (list[str] | None):
            HTML selectors for buttons or links used to perform logout.
            Can be `None` if the provider doesn't require a specific selector 
            logic.

        logout_texts (Pattern[str] | None):
            Regular expression used to match visible text elements
            associated with logout actions on the provider's website.
            Can be `None` if logout is handled exclusively via selectors
            or is not required.

        name (str):
            The provider's display name.

        popup_selectors (list[str]):
            HTML selectors used to detect and close popup elements.

        price_classes (list[str]):
            CSS classes used to extract the product's price.

        result_container (list[str]):
            HTML selectors identifying the container of search results.

        search_texts (Pattern[str]):
            Regular expression used to match search-related text
            elements (e.g. placeholders, aria-labels, buttons) on the
            provider's website.

        title_classes (list[str]):
            CSS classes specifying the title element within a search result.

        url (str):
            The URL of the provider's website.

    Raises:
        ValueError:
            If the provider's website URL is not valid or not reachable.
    """


    def __init__(
        self,
        availability_classes: AvailabilityDict,
        availability_pattern: Pattern[str] | None,
        login_required: bool,
        logout_selectors: list[str] | None,
        logout_texts: Pattern[str] | None,
        popup_selectors: list[str],
        price_classes: list[str],
        provider_name: str,
        provider_url: str,
        result_container: list[str],
        search_texts: Pattern[str],
        title_classes: list[str],
    ):
        self.availability_classes = availability_classes
        self.availability_pattern = availability_pattern
        self.login_required = login_required
        self.logout_selectors = logout_selectors
        self.logout_texts = logout_texts
        self.name = provider_name
        self.popup_selectors = popup_selectors
        self.price_classes = price_classes
        self.result_container = result_container
        self.search_texts = search_texts
        self.title_classes = title_classes
        self.url = provider_url

        if not self.__is_valid_url(provider_url):
            raise ValueError(
                (
                    f"Invalid or unreachable URL for provider {self.name}.\n"
                    "Please, fix the error by providing a valid URL."
                )
            )
        

    @staticmethod
    def __is_valid_url(url: str) -> bool:
        """
        Check whether the given URL is reachable.

        The URL is considered valid if:

        - An HTTP HEAD request responds with a status code < 400.
        - The request fails due to an SSL error (e.g. expired certificate),
          which is interpreted as “reachable but with SSL issues”.

        Returns:
            bool:
                - `True` if the URL is reachable or returns an SSL-related error.
                - `False` if the URL is invalid or unreachable.
        """

        try:
            response = requests.head(url)
            return response.status_code < 400 
             
        except requests.RequestException:
            return False

        
    def has_auto_login(self) -> bool:
        """
        Determine whether the current `BaseProvider` instance provides
        its own implementation of the `auto_login` method. This is true
        only if the subclass overrides the default `BaseProvider.auto_login`
        implementation.

        Returns:
            bool:
                - `True` if the provider defines a custom `auto_login` method.
                - `False` otherwise.
        """

        return self.auto_login.__func__ is not BaseProvider.auto_login
        
    
    async def auto_login(
            self, 
            page: Page,
            credentials: dict
        ) -> bool:
        """
        Default automatic login implementation, which performs no action.
        Subclasses of `BaseProvider` should override this method to
        implement provider-specific authentication logic.

        Args:
            page (Page):
                The page instance already navigated to the provider's
                login area.

        Returns:
            bool:
                - `True` if the login procedure succeeds,
                - `False` otherwise.
        """

        return False
    

    async def is_logged_in(
            self,
            page: Page
        ) -> bool:
        """
        Check if the user is logged-in into the website in
        the given webpage.

        Args:
            page (Page):
                A page at the given provider's website.

        Returns:
            bool
            - `True` if the user is logged-in.
            - `False` otherwise.
        """

        try:
            if self.logout_selectors and self.logout_texts:
                results: list[ElementHandle] = (
                    await find_elements_with_attr_pattern(
                        page,
                        self.logout_selectors,
                        self.logout_texts,
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
    

    async def has_captcha(
            self,
            page: Page
        ) -> bool:
        """"""

        return await detect_captcha(page)  
    

    async def close_all_popups(
            self,
            page: Page
        ) -> None:
        """"""

        await close_popups(
            self.popup_selectors,
            page
        )