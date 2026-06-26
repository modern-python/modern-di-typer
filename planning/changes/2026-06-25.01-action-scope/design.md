---
summary: Added `action_scope(ctx)` so commands reach ACTION-scoped deps without injecting `Container` or calling `build_child_container()` by hand.
---

# Design: Deepen ACTION scope behind `action_scope(ctx)`

## Summary

Add a public `action_scope(ctx)` context manager that yields a fresh
`Scope.ACTION` container (a child of the per-command `Scope.REQUEST` container).
Commands stop reaching ACTION scope by injecting `modern_di.Container` and
calling `build_child_container()` at every call site; the scope-nesting moves
behind one named interface. Multiple action scopes per command are preserved.

## Motivation

From an architecture review: `Scope.REQUEST` was deep behind `@inject`, but
`Scope.ACTION` was shallow — every ACTION command had to inject
`modern_di.Container`, then `with container.build_child_container() as action:`,
then `action.resolve_provider(...)`. `modern_di`'s child-building leaked across
the seam at each call site. The library's own shape was inconsistent: one scope
deep, the adjacent one leaking.

## Non-goals

- Auto-injecting ACTION-scoped parameters (would collapse ACTION to one-per-command
  and remove the loop case). See the decision file.
- Exposing `scope=` / `context=` passthrough on `action_scope` — kept minimal.
- Touching the `setup_di` / `ctx.obj` container seam (separate, deferred item).

## Design

### 1. `action_scope(ctx)`

A `@contextlib.contextmanager` that reads the command container off
`ctx.meta[_COMMAND_CONTAINER_KEY]`, builds a child (the next-deeper scope —
`ACTION` by default), yields it, and closes it on exit.

### 2. `@inject` always builds + stashes the command container

The wrapper drops its `if not di_params: return func(...)` early-exit and always
builds the `Scope.REQUEST` container, stashing it on `ctx.meta` so `action_scope`
can parent onto it. Parenting onto the *same* command container is what makes a
`Scope.REQUEST` singleton shared between an injected parameter and one resolved
inside an action scope. `ctx.meta` (per-invocation, isolated) is used rather than
`ctx.obj` (shared app state).

## Testing

New pytest cases (inline-command pattern, `CliRunner`): ACTION provider resolves
through `action_scope`; two iterations yield distinct ACTION instances; a cached
`Scope.REQUEST` singleton is shared between an injected param and one resolved
inside `action_scope`; the no-DI-params path still works. The existing manual
`FromDI(Container)` test stays green (backward compatible). `just test-ci` — 100%.

## Risk

Low. The early-exit removal means every command now builds a `Scope.REQUEST`
container (negligible cost). `ctx.meta` isolation verified empirically before
implementation. Backward compatible: the manual ACTION pattern is unchanged.
