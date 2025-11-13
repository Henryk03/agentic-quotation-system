
from utils import BaseProvider


class LoginFailedException(Exception):
    """
    Exception raised when the log-in operation fails.
    """

    def __init__(self, provider: BaseProvider):
        self.provider = provider
        super().__init__(
            (
                f"Log-in failed while logging-in into {provider.name} "
                " website.\nPlease, try again."
            )
        )
