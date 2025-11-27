
import os
import re
from getpass import getpass
from dotenv import load_dotenv
from pathlib import Path
from utils import BaseProvider


class GruppoComet(BaseProvider):

    def __init__(self):
        super().__init__(
            provider_name = "gruppocomet",
            provider_url = "https://gruppocomet.it/simevignuda",
            login_required = True,
            result_container = [".result-block-v2"],
            popup_selectors = [
                "button.iubenda-cs-close-btn",
                "a#eu-privacy-close"
            ],
            logout_selectors = ["a"],
            title_classes = [".result-title"], 
            availability_classes = {
                "available": [".disp-ok"], 
                "not_available": [".disp-no"]
            },
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

            username = os.getenv("GRUPPOCOMET_USERNAME")
            password = os.getenv("GRUPPOCOMET_PASSWORD")

            if not username:
                username = input("Inserisci lo username per Gruppo Comet: ")
            if not password:
                password = getpass("Inserisci la password per Gruppo Comet: ")

            env_path.touch(600, exist_ok=True)

            with open(env_path, "r+") as f:
                lines = f.read().splitlines()
                keys = {line.split("=", 1)[0] for line in lines if "=" in line}

                if "GRUPPOCOMET_USERNAME" not in keys:
                    f.write(f"GRUPPOCOMET_USERNAME={username}\n")
                if "GRUPPOCOMET_PASSWORD" not in keys:
                    f.write(f"GRUPPOCOMET_PASSWORD={password}\n")

            await page.locator("input[name='username']").fill(username)
            await page.locator("input[name='password']").fill(password)
            await page.keyboard.press("Enter")

            return True
        except:
            return False
        

class Comet(BaseProvider):

    def __init__(self):
        super().__init__(
            provider_name = "comet",
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