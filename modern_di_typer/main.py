import contextlib
import functools
import inspect
import typing

import typer
from modern_di import Container, Scope, integrations


T = typing.TypeVar("T")

_COMMAND_CONTAINER_KEY: typing.Final = "modern_di_typer.command_container"


FromDI = integrations.from_di


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


@contextlib.contextmanager
def action_scope(ctx: typer.Context) -> typing.Iterator[Container]:
    request_container: Container = ctx.meta[_COMMAND_CONTAINER_KEY]
    with request_container.build_child_container() as action_container:
        yield action_container


def _parse_inject_params(
    func: typing.Callable[..., typing.Any],
) -> tuple[dict[str, integrations.Marker[typing.Any]], str | None]:
    hints = typing.get_type_hints(func, include_extras=True)
    ctx_param_name = next((name for name, hint in hints.items() if hint is typer.Context), None)
    return integrations.parse_markers(func), ctx_param_name


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

        with _build_command_container(ctx) as cmd_container:
            ctx.meta[_COMMAND_CONTAINER_KEY] = cmd_container
            if di_params:
                arguments.update(integrations.resolve_markers(cmd_container, di_params))
            return func(**arguments)

    wrapper.__signature__ = new_sig  # ty: ignore[unresolved-attribute]
    return wrapper
