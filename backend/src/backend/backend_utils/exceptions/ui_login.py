
from shared.provider.base_provider import BaseProvider


class UILoginException(Exception):
    """"""


    def __init__(
            self,
            provider: BaseProvider,
            message: str | None = None
        ):
        self.provider = provider

        default_message = (
            f"Auto-login failed while logging into '{provider.name}'. "
            "Proceeding with manual login."
        )

        super().__init__(message or default_message)
