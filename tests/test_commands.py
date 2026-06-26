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
