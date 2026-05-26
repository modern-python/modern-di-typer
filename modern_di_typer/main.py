import contextlib
import dataclasses
import functools
import inspect
import typing

import typer
from modern_di import Container, Scope, providers


T_co = typing.TypeVar("T_co", covariant=True)
T = typing.TypeVar("T")


@dataclasses.dataclass(slots=True, frozen=True)
class _FromDI(typing.Generic[T_co]):
    provider: providers.AbstractProvider[T_co] | type[T_co]


def FromDI(provider: providers.AbstractProvider[T_co] | type[T_co]) -> T_co:  # noqa: N802
    return typing.cast(T_co, _FromDI(provider))


def setup_di(app: typer.Typer, container: Container) -> Container:
    if not app.info.context_settings:
        app.info.context_settings = {}
    obj = app.info.context_settings.get("obj") or {}
    obj["di_container"] = container
    app.info.context_settings["obj"] = obj
    return container


def fetch_di_container(ctx: typer.Context) -> Container:
    return typing.cast(Container, ctx.obj["di_container"])


@contextlib.contextmanager
def _build_command_container(ctx: typer.Context) -> typing.Iterator[Container]:
    container = fetch_di_container(ctx).build_child_container(scope=Scope.REQUEST)
    try:
        yield container
    finally:
        container.close_sync()


def _parse_inject_params(
    func: typing.Callable[..., typing.Any],
) -> tuple[dict[str, _FromDI[typing.Any]], str | None]:
    hints = typing.get_type_hints(func, include_extras=True)
    di_params: dict[str, _FromDI[typing.Any]] = {}
    ctx_param_name: str | None = None

    for name, hint in hints.items():
        if name == "return":
            continue
        if hint is typer.Context:
            ctx_param_name = name
        elif typing.get_origin(hint) is typing.Annotated:
            for meta in typing.get_args(hint)[1:]:
                if isinstance(meta, _FromDI):
                    di_params[name] = meta
                    break

    return di_params, ctx_param_name


def _resolve_di_params(
    cmd_container: Container,
    di_params: dict[str, _FromDI[typing.Any]],
) -> dict[str, typing.Any]:
    return {
        name: (
            cmd_container.resolve_provider(marker.provider)
            if isinstance(marker.provider, providers.AbstractProvider)
            else cmd_container.resolve(dependency_type=marker.provider)
        )
        for name, marker in di_params.items()
    }


def inject(func: typing.Callable[..., T]) -> typing.Callable[..., T]:
    di_params, ctx_param_name = _parse_inject_params(func)

    sig = inspect.signature(func)
    new_params = [p for name, p in sig.parameters.items() if name not in di_params]

    added_ctx = ctx_param_name is None
    if added_ctx:
        ctx_param_name = "ctx"
        new_params.insert(
            0,
            inspect.Parameter(ctx_param_name, kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=typer.Context),
        )

    ctx_key: str = ctx_param_name
    new_sig = sig.replace(parameters=new_params)

    @functools.wraps(func)
    def wrapper(*args: typing.Any, **kwargs: typing.Any) -> T:  # noqa: ANN401
        bound = new_sig.bind(*args, **kwargs)
        bound.apply_defaults()
        arguments = dict(bound.arguments)

        ctx: typer.Context = arguments[ctx_key]
        if added_ctx:
            del arguments[ctx_key]

        if not di_params:
            return func(**arguments)

        with _build_command_container(ctx) as cmd_container:
            arguments.update(_resolve_di_params(cmd_container, di_params))
            return func(**arguments)

    wrapper.__signature__ = new_sig  # ty: ignore[unresolved-attribute]
    return wrapper
