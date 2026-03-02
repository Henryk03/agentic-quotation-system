
from typing import TypedDict


class AvailabilityDict(TypedDict):
    """
    Dictionary defining CSS selectors used to determine product 
    availability on a provider's website.

    Attributes
    ----------
    available : list[str]
        List of CSS selectors that indicate a product is in stock.

    not_available : list[str]
        List of CSS selectors that indicate a product is out of stock.
    """

    available: list[str]
    not_available: list[str]