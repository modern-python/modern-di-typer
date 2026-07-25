# Minimal modern-di + typer example.
# Run for real:  python -m examples.app world
import dataclasses
import typing

import typer
from modern_di import Container, Group, Scope, providers

from modern_di_typer import FromDI, inject, setup_di


@dataclasses.dataclass(kw_only=True)
class Settings:
    greeting: str = "Hello"


@dataclasses.dataclass(kw_only=True)
class GreetingService:
    settings: Settings  # auto-injected by type

    def greet(self, name: str) -> str:
        return f"{self.settings.greeting}, {name}!"


class Dependencies(Group):
    settings = providers.Factory(scope=Scope.APP, creator=Settings)
    service = providers.Factory(scope=Scope.REQUEST, creator=GreetingService)


app = typer.Typer()
container = Container(groups=[Dependencies], validate=True)
setup_di(app, container)


@app.command()
@inject
def greet(
    name: typing.Annotated[str, typer.Argument()],
    service: typing.Annotated[GreetingService, FromDI(Dependencies.service)],
) -> None:
    typer.echo(service.greet(name))


if __name__ == "__main__":  # pragma: no cover
    with container:
        app()
