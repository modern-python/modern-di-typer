# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Run `just --list` (or read the `Justfile`) for all recipes. Which to use when:

- `just test` — plain pytest, no coverage gate. Passes args through, e.g.
  `just test tests/test_commands.py::test_app_scoped_factory`.
- `just test-ci` / `just test-branch` — the 100%-coverage-gated runs (CI uses
  `test-ci`; `test-branch` adds branch coverage).
- `just lint` auto-fixes; `just lint-ci` is the non-fixing CI check.

## Architecture

This is a small library (~120 lines) that integrates [Modern-DI](https://github.com/modern-python/modern-di) with [Typer](https://github.com/fastapi/typer). The entire implementation lives in `modern_di_typer/main.py`.

### How `inject` works

The `inject` decorator works at decoration time, not call time:

1. **Decoration time** (`inject(func)`): Inspects type hints via `typing.get_type_hints` to find parameters annotated with `Annotated[T, _FromDI(...)]`. Rewrites `func.__signature__` to remove DI params (so Typer doesn't prompt for them) and injects a `typer.Context` parameter if one isn't already present.

2. **Call time** (`wrapper(...)`): Reads the app-scoped container via `fetch_di_container(ctx)` (which reads `ctx.obj["di_container"]`, where `setup_di` stashed it), always builds a `Scope.REQUEST` child container, stashes it on `ctx.meta` (under `_COMMAND_CONTAINER_KEY`) so `action_scope` can parent ACTION children onto it, resolves DI params (if any), and calls the original function with all params filled in.

### Scope model

- `setup_di(app, container)` — registers an **app-scoped** container by stashing it in `app.info.context_settings["obj"]["di_container"]`, which Typer/Click promotes to `ctx.obj` at runtime
- `@inject` — creates a **REQUEST-scoped** child container per command invocation (closed after the command returns)
- `_build_command_container(ctx)` — private context manager (not exported) that `inject` uses to build the REQUEST-scoped child
- `action_scope(ctx)` — public context manager yielding an **ACTION-scoped** child of the command's REQUEST container (read from `ctx.meta`); each `with` block is a fresh action scope, so a command can open many within one invocation (see README "Action scope"). Injecting `modern_di.Container` + calling `build_child_container()` manually still works but `action_scope` is preferred

### `FromDI` type trick

`FromDI` is a factory function that returns `typing.cast(T_co, _FromDI(provider))`. This makes type checkers treat it as returning the resolved type `T_co` while at runtime it returns a `_FromDI` dataclass instance that `inject` can detect.

### Test pattern

Tests define commands inline inside test functions and invoke them with `typer.testing.CliRunner`. The `app` fixture (in `conftest.py`) creates a fresh Typer app + container for each test.
