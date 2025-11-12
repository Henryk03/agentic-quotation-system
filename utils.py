
import asyncio
import requests
from enum import Enum
from typing import TypedDict, Any
from playwright.async_api import Page

# # list containing the html tags (followed by
    # # their class(es) or id(s)) whose role is to show 
    # # informations about an item
    # result_containers = [
    #     ".result-block-v2"
    # ]

    # # list containing the html classes for
    # # the search of the product name (title)
    # title_classes = [
    #     ".result-title"
    # ]

    # # list containing the classes that mark
    # # the product availability status
    # availability_classes = [
    #     ".disp-no",
    #     ".disp-ok"
    # ]

    # # list containing the classes that
    # # that mark the price tag
    # price_classes = [
    #     ".result-price"
    # ]


class AvailabilityDict(TypedDict):
    """"""

    available: list[str]
    not_available: list[str]


class SafeAsyncList:
    """
    ADT for a thread-safe asynchronous list.
    """


    def __init__(self):
        self._list = []
        self._lock = asyncio.Lock()


    async def add(self, item: Any) -> None:
        """
        Safely append an item to the list.

        This method ensures that only one coroutine at a 
        time can modify the underlying list, preventing race
        conditions or data corruption.

        Args:
            item (Any):
                A generic item of any type to be inserted into
                the underlying list.
        """

        async with self._lock:
            self._list.append(item)


    async def get_all(self) -> list:
        """
        Return a deep copy of the list.

        The returned list represents the current state of the 
        internal data. Since it is a copy, modifications to the
        returned list do not affect the internal storage.
        """

        return list(self._list)


class Providers(Enum):
    """
    Enum for the providers of professional or commercial items
    """

    GRUPPOCOMET = "gruppocomet"
    COMET = "comet"


class BaseProvider:
    """
    Base class for provider data and optional log-in logic

    Attributes:
        name:
        url:
        
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
        """"""

        try:
            response = requests.head(url)
            return response.status_code < 400      
        except requests.RequestException:       # invalid URL
            return False
        except requests.exceptions.SSLError:    # expired certificate
            return True

        

    async def has_auto_login(self) -> bool:
        """"""

        return self.auto_login.__func__ is not BaseProvider.auto_login
        
    
    async def auto_login(self, page: Page) -> bool:
        """
        Default automatic log-in function that does nothing.
        Override this method for each provider, subclass of `BaseProvider`.

        Args:
            page (Page):
                The webpage of the provider.

        Returns:
            bool
            - `True` if the log-in was successful.
            - `False` otherwise.
        """

        print(f"Manual log-in required for {self.name}.")
        return False