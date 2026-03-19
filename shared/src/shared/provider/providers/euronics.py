
import re

from shared.provider.base_provider import BaseProvider


class Euronics(BaseProvider):

    def __init__(self):
        super().__init__(
            availability_classes = {
                "available": [
                    ".addToCart.btn-eur.add-to-cart-global.yellow.w-100"
                ], 
                "not_available": [
                    ".mw-100.w-100.btn-eur-outline-sm.blue"
                ]
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
                "div.product-layou.grid-mode"
            ],
            search_texts = re.compile(
                "inserisci parola chiave o numero articolo", 
                re.IGNORECASE
            ),
            title_classes = [
                ".tile-name"
            ]         
        )

provider: BaseProvider = Euronics()