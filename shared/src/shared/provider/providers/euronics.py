
import re

from shared.provider.base_provider import BaseProvider


class Euronics(BaseProvider):

    def __init__(self):
        super().__init__(
            availability_classes = {
                "available": [".addToCart"], 
                "not_available": [".btn-eur-outline-sm"]
            },
            availability_texts = re.compile(
                r"aggiungi", 
                re.IGNORECASE
            ),
            login_required = False,
            logout_selectors = None,
            logout_texts = None,
            popup_selectors = [
                "button.onetrust-close-btn-handler"
            ],
            price_classes = [
                ".price-formatted"
            ],
            product_link_selectors = [
                "a.text-dark"
            ],
            provider_name = "Euronics",
            provider_url = "https://euronics.it",
            result_container = [
                "div.product"
            ],
            search_texts = re.compile(
                "cosa stai cercando", 
                re.IGNORECASE
            ),
            title_classes = [
                ".tile-name"
            ]         
        )

provider: BaseProvider = Euronics()