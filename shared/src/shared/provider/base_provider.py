
from re import Pattern

import requests
from playwright.async_api import (
    ElementHandle,
    Page
)

from shared.playwright.captcha_detection import detect_captcha
from shared.playwright.page_utilities import (
    find_elements_with_attr_pattern,
    close_popups
)
from shared.shared_utils.common.dictionaries import AvailabilityDict


class BaseProvider:
    """
    Base class representing a provider and its optional login logic.

    Attributes
    ----------
    availability_classes : AvailabilityDict
        CSS classes or selectors used to detect product availability.

    availability_texts : Pattern[str] | None
        Regular expression used to identify availability based 
        on specific text. If `None`, availability is determined 
        only via CSS classes.

    login_required : bool
        Indicates whether authentication is required to browse 
        the provider's site.

    logout_selectors : list[str] | None
        HTML selectors for logout buttons or links. `None` if not 
        needed.

    logout_texts : Pattern[str] | None
        Regex to match logout-related visible text elements. 
        `None` if not needed.

    name : str
        The provider's display name.

    popup_selectors : list[str]
        HTML selectors for popups to be closed.

    price_classes : list[str]
        CSS classes used to extract product price.

    product_link_selectors : list[str]
        HTML selectors to locate product links or parent containers.

    result_container : list[str]
        HTML selectors identifying the search result container.

    search_texts : Pattern[str]
        Regex to match search-related text elements on the provider's site.

    title_classes : list[str]
        CSS classes specifying the title element within a search result.

    url : str
        URL of the provider's website.

    Raises
    ------
    ValueError
        If the provider's URL is not valid or unreachable.

    Notes
    -----
    To ensure data accuracy, selectors provided for links and 
    other fields must be as specific as possible.
    """


    def __init__(
        self,
        availability_classes: AvailabilityDict,
        availability_texts: Pattern[str] | None,
        login_required: bool,
        logout_selectors: list[str] | None,
        logout_texts: Pattern[str] | None,
        popup_selectors: list[str],
        price_classes: list[str],
        product_link_selectors: list[str],
        provider_name: str,
        provider_url: str,
        result_container: list[str],
        search_texts: Pattern[str],
        title_classes: list[str],
    ):
        self.availability_classes = availability_classes
        self.availability_texts = availability_texts
        self.login_required = login_required
        self.logout_selectors = logout_selectors
        self.logout_texts = logout_texts
        self.name = provider_name
        self.popup_selectors = popup_selectors
        self.price_classes = price_classes
        self.product_link_selectors = product_link_selectors
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
    def __is_valid_url(
            url: str
        ) -> bool:
        """
        Check whether the given URL is reachable.

        Parameters
        ----------
        url : str
            The URL to validate.

        Returns
        -------
        bool
            `True` if reachable (status < 400) or SSL error occurs.
            `False` otherwise.
        """

        try:
            response = requests.get(url, stream = True)
            return response.status_code < 400 
             
        except requests.RequestException:
            return False

        
    def has_auto_login(self) -> bool:
        """
        Determine if the provider defines a custom auto-login method.

        Returns
        -------
        bool
            `True` if `auto_login` is overridden, `False` otherwise.
        """

        return self.auto_login.__func__ is not BaseProvider.auto_login
        
    
    async def auto_login(
            self, 
            page: Page,
            username: str,
            password: str
        ) -> bool:
        """
        Default auto-login implementation.

        Subclasses should override to implement provider-specific 
        login logic.

        Parameters
        ----------
        page : Page
            Playwright page already navigated to the login area.

        username : str
            User's login username.

        password : str
            User's login password.

        Returns
        -------
        bool
            `True` if login succeeds, `False` otherwise.
        """

        return False
    

    async def is_logged_in(
            self,
            page: Page
        ) -> bool:
        """
        Check if the user is logged in on the website.

        Parameters
        ----------
        page : Page
            Playwright page at the provider's website.

        Returns
        -------
        bool
            `True` if logged in, `False` otherwise.
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
        """
        Detect if a captcha is present on the page.

        Parameters
        ----------
        page : Page
            Playwright page to inspect.

        Returns
        -------
        bool
            `True` if captcha is detected, `False` otherwise.
        """

        return await detect_captcha(page)  
    

    async def close_all_popups(
            self,
            page: Page
        ) -> None:
        """
        Close all popups on the provider's page using registered 
        selectors.

        Parameters
        ----------
        page : Page
            Playwright page on which popups should be closed.

        Returns
        -------
        None
        """

        await close_popups(
            self.popup_selectors,
            page
        )