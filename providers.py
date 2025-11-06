
import os
import re
from dotenv import load_dotenv
from pathlib import Path
from utils import BaseProvider, Providers


class GruppoComet(BaseProvider):

    def __init__(self):
        super().__init__(
            provider_name = "gruppocomet",
            provider_url = "https://gruppocomet.it/simevignuda",
            result_container = [".result-block-v2"],
            popup_selectors = ["button.iubenda-cs-close-btn", "a#eu-privacy-close"],
            logout_selectors = ["a"],
            title_classes = [".result-title"], 
            availability_classes = [".disp-no", ".disp-ok"],
            price_classes = [".result-price"]
        )

    async def auto_login(self, page):

        login_texts = re.compile(
            "accedi",
            re.IGNORECASE
        )

        try:
            await page.get_by_role("link", name=login_texts).click()

            env_path = Path(__file__).parent / ".env"
            load_dotenv(dotenv_path=env_path)

            await page.locator(
                "input[name='username']"
            ).fill(
                os.getenv("GRUPPOCOMET_USERNAME")
            )

            await page.locator(
                "input[name='password']"
            ).fill(
                os.getenv("GRUPPOCOMET_PASSWORD")
            )

            await page.keyboard.press("Enter")
            return True
        except:
            return False
        


PROVIDER_MAP = {
    Providers.GRUPPOCOMET: GruppoComet
}