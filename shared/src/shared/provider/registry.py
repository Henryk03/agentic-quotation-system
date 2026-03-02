
import importlib
import pkgutil
import re
import types

from shared.exceptions import ProviderNotSupportedException
from shared.provider import providers as providers_pkg
from shared.provider.base_provider import BaseProvider


PROVIDER_REGISTRY: dict[str, BaseProvider] = {}


def register_provider(
        provider_instance: BaseProvider
    ) -> None:
    """
    Register a provider instance in the global registry.

    Parameters
    ----------
    provider_instance : BaseProvider
        An instance of a provider to register.

    Raises
    ------
    RuntimeError
        If a provider with the same name is already registered.
    """

    name: str = provider_instance.name

    if name in PROVIDER_REGISTRY:
        raise RuntimeError(
            f"Duplicate provider name detected: {name}"
        )
    
    PROVIDER_REGISTRY[name] = provider_instance


def autodiscover_providers() -> None:
    """
    Automatically discover and register all provider instances 
    defined in the `shared.provider.providers` package.

    Notes
    -----
    Each provider module must expose a variable named `provider` 
    containing an instance of `BaseProvider`.
    """

    for module_info in pkgutil.iter_modules(providers_pkg.__path__):
        module_name: str = f"{providers_pkg.__name__}.{module_info.name}"
        module: types.ModuleType = importlib.import_module(module_name)

        provider: BaseProvider | None = getattr(module, "provider", None)

        if isinstance(provider, BaseProvider):
            register_provider(provider)


# providers' registration at import time
autodiscover_providers()


def all_providers() -> list[BaseProvider]:
    """
    Return a list of all registered provider instances.

    Returns
    -------
    list[BaseProvider]
        All provider instances in the registry.
    """

    return list(PROVIDER_REGISTRY.values())


def all_provider_names() -> list[str]:
    """
    Return the names of all registered providers.

    Returns
    -------
    list[str]
        Provider names as registered in the registry.
    """

    return list(PROVIDER_REGISTRY.keys())


def get_provider_registry() -> dict[str, BaseProvider]:
    """
    Return the complete provider registry.

    Returns
    -------
    dict[str, BaseProvider]
        A dictionary mapping provider names to provider instances.
    """

    return PROVIDER_REGISTRY


def support_autologin(provider: str) -> bool:
    """
    Check whether a provider supports automatic login.

    Parameters
    ----------
    provider : str
        Name of the provider.

    Returns
    -------
    bool
        `True` if the provider defines a custom `auto_login` method, 
        `False` otherwise.
    """

    if provider in PROVIDER_REGISTRY:
        instance: BaseProvider = PROVIDER_REGISTRY[provider]

        return instance.has_auto_login()
    
    return False


def get_provider(provider_name: str) -> BaseProvider:
    """
    Retrieve a provider instance from the registry by name.

    The lookup is case-insensitive and allows optional spaces 
    between words derived from camel case names.

    Parameters
    ----------
    provider_name : str
        Name of the provider to retrieve.

    Returns
    -------
    BaseProvider
        The provider instance matching the given name.

    Raises
    ------
    ProviderNotSupportedException
        If the provider name does not match any registered provider.
    """

    normalized_input: str = provider_name.strip().lower()

    for registry_key, provider_instance in PROVIDER_REGISTRY.items():
        pattern = re.sub(r'([a-z])([A-Z])', r'\1\\s*\2', registry_key)
        
        if re.fullmatch(pattern, normalized_input, re.IGNORECASE):
            return provider_instance
    
    raise ProviderNotSupportedException(provider_name)