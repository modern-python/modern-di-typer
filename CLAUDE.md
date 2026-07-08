# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Run `just --list` (or read the `Justfile`) for all recipes. Which to use when:

- `just test` — plain pytest, no coverage gate. Passes args through, e.g.
  `just test tests/test_commands.py::test_app_scoped_factory`.
- `just test-ci` / `just test-branch` — the 100%-coverage-gated runs (CI uses
  `test-ci`; `test-branch` adds branch coverage).
- `just lint` auto-fixes; `just lint-ci` is the non-fixing CI check (also validates planning changes).
- `just check-planning` validates planning changes/decisions; `just index` prints the change listing.

## Architecture

> Quick orientation only. The authoritative, code-current account of each capability lives in [`architecture/`](architecture/) — one file per capability. **When a change alters a capability's behavior, update the matching `architecture/<capability>.md` in the same PR** — that promotion is what keeps `architecture/` true.

This is a small library (~120 lines) integrating [Modern-DI](https://github.com/modern-python/modern-di) with [Typer](https://github.com/fastapi/typer); the implementation lives in `modern_di_typer/main.py`.

- **Injection** — `@inject` rewrites a command's signature at decoration time (removing `FromDI` params, adding `typer.Context`) and resolves those params at call time. `FromDI(provider)` is the annotation marker.
- **Scopes** — `setup_di` registers the **app container**; `@inject` builds a per-command **`Scope.REQUEST` container** (stashed on `ctx.meta`); `action_scope(ctx)` yields an **`Scope.ACTION`** child of it, one fresh container per `with` block.

Where the detail lives — read the matching capability file before changing behavior:

| File | Covers |
|---|---|
| [architecture/scopes.md](architecture/scopes.md) | app container, per-command container, `action_scope`, `setup_di`/`fetch_di_container` |
| [architecture/injection.md](architecture/injection.md) | `@inject` decoration/call time, the `FromDI` marker |

### Test pattern

Tests define commands inline inside test functions and invoke them with `typer.testing.CliRunner`. The `app` fixture (in `conftest.py`) creates a fresh Typer app + container for each test.

## Workflow

Planning uses a portable two-axis convention — [`architecture/`](architecture/) (repo root) is the living **truth home** and promotion target; [`planning/changes/`](planning/changes/) holds the per-change files. **Start at the [Quick path](planning/README.md#quick-path-start-here)** in `planning/README.md` to choose a lane, create a change file, and ship. Run `just check-planning` to validate changes and `just index` to print the listing. Design decisions (and rejected alternatives) live in [`planning/decisions/`](planning/decisions/).
