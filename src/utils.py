
import asyncio
import requests
from pydantic import BaseModel
from typing import TypedDict, Any, Optional
from playwright.async_api import Page


class AvailabilityDict(TypedDict):
    """
    Dictionary specifying the CSS selectors used to identify product
    availability on a provider's website.

    Attributes:
        available (list[str]):
            List of selectors corresponding to products that are in stock.

        not_available (list[str]):
            List of selectors corresponding to products that are out of stock.
    """

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


class BaseProvider:
    """
    Base class representing a provider and its optional login logic.

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
                True if the URL is reachable or returns an SSL-related error.
                False if the URL is invalid or unreachable.
        """

        try:
            response = requests.head(url)
            return response.status_code < 400      
        except requests.RequestException:       # invalid URL
            return False
        except requests.exceptions.SSLError:    # expired certificate
            return True

        

    async def has_auto_login(self) -> bool:
        """
        Determine whether the current `BaseProvider` instance provides
        its own implementation of the `auto_login` method. This is true
        only if the subclass overrides the default `BaseProvider.auto_login`
        implementation.

        Returns:
            bool:
                True if the provider defines a custom `auto_login` method,
                False otherwise.
        """

        return self.auto_login.__func__ is not BaseProvider.auto_login
        
    
    async def auto_login(self, page: Page) -> bool:
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
                True if the login procedure succeeds,
                False otherwise.
        """

        return False
    

class ChatMessage(BaseModel):
    """
    Represents a single message within a chat conversation.

    Attributes:
        role (str):
            The role of the message sender (e.g. "user", "assistant", "system").

        content (str):
            The textual content of the message.
    """

    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    """
    Defines the request payload for generating a chat completion.

    Attributes:
        model (str):
            The identifier of the model to be used for the completion.

        messages (list[ChatMessage]):
            The ordered list of messages forming the conversation context.

        max_tokens (Optional[int]): 
            The maximum number of tokens the model is allowed to generate 
            in the response.

        temperature (Optional[float]):
            Controls randomness in the output; higher values produce more 
            diverse responses.

        stream (Optional[bool]):
            When set to True, the response is returned as a stream of partial 
            messages.
    """

    model: str = "gemini-2.5-flash"
    messages: list[ChatMessage]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.5
    stream: Optional[bool] = True
