
import re

from shared.provider.base_provider import BaseProvider


class MediaWorld(BaseProvider):

    def __init__(self):
        super().__init__(
            availability_classes = {
                "available": [".sc-663022ae-0"], 
                "not_available": [".sc-59b6826e-0 jJIqay"]
            },
            availability_texts = re.compile(
                r"aggiungi al carrello", 
                re.IGNORECASE
            ),
            login_required = False,
            logout_selectors = None,
            logout_texts = None,
            popup_selectors = [
                "button.sc-74ef8087-1"
            ],
            price_classes = [
                ".mms-ui-sr_true"
            ],
            product_link_selectors = [
                "a.sc-66506eb5-1"
            ],
            provider_name = "MediaWorld",
            provider_url = "https://mediaworld.it",
            result_container = [
                "article.mms-ui-color-palette_base"
            ],
            search_texts = re.compile(
                "cosa stai cercando", 
                re.IGNORECASE
            ),
            title_classes = [
                ".sc-59b6826e-0"
            ]         
        )

provider: BaseProvider = MediaWorld()