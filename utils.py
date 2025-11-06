
import requests
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Literal
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


class Providers(Enum):
    """
    Enum for the providers of professional items
    """

    GRUPPOCOMET = "gruppocomet"


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
            result_container: List[str],
            popup_selectors: List[str],
            logout_selectors: List[str],
            title_classes: List[str],
            availability_classes: List[str],
            price_classes: List[str]
        ):

        self.name = provider_name
        self.url = provider_url
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
        except requests.RequestException:
            return False
        

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
    

class ClassifyRequest(BaseModel):
    """
    Classify user's requests into 'question' or 'command'.
    """

    request_class: Literal["question", "command"] = Field(
        description=(
            "Request class: 'question' if it's a question "
            "about one or more items; 'command' if it's a "
            "simple scraping request."
        )
    )