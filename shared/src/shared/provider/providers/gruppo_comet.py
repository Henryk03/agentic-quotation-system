
import re

from playwright.async_api import Page

from shared.provider.base_provider import BaseProvider


class GruppoComet(BaseProvider):

    def __init__(self):
        super().__init__(
            availability_classes = {
                "available": [".disp-ok"], 
                "not_available": [".disp-no"]
            },
            availability_pattern = None,
            login_required = True,
            logout_selectors = [
                "a"
            ],
            logout_texts = re.compile(
                r"(?:log|sign)[- ]?out",
                re.IGNORECASE
            ),
            popup_selectors = [
                "button.iubenda-cs-close-btn",
                "a#eu-privacy-close"
            ],
            price_classes = [
                ".result-price"
            ],
            provider_name = "GruppoComet",
            provider_url = "https://gruppocomet.it/simevignuda",
            result_container = [
                ".result-block-v2"
            ],
            search_texts = re.compile(
                "cerca per attributo", 
                re.IGNORECASE
            ),
            title_classes = [
                ".result-title"
            ] 
        )

    async def auto_login(
            self, 
            page: Page,
            credentials: dict[str, str]
        ) -> bool:

        login_texts: re.Pattern[str] = re.compile(
            "accedi",
            re.IGNORECASE
        )

        try:
            await page.get_by_role("link", name=login_texts).click()

            username: str = credentials["username"]
            password: str = credentials["password"]

            await page.locator("input[name='username']").fill(username)
            await page.locator("input[name='password']").fill(password)
            await page.keyboard.press("Enter")

            await page.wait_for_load_state("networkidle")

            return await self.is_logged_in(page)

        except:
            return False
        
provider: BaseProvider = GruppoComet()