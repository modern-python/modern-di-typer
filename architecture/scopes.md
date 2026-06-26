# Scopes

`modern-di-typer` maps `modern_di`'s scope hierarchy
(`APP → SESSION → REQUEST → ACTION → STEP`, deeper = higher integer; see
[modern-di's `architecture/scopes.md`](https://github.com/modern-python/modern-di/blob/main/architecture/scopes.md))
onto a Typer CLI's lifecycle. Three containers matter at the CLI boundary.

## App container

The application-lifetime container, registered once via `setup_di(app, container)`.
It is the root the whole process resolves `Scope.APP` providers from.

`setup_di` stashes it in `app.info.context_settings["obj"]["di_container"]`,
which Typer/Click promotes to `ctx.obj` when a command runs. Retrieve it with
`fetch_di_container(ctx)` (reads `ctx.obj["di_container"]`).

```python
app = typer.Typer()
container = modern_di.Container(groups=[Dependencies])
setup_di(app, container)        # registers the app container

if __name__ == "__main__":
    with container:             # opens/closes the app container
        app()
```

## Command container

The per-invocation `Scope.REQUEST` container. `@inject` **always** builds one
per command run — even when the command declares no `FromDI` parameters — and
closes it when the command returns. Injected `FromDI` parameters are resolved
from it, so `Scope.REQUEST` providers live for exactly one command invocation.

The command container is stashed on `ctx.meta` (under the
`_COMMAND_CONTAINER_KEY` constant) so `action_scope` can parent action
containers onto it. `ctx.meta` is per-invocation and isolated — unlike `ctx.obj`,
which is shared app-level state — so nothing leaks between invocations.

## Action scope

`Scope.ACTION` is deeper than the command's `Scope.REQUEST`. `action_scope(ctx)`
is a context manager that yields a fresh `Scope.ACTION` container — a **child of
the command container** — and closes it on exit.

Because it is a child of the command container, a `Scope.REQUEST` provider
resolved inside an action scope is the *same* instance as the one injected into
the command (they share the command container via `find_container`). And because
each `with` block builds a fresh action container, a single command can open
**many** action scopes — one per unit of work:

```python
@app.command()
@inject
def my_command(ctx: typer.Context) -> None:
    for job_name in job_names:
        with action_scope(ctx) as action:          # one ACTION container per job
            action.resolve_provider(Dependencies.job).run()
```

The manual alternative — injecting `modern_di.Container` via `FromDI` and calling
`build_child_container()` by hand — still works, but `action_scope` is the
preferred interface: it keeps `modern_di`'s child-building out of the call site.

See [decisions/2026-06-25-action-scope-multiple-actions-per-command.md](../planning/decisions/2026-06-25-action-scope-multiple-actions-per-command.md)
for why action scope stays caller-driven rather than auto-injected.
