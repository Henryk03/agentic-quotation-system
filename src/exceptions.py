
from utils import BaseProvider


class LoginFailedException(Exception):
    """
    Exception raised when the login operation fails.
    """

    def __init__(self, provider: BaseProvider):
        self.provider = provider
        super().__init__(
            (
                f"Login failed while logging-in into {provider.name} "
                " website.\nPlease, try again."
            )
        )
