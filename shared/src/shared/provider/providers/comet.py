
import re

from shared.provider.base_provider import BaseProvider


class Comet(BaseProvider):

    def __init__(self):
        super().__init__(
            availability_classes = {
                "available": [".c-btn-primary"], 
                "not_available": [".text-h5-semibold"]
            },
            availability_pattern = re.compile(
                r"aggiungi al carrello", 
                re.IGNORECASE
            ),
            login_required = False,
            logout_selectors = None,
            logout_texts = None,
            popup_selectors = [
                "button.iubenda-cs-reject-btn",
                "i.btn-close-popup"
            ],
            price_classes = [
                ".c-cd-prodotto__prezzo-finale"
            ],
            provider_name = "Comet",
            provider_url = "https://comet.it",
            result_container = [
                ".c-cd-prodotto"
            ],
            search_texts = re.compile(
                "cerca un prodotto", 
                re.IGNORECASE
            ),
            title_classes = [
                ".c-cd-prodotto__titolo"
            ]         
        )

provider: BaseProvider = Comet()