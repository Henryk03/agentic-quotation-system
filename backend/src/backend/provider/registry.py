
from backend.provider.base_provider import BaseProvider
from backend.provider.providers import comet, gruppo_comet


PROVIDER_REGISTRY: dict[str, BaseProvider] = {}


def register_provider(provider_cls: BaseProvider) -> None:
    """"""

    name = provider_cls.name.upper()
    PROVIDER_REGISTRY[name] = provider_cls


# =========================
#  providers' registration 
# =========================
register_provider(comet.Comet)
register_provider(gruppo_comet.GruppoComet)


def all_providers_string() -> str:
    """"""

    return ", ".join(list(PROVIDER_REGISTRY.keys()))


def all_providers() -> list[BaseProvider]:
    """"""

    return list(PROVIDER_REGISTRY.values())