# modern-di-typer

[![PyPI version](https://img.shields.io/pypi/v/modern-di-typer.svg)](https://pypi.org/project/modern-di-typer/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/modern-di-typer.svg)](https://pypi.org/project/modern-di-typer/)
[![Downloads](https://img.shields.io/pypi/dm/modern-di-typer.svg)](https://pypistats.org/packages/modern-di-typer)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/modern-python/modern-di-typer/actions/workflows/ci.yml)
[![CI](https://github.com/modern-python/modern-di-typer/actions/workflows/ci.yml/badge.svg)](https://github.com/modern-python/modern-di-typer/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/modern-python/modern-di-typer.svg)](https://github.com/modern-python/modern-di-typer/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/modern-python/modern-di-typer)](https://github.com/modern-python/modern-di-typer/stargazers)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![ty](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ty/main/assets/badge/v0.json)](https://github.com/astral-sh/ty)

[Modern-DI](https://github.com/modern-python/modern-di) integration for [Typer](https://typer.tiangolo.com).

## Installation

```bash
uv add modern-di-typer      # or: pip install modern-di-typer
```

## Usage

```python
import typing
import typer
import modern_di
from modern_di import Scope, providers, Group
from modern_di_typer import FromDI, inject, setup_di


class Dependencies(Group):
    settings = providers.Factory(creator=lambda: {"debug": True})
    service = providers.Factory(scope=Scope.REQUEST, creator=MyService, bound_type=None)


app = typer.Typer()
container = modern_di.Container(groups=[Dependencies])
setup_di(app, container)


@app.command()
@inject
def my_command(
    name: typing.Annotated[str, typer.Argument()],
    service: typing.Annotated[MyService, FromDI(Dependencies.service)],
) -> None:
    service.run(name)


if __name__ == "__main__":
    with container:
        app()
```

## Action scope

To resolve `Scope.ACTION` dependencies, inject `modern_di.Container` (the REQUEST-scoped container created by `@inject`) and build a child:

```python
import modern_di
from modern_di import Scope, providers, Group
from modern_di_typer import FromDI, inject


class Dependencies(Group):
    job = providers.Factory(scope=Scope.ACTION, creator=MyJob, bound_type=None)


@app.command()
@inject
def my_command(
    container: typing.Annotated[modern_di.Container, FromDI(modern_di.Container)],
) -> None:
    with container.build_child_container() as action_container:
        job = action_container.resolve_provider(Dependencies.job)
        job.run()
```

## API

- `setup_di(app, container)` — register the container with a Typer app
- `inject` — decorator that resolves `FromDI`-annotated parameters before the command runs; also exposes `typer.Context` with `ctx.obj["di_container"]` for manual use
- `FromDI(provider)` — marker used in `Annotated[T, FromDI(...)]`; accepts a provider instance or a type
- `fetch_di_container(ctx)` — returns the app-scoped container from `ctx.obj`

## 📦 [PyPI](https://pypi.org/project/modern-di-typer)

## 📝 [License](LICENSE)

## Part of `modern-python`

Browse the full list of templates and libraries in
[`modern-python`](https://github.com/modern-python) — see the org profile for the categorized index.
