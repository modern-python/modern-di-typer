import typing

import typer
from typer.testing import CliRunner

import modern_di_typer
from modern_di_typer import FromDI, build_command_container, inject
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
    def cmd(ctx: typer.Context) -> None:
        with build_command_container(ctx) as cmd_container:
            action_container = cmd_container.build_child_container()
            instance = action_container.resolve_provider(Dependencies.action_factory)
            assert isinstance(instance, DependentCreator)

    result = runner.invoke(app)
    assert result.exit_code == 0


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
