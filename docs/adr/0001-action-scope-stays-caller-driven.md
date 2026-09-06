# Action scope stays caller-driven, multiple per command

**Decision:** Reach `Scope.ACTION` dependencies through a caller-driven context manager
`action_scope(ctx)`, not by auto-resolving ACTION-scoped `FromDI` parameters into the command
signature.

Deepening ACTION scope behind `@inject` had two shapes on the table. **Auto-injection** would have
`@inject` build one ACTION container per command and inject resolved ACTION parameters alongside
the REQUEST ones — symmetric with what already happens, and simple. **Caller-driven** gives the
command a named context manager that opens an ACTION container on demand.

`Scope.ACTION` is *finer* than `Scope.REQUEST`, and its whole purpose is to allow several
action-scoped lifetimes within one command — a loop over a batch, one action per item.
Auto-injection builds a single ACTION container per command, so the injected value is one fixed
instance for the whole command: it removes the multiplicity that is the only reason ACTION sits
below REQUEST. It would silently destroy the loop case and surprise anyone using ACTION as
intended.

Caller-driven achieves the same deepening goal — `modern-di`'s `build_child_container()` stops
appearing at every call site — without changing what ACTION means. Each `with action_scope(ctx)`
block is a fresh container.

Three sub-decisions were taken with it. The manager is **ctx-based**, promoting the existing
private command-container concept rather than introducing a new injection marker for an opener. It
yields the **raw `Container`**: `resolve_provider` / `resolve` is `modern-di`'s normal interface
and not a leak worth hiding — only `build_child_container` was. And the command container is
stashed on **`ctx.meta`**, which is per-invocation and isolated, rather than `ctx.obj`, which is
shared app state.

**Revisit trigger:** a concrete use case appears where "one action = one command" is the natural
model and the loop case is absent. At that moment auto-injection becomes worth reconsidering as an
additive option.
