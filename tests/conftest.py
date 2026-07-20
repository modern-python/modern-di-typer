import typing

import modern_di
import pytest
import typer

import modern_di_typer
from tests.dependencies import Dependencies


@pytest.fixture
def app() -> typing.Iterator[typer.Typer]:
    app_ = typer.Typer()
    with modern_di.Container(groups=[Dependencies], validate=True) as container:
        modern_di_typer.setup_di(app_, container=container)
        yield app_
