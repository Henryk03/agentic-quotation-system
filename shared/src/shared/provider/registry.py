
import asyncio

from shared.provider.base_provider import BaseProvider
from shared.provider.providers import comet, gruppo_comet


PROVIDER_REGISTRY: dict[str, BaseProvider] = {}


def register_provider(provider_cls: BaseProvider) -> None:
    """"""

    istance = provider_cls()
    name = istance.name
    PROVIDER_REGISTRY[name] = provider_cls


# =========================
#  providers' registration 
# =========================
register_provider(comet.Comet)
register_provider(gruppo_comet.GruppoComet)


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
        instance: BaseProvider = PROVIDER_REGISTRY[provider]()

        return instance.has_auto_login()
    
    return False


def get_provider(provider_name: str) -> BaseProvider | None:
    """"""

    if provider_name in PROVIDER_REGISTRY:
        return PROVIDER_REGISTRY[provider_name]
    
    return None