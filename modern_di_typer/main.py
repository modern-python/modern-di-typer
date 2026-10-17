import collections.abc
import contextlib
import functools
import inspect
import typing

import typer
from modern_di import Container, Scope, integrations


T = typing.TypeVar("T")

_COMMAND_CONTAINER_KEY: typing.Final = "modern_di_typer.command_container"
_CONTEXT_PARAM_NAME: typing.Final = "_modern_di_typer_ctx"
_MISSING: typing.Final = object()


FromDI = integrations.from_di


class _ContextSettings(dict[str, typing.Any]):
    app_container: Container


def setup_di(app: typer.Typer, container: Container) -> Container:
    settings = _ContextSettings(app.info.context_settings or {})
    if settings.get("obj") is None:
        settings["obj"] = {}
    settings.app_container = container
    app.info.context_settings = settings
    return container


def fetch_di_container(ctx: typer.Context) -> Container:
    settings = ctx.find_root().command.context_settings
    if isinstance(settings, _ContextSettings):
        return settings.app_container
    msg = (
        "No modern-di container found on the app. "
        "Call setup_di(app, container) before using @inject or fetch_di_container."
    )
    raise RuntimeError(msg)


@contextlib.contextmanager
def _build_command_container(ctx: typer.Context) -> collections.abc.Generator[Container]:
    with fetch_di_container(ctx).build_child_container(scope=Scope.REQUEST) as container:
        yield container


@contextlib.contextmanager
def action_scope(ctx: typer.Context) -> collections.abc.Generator[Container]:
    try:
        request_container: Container = ctx.meta[_COMMAND_CONTAINER_KEY]
    except KeyError:
        msg = (
            "No modern-di command container found for this command. "
            "Decorate the command with @inject so action_scope has a per-command container to nest under."
        )
        raise RuntimeError(msg) from None
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
        ctx_param_name = _CONTEXT_PARAM_NAME
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
            previous = ctx.meta.get(_COMMAND_CONTAINER_KEY, _MISSING)
            ctx.meta[_COMMAND_CONTAINER_KEY] = cmd_container
            try:
                if di_params:
                    arguments.update(integrations.resolve_markers(cmd_container, di_params))
                return func(**arguments)
            finally:
                # ctx.meta is shared with subcommands, which must not see this container once it closes.
                if previous is _MISSING:
                    del ctx.meta[_COMMAND_CONTAINER_KEY]
                else:
                    ctx.meta[_COMMAND_CONTAINER_KEY] = previous

    wrapper.__signature__ = new_sig  # ty: ignore[unresolved-attribute]
    return wrapper
