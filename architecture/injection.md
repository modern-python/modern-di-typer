# Injection

`@inject` lets a Typer command declare its dependencies as type annotations and
have them resolved before the command body runs. The whole mechanism lives in
`modern_di_typer/main.py`.

## The `FromDI` marker

`FromDI(provider)` marks a parameter for injection inside an `Annotated` hint:

```python
service: typing.Annotated[MyService, FromDI(Dependencies.service)]
```

`FromDI` is `modern_di.integrations.from_di` — its marker factory. Type
checkers see it as returning the resolved type `T`, while at runtime it
returns a frozen `Marker` instance that `inject` detects. The argument is
either a provider instance (`AbstractProvider`) or a bare type — resolution
handles both.

## `@inject` — decoration time

`inject(func)` runs once, when the command is defined:

1. `_parse_inject_params` delegates to `modern_di.integrations.parse_markers(func)`
   to find parameters whose `Annotated` metadata contains a `Marker`, and
   separately scans `typing.get_type_hints(func, include_extras=True)` itself
   for any existing `typer.Context` parameter — a typer-specific concern the
   kit has no equivalent for.
2. It rewrites `func.__signature__` to **remove** the `FromDI` parameters (so
   Typer never prompts for them on the CLI) and **inserts** a `typer.Context`
   parameter at position 0 if the command didn't already declare one.

## `@inject` — call time

The wrapper runs on every invocation:

1. Bind the incoming args against the rewritten signature; pull out the
   `typer.Context` (deleting it again if `inject` added it implicitly).
2. Build the per-command `Scope.REQUEST` container and stash it on `ctx.meta`
   (see [scopes.md](scopes.md)).
3. If there are `FromDI` parameters, `modern_di.integrations.resolve_markers(cmd_container, di_params)`
   resolves each from the command container — under the hood, each
   `Marker.resolve(container)` calls `container.resolve_dependency(...)`,
   modern-di's single provider-or-type dispatch — and fills them into the
   call.
4. Call the original function; close the command container on return.

`FromDI` parameters coexist with ordinary Typer arguments and options: because
`inject` strips only the `FromDI` parameters from the signature, Typer still sees
(and parses) the rest.
