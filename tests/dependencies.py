import dataclasses

from modern_di import Group, Scope, providers


@dataclasses.dataclass(kw_only=True, slots=True)
class SimpleCreator:
    dep1: str


@dataclasses.dataclass(kw_only=True, slots=True)
class DependentCreator:
    dep1: SimpleCreator


class Dependencies(Group):
    app_factory = providers.Factory(creator=SimpleCreator, kwargs={"dep1": "original"})
    request_factory = providers.Factory(scope=Scope.REQUEST, creator=DependentCreator, bound_type=None)
    cached_request_factory = providers.Factory(
        scope=Scope.REQUEST,
        creator=DependentCreator,
        bound_type=None,
        cache_settings=providers.CacheSettings(),
    )
    action_factory = providers.Factory(scope=Scope.ACTION, creator=DependentCreator, bound_type=None)
