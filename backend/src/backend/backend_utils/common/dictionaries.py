
from typing import TypedDict


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