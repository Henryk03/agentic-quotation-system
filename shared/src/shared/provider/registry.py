
import re
import types
import pkgutil
import importlib

from shared.exceptions import ProviderNotSupportedException
from shared.provider.base_provider import BaseProvider
from shared.provider import providers as providers_pkg


PROVIDER_REGISTRY: dict[str, BaseProvider] = {}


def register_provider(provider_instance: BaseProvider) -> None:
    """"""

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
    """"""

    return list(PROVIDER_REGISTRY.values())


def all_provider_names() -> list[str]:
    """"""

    return list(PROVIDER_REGISTRY.keys())


def get_provider_registry() -> dict[str, BaseProvider]:
    """"""

    return PROVIDER_REGISTRY


def support_autologin(provider: str) -> bool:
    """"""

    if provider in PROVIDER_REGISTRY:
        instance: BaseProvider = PROVIDER_REGISTRY[provider]

        return instance.has_auto_login()
    
    return False


def get_provider(provider_name: str) -> BaseProvider:
    """"""

    normalized_input: str = provider_name.strip().lower()

    for registry_key, provider_instance in PROVIDER_REGISTRY.items():
        pattern = re.sub(r'([a-z])([A-Z])', r'\1\\s*\2', registry_key)
        
        if re.fullmatch(pattern, normalized_input, re.IGNORECASE):
            return provider_instance
    
    raise ProviderNotSupportedException(provider_name)