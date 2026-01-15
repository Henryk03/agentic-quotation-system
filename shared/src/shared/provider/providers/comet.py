
from shared.provider.base_provider import BaseProvider


class Comet(BaseProvider):

    def __init__(self):
        super().__init__(
            provider_name = "Comet",
            provider_url = "https://comet.it",
            login_required = False,
            result_container = [".c-cd-prodotto"],
            popup_selectors = [
                "button.iubenda-cs-reject-btn",
                "i.btn-close-popup"
            ],
            logout_selectors = [],
            title_classes = [".c-cd-prodotto__titolo"], 
            availability_classes = {
                "available": [".c-btn-primary"], 
                "not_available": [".text-h5-semibold"]
            },
            price_classes = [".c-cd-prodotto__prezzo-finale"]
        )