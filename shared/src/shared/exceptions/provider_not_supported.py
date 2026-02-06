

class ProviderNotSupportedException(Exception):
    """"""


    def __init__(
            self,
            provider: str
        ):

        self.provider = provider

        super().__init__(f"The provider {provider} is not supported")