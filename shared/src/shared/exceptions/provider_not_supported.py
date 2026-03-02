

class ProviderNotSupportedException(Exception):
    """
    Exception raised when an unsupported provider is used.

    Parameters
    ----------
    provider : str
        The name of the provider that is not supported.

    Attributes
    ----------
    provider : str
        Stores the name of the unsupported provider.

    Notes
    -----
    This exception is typically raised when attempting to 
    use a provider that has not been registered or implemented 
    in the system.
    """


    def __init__(
            self,
            provider: str
        ):

        self.provider = provider

        super().__init__(
            f"The provider {provider} is not supported"
        )