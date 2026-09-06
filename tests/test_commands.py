import typing

import modern_di
import typer
from typer.testing import CliRunner

import modern_di_typer
from modern_di_typer import FromDI, action_scope, inject
from tests.dependencies import Dependencies, DependentCreator, SimpleCreator


def test_app_scoped_factory(app: typer.Typer) -> None:
    runner = CliRunner()

    @app.command()
    @inject
    def cmd(instance: typing.Annotated[SimpleCreator, FromDI(SimpleCreator)]) -> None:
        assert isinstance(instance, SimpleCreator)
        assert instance.dep1 == "original"

    result = runner.invoke(app)
    assert result.exit_code == 0


def test_request_scoped_factory(app: typer.Typer) -> None:
    runner = CliRunner()
    instances: list[DependentCreator] = []

    @app.command()
    @inject
    def cmd(
        app_instance: typing.Annotated[SimpleCreator, FromDI(SimpleCreator)],
        request_instance: typing.Annotated[DependentCreator, FromDI(Dependencies.request_factory)],
    ) -> None:
        assert isinstance(app_instance, SimpleCreator)
        assert isinstance(request_instance, DependentCreator)
        assert request_instance.dep1 is not app_instance
        instances.append(request_instance)

    runner.invoke(app)
    runner.invoke(app)
    assert len(instances) == 2  # noqa: PLR2004
    assert instances[0] is not instances[1]


def test_action_scope(app: typer.Typer) -> None:
    runner = CliRunner()

    @app.command()
    @inject
    def cmd(container: typing.Annotated[modern_di.Container, FromDI(modern_di.Container)]) -> None:
        with container.build_child_container() as action_container:
            instance = action_container.resolve_provider(Dependencies.action_factory)
            assert isinstance(instance, DependentCreator)

    result = runner.invoke(app)
    assert result.exit_code == 0


def test_action_scope_resolves_action_provider(app: typer.Typer) -> None:
    runner = CliRunner()

    @app.command()
    @inject
    def cmd(ctx: typer.Context) -> None:
        with action_scope(ctx) as action:
            instance = action.resolve_provider(Dependencies.action_factory)
            assert isinstance(instance, DependentCreator)

    result = runner.invoke(app)
    assert result.exit_code == 0, result.output


def test_action_scope_yields_distinct_instances_per_iteration(app: typer.Typer) -> None:
    runner = CliRunner()
    instances: list[DependentCreator] = []

    @app.command()
    @inject
    def cmd(ctx: typer.Context) -> None:
        for _ in range(2):
            with action_scope(ctx) as action:
                instances.append(action.resolve_provider(Dependencies.action_factory))

    result = runner.invoke(app)
    assert result.exit_code == 0, result.output
    assert len(instances) == 2  # noqa: PLR2004
    assert instances[0] is not instances[1]


def test_action_scope_shares_request_singleton(app: typer.Typer) -> None:
    runner = CliRunner()
    captured: dict[str, typing.Any] = {}

    @app.command()
    @inject
    def cmd(
        ctx: typer.Context,
        request_instance: typing.Annotated[DependentCreator, FromDI(Dependencies.cached_request_factory)],
    ) -> None:
        with action_scope(ctx) as action:
            captured["from_action"] = action.resolve_provider(Dependencies.cached_request_factory)
        captured["injected"] = request_instance

    result = runner.invoke(app)
    assert result.exit_code == 0, result.output
    assert captured["from_action"] is captured["injected"]


def test_each_action_scope_block_opens_its_own_container(app: typer.Typer) -> None:
    """INVARIANT: every ``action_scope`` block opens its own container, so one command can open many.

    Broken by hoisting the action container up to one per command — the shape auto-injection would
    have forced, and the reason it was rejected (``docs/adr/0001-action-scope-stays-caller-driven.md``).
    ``Scope.ACTION`` sits below ``Scope.REQUEST`` for exactly one purpose: several action lifetimes
    inside a single command, one per item of a batch. Collapse it to one and the scope is
    indistinguishable from REQUEST while still costing a container.

    Both assertions are load-bearing. The container check catches a block that re-yields an
    already-built container; the instance check catches one that yields a distinct container which
    is nonetheless not a fresh lifetime. The provider is *cached* on purpose — an uncached one
    hands back a new instance per resolve, so it would prove nothing about which container produced
    it and the second assertion would hold under every violation.
    """
    runner = CliRunner()
    containers: list[modern_di.Container] = []
    instances: list[DependentCreator] = []

    @app.command()
    @inject
    def cmd(ctx: typer.Context) -> None:
        for _ in range(2):
            with action_scope(ctx) as action:
                containers.append(action)
                instances.append(action.resolve_provider(Dependencies.cached_action_factory))

    result = runner.invoke(app)
    assert result.exit_code == 0, result.output
    assert containers[0] is not containers[1]
    assert instances[0] is not instances[1]


def test_command_container_never_enters_shared_app_state(app: typer.Typer) -> None:
    """INVARIANT: the command container is stashed on per-invocation state, never on ``ctx.obj``.

    Broken by parking the command container — or anything else per-invocation — in the object Typer
    builds from ``context_settings``. That object is a single dict shared by every invocation of the
    same app, so a container left there outlives the command that opened it: a later invocation can
    reach a closed container, and a long-lived app accumulates one per command run. ``ctx.meta`` is
    rebuilt per invocation and discarded with the context, which is what makes the command
    container's lifetime equal to the command's.
    """
    runner = CliRunner()
    obj_keys: list[set[str]] = []

    @app.command()
    @inject
    def cmd(ctx: typer.Context) -> None:
        with action_scope(ctx) as action:
            action.resolve_provider(Dependencies.action_factory)
        obj_keys.append(set(ctx.obj))

    result = runner.invoke(app)
    assert result.exit_code == 0, result.output
    assert obj_keys == [{"di_container"}]
    context_settings = app.info.context_settings
    assert context_settings is not None
    assert set(context_settings["obj"]) == {"di_container"}


def test_fetch_di_container(app: typer.Typer) -> None:
    runner = CliRunner()

    @app.command()
    @inject
    def cmd(ctx: typer.Context) -> None:
        container = modern_di_typer.fetch_di_container(ctx)
        instance = container.resolve(SimpleCreator)
        assert isinstance(instance, SimpleCreator)

    result = runner.invoke(app)
    assert result.exit_code == 0


def test_command_with_positional_argument(app: typer.Typer) -> None:
    runner = CliRunner()
    received: dict[str, typing.Any] = {}

    @app.command()
    @inject
    def cmd(name: str, instance: typing.Annotated[SimpleCreator, FromDI(SimpleCreator)]) -> None:
        received["name"] = name
        received["instance"] = instance

    result = runner.invoke(app, ["alice"])
    assert result.exit_code == 0, result.output
    assert received["name"] == "alice"
    assert isinstance(received["instance"], SimpleCreator)


def test_command_with_option(app: typer.Typer) -> None:
    runner = CliRunner()
    received: dict[str, typing.Any] = {}

    @app.command()
    @inject
    def cmd(
        instance: typing.Annotated[SimpleCreator, FromDI(SimpleCreator)],
        count: int = typer.Option(1, "--count"),
    ) -> None:
        received["count"] = count
        received["instance"] = instance

    result = runner.invoke(app, ["--count", "5"])
    assert result.exit_code == 0, result.output
    assert received["count"] == 5  # noqa: PLR2004
    assert isinstance(received["instance"], SimpleCreator)


def test_command_with_option_default(app: typer.Typer) -> None:
    runner = CliRunner()
    received: dict[str, typing.Any] = {}

    @app.command()
    @inject
    def cmd(
        instance: typing.Annotated[SimpleCreator, FromDI(SimpleCreator)],
        count: int = typer.Option(7, "--count"),
    ) -> None:
        received["count"] = count
        received["instance"] = instance

    result = runner.invoke(app)
    assert result.exit_code == 0, result.output
    assert received["count"] == 7  # noqa: PLR2004
    assert isinstance(received["instance"], SimpleCreator)


def test_command_with_arg_option_and_explicit_context(app: typer.Typer) -> None:
    runner = CliRunner()
    received: dict[str, typing.Any] = {}

    @app.command()
    @inject
    def cmd(
        ctx: typer.Context,
        name: str,
        instance: typing.Annotated[SimpleCreator, FromDI(SimpleCreator)],
        verbose: bool = typer.Option(False, "--verbose"),
    ) -> None:
        received["ctx"] = ctx
        received["name"] = name
        received["verbose"] = verbose
        received["instance"] = instance

    result = runner.invoke(app, ["bob", "--verbose"])
    assert result.exit_code == 0, result.output
    assert received["name"] == "bob"
    assert received["verbose"] is True
    assert isinstance(received["ctx"], typer._click.Context)  # noqa: SLF001
    assert isinstance(received["instance"], SimpleCreator)
