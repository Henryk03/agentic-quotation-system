
import re

import requests
from playwright.async_api import Page, ElementHandle

from shared.playwright.page_utilities import find_elements_with_attr_pattern
from shared.playwright.captcha_detection import detect_captcha
from shared.shared_utils.common.dictionaries import AvailabilityDict


class BaseProvider:
    """
    Base class representing a provider and its optional login logic.
    Each subclass is automatically registered, and the registry stores 
    ready-to-use instances.

    Attributes:
        name (str):
            The provider's name.

        url (str):
            The URL of the provider's website.

        login_required (bool):
            Indicates whether authentication is required to browse
            the provider's site.

        result_container (list[str]):
            HTML selectors identifying the container of search results.

        popup_selectors (list[str]):
            HTML selectors used to detect and close popup elements.

        logout_selectors (list[str]):
            HTML selectors for buttons or links used to perform logout.

        title_classes (list[str]):
            CSS classes specifying the title element within a search result.

        availability_classes (AvailabilityDict):
            CSS classes or selectors used to detect product availability.

        price_classes (list[str]):
            CSS classes used to extract the product's price.

    Raises:
        ValueError:
            If the provider's website is not reachable.
        
    """


    def __init__(
            self,
            provider_name: str,
            provider_url: str,
            login_required: bool,
            result_container: list[str],
            popup_selectors: list[str],
            logout_selectors: list[str],
            title_classes: list[str],
            availability_classes: AvailabilityDict,
            price_classes: list[str]
        ):

        self.name = provider_name
        self.url = provider_url
        self.login_required = login_required
        self.result_container = result_container
        self.popup_selectors = popup_selectors
        self.logout_selectors = logout_selectors
        self.title_classes = title_classes
        self.availability_classes = availability_classes
        self.price_classes = price_classes

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
                - `True` if the provider defines a custom `auto_login` method,
                - `False` otherwise.
        """

        return self.auto_login.__func__ is not BaseProvider.auto_login
        
    
    async def auto_login(self, _: Page) -> bool:
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
            logout_texts: re.Pattern[str] = re.compile(
                r"(?:log|sign)[- ]?out",
                re.IGNORECASE
            )

            results: list[ElementHandle] = (
                await find_elements_with_attr_pattern(
                    page,
                    self.logout_selectors,
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
    

    async def has_captcha(
            self,
            page: Page
        ) -> bool:
        """"""

        return await detect_captcha(page)