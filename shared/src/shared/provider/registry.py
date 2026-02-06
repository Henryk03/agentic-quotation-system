
import re

from shared.exceptions import ProviderNotSupportedException
from shared.provider.base_provider import BaseProvider
from shared.provider.providers import comet, gruppo_comet


PROVIDER_REGISTRY: dict[str, BaseProvider] = {}


def register_provider(provider_instance: BaseProvider) -> None:
    """"""

    name: str = provider_instance.name
    PROVIDER_REGISTRY[name] = provider_instance


# =========================
#  providers' registration 
# =========================
register_provider(comet.Comet())
register_provider(gruppo_comet.GruppoComet())


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