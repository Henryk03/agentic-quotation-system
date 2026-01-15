
# import re
# from dotenv import dotenv_values

from shared.provider.base_provider import BaseProvider


class GruppoComet(BaseProvider):

    def __init__(self):
        super().__init__(
            provider_name = "GruppoComet",
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

    # async def auto_login(self, page):

    #     login_texts = re.compile(
    #         "accedi",
    #         re.IGNORECASE
    #     )

    #     try:
    #         await page.get_by_role("link", name=login_texts).click()

    #         credentials = dotenv_values("/run/secrets/autologin-env")

    #         username = credentials["GRUPPOCOMET_USERNAME"]
    #         password = credentials["GRUPPOCOMET_PASSWORD"]

    #         await page.locator("input[name='username']").fill(username)
    #         await page.locator("input[name='password']").fill(password)
    #         await page.keyboard.press("Enter")

    #         return True
    #     except:
    #         return False