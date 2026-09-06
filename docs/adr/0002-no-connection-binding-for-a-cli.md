# No connection binding: this integration uses only the resolution half of the kit

**Decision:** `modern_di_typer` composes `modern_di.integrations` for markers and resolution
(`from_di`, `parse_markers`, `resolve_markers`) and deliberately uses none of the connection-binding
half (`bind`, `classify_connection`).

The kit was designed against a survey of adapters that all share a shape: a framework hands the
adapter a per-unit-of-work object — a web `Request`, a broker `StreamMessage` — which `bind()`
turns into the DI context a child container is built with. Every sibling integration uses both
halves, so the standing question about this one is why it does not.

A CLI invocation has no such object. The only per-invocation thing Typer produces is Click's
`typer.Context`, and `@inject` already threads that through natively — it is the parameter the
command itself may declare, the carrier for `action_scope`, and the handle on the app container.
Binding it into DI context would make the same object reachable two ways, one of them stringly
typed. Accordingly the command container is built with no `context=` argument at all, and there is
no dictionary key `bind()` could derive.

That leaves the marker/parse/resolve triad, which maps one-to-one onto what this package used to
hand-roll, and one wrinkle the kit has no equivalent for: finding an already-declared
`typer.Context` parameter so `@inject` does not insert a redundant one. That scan stays local
because it is a Typer concern, not a DI one.

**Revisit trigger:** a per-invocation object worth putting into DI context appears — a CLI session
or transaction handle that providers should resolve against, rather than something the command
reads off `ctx` itself. At that point `bind`/`classify_connection` have something to attach to and
this integration should look like its siblings.
