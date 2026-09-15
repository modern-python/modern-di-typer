# Action scope stays caller-driven, multiple per command

`Scope.ACTION` dependencies are reached through a caller-driven context manager, `action_scope(ctx)`,
not by auto-resolving ACTION-scoped `FromDI` parameters into the command signature.

Deepening ACTION scope behind `@inject` had two shapes on the table. Auto-injection would have
`@inject` build one ACTION container per command and inject resolved ACTION parameters alongside
the REQUEST ones, symmetric with what already happens. Caller-driven gives the command a named
context manager that opens an ACTION container on demand.

`Scope.ACTION` is finer than `Scope.REQUEST`, and its whole purpose is to allow several
action-scoped lifetimes within one command, one action per item of a batch. Auto-injection builds a
single ACTION container per command, so the injected value is one fixed instance for the whole
command: it removes the multiplicity that is the only reason ACTION sits below REQUEST.

Caller-driven achieves the same deepening goal, `build_child_container()` stops appearing at every
call site, without changing what ACTION means. Each `with action_scope(ctx)` block is a fresh
container.

Three sub-decisions were taken with it. The manager is ctx-based, promoting the existing private
command-container concept rather than introducing a new injection marker for an opener. It yields
the raw `Container`: `resolve_provider` and `resolve` are `modern-di`'s normal interface and not a
leak worth hiding, only `build_child_container` was. And the command container is stashed on
`ctx.meta`, which is per-invocation and isolated, rather than `ctx.obj`, which is shared app state.

Revisit when a concrete use case appears where "one action = one command" is the natural model and
the loop case is absent. Auto-injection then becomes worth reconsidering as an additive option.
