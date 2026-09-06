# modern-di-typer

A [`modern-di`](https://github.com/modern-python/modern-di) integration for
[Typer](https://typer.tiangolo.com): a command declares its dependencies as annotations, and they
are resolved before its body runs, from a container whose lifetime matches the invocation.

## Language

A term is listed only when there is a synonym to reject, or a meaning subtle enough that code and
docs must agree on it. General programming vocabulary does not belong here, however heavily this
package uses it.

Two vocabularies meet here and neither is this package's to define. The domain terms are
`modern-di`'s — `Container`, `Provider`, `Group`, `Scope`, `Resolution`, `Override` — and that
project's `CONTEXT.md` is the authority for every one of them. The CLI terms are Typer's and
Click's — command, option, argument, callback, context. The three below are this package's own:
they name the three containers in play during a command, and telling them apart is most of what
this integration is.

**App container**:
The container the user constructs and opens for the life of the process. `setup_di` registers it on
a Typer app and `fetch_di_container(ctx)` reads it back. This package never builds one and never
opens one.

**Command container**:
The `Scope.REQUEST` child built for a single command invocation and closed when the command
returns — always, whether or not the command declares a `FromDI` parameter.
_Avoid_: request container. `Scope.REQUEST` is the scope's name, not the container's, and
"request" in a CLI invites an HTTP request that does not exist here.

**Action container**:
The `Scope.ACTION` child of the command container that one `action_scope(ctx)` block yields. One
per block, not one per command: opening several of them within a command — one per item of a
batch — is the reason `Scope.ACTION` sits below `Scope.REQUEST`
([ADR-0001](docs/adr/0001-action-scope-stays-caller-driven.md)).
