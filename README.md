<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)"  srcset="https://raw.githubusercontent.com/modern-python/.github/main/brand/projects/modern-di-typer/lockup-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/modern-python/.github/main/brand/projects/modern-di-typer/lockup-light.svg">
    <img alt="modern-di-typer" src="https://raw.githubusercontent.com/modern-python/.github/main/brand/projects/modern-di-typer/lockup.png" width="420">
  </picture>
</p>

[![PyPI version](https://img.shields.io/pypi/v/modern-di-typer.svg)](https://pypi.org/project/modern-di-typer/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/modern-di-typer.svg)](https://pypi.org/project/modern-di-typer/)
[![Downloads](https://static.pepy.tech/badge/modern-di-typer/month)](https://pepy.tech/projects/modern-di-typer)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/modern-python/modern-di-typer/actions/workflows/ci.yml)
[![CI](https://github.com/modern-python/modern-di-typer/actions/workflows/ci.yml/badge.svg)](https://github.com/modern-python/modern-di-typer/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/modern-python/modern-di-typer.svg)](https://github.com/modern-python/modern-di-typer/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/modern-python/modern-di-typer)](https://github.com/modern-python/modern-di-typer/stargazers)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![ty](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ty/main/assets/badge/v0.json)](https://github.com/astral-sh/ty)

[Modern-DI](https://github.com/modern-python/modern-di) integration for [Typer](https://typer.tiangolo.com).

Full guide: [Typer integration docs](https://modern-di.modern-python.org/integrations/typer/)

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
container = modern_di.Container(groups=[Dependencies], validate=True)
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

`Scope.ACTION` dependencies live below the per-command `Scope.REQUEST` container.
Open one with `action_scope(ctx)`: each `with` block yields a fresh action-scoped
container (a child of the command's request container), so you can open as many as
you need within a single command — one per item in a batch, for example.

```python
import typer
from modern_di import Scope, providers, Group
from modern_di_typer import FromDI, action_scope, inject


class Dependencies(Group):
    job = providers.Factory(scope=Scope.ACTION, creator=MyJob, bound_type=None)


@app.command()
@inject
def my_command(ctx: typer.Context) -> None:
    for job_name in job_names:
        with action_scope(ctx) as action:
            action.resolve_provider(Dependencies.job).run()
```

## API

- `setup_di(app, container)` — register the container with a Typer app
- `inject` — decorator that resolves `FromDI`-annotated parameters before the command runs; also exposes `typer.Context` with `ctx.obj["di_container"]` for manual use
- `FromDI(provider)` — marker used in `Annotated[T, FromDI(...)]`; accepts a provider instance or a type
- `action_scope(ctx)` — context manager yielding a fresh `Scope.ACTION` container (a child of the command's request container); open one per action
- `fetch_di_container(ctx)` — returns the app-scoped container from `ctx.obj`

## Used by

- **[semvertag](https://github.com/modern-python/semvertag)** — a CLI
  auto-tagger for GitLab/GitHub that wires its settings, API providers, and
  version-bump strategies through a `modern_di` container with
  `modern-di-typer`. See
  [`semvertag/ioc.py`](https://github.com/modern-python/semvertag/blob/main/semvertag/ioc.py)
  for a real-world `setup_di` + `Group` setup.

## 📦 [PyPI](https://pypi.org/project/modern-di-typer)

## 📝 [License](LICENSE)

## Part of `modern-python`

Built on [`modern-di`](https://github.com/modern-python/modern-di), a dependency-injection framework with IoC container and scopes.

Browse the full list of templates and libraries in
[`modern-python`](https://github.com/modern-python) — see the org profile for the categorized index.
