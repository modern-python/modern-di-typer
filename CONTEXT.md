# modern-di-typer

The seam between a `modern_di` container and a Typer CLI: it maps `modern_di`'s
scope lifetimes onto a command's lifecycle and lets commands declare dependencies
as annotations instead of resolving them by hand.

## Language

**App container**:
The application-lifetime container, registered once against a Typer app. Lives for
the whole process.
_Avoid_: root container, global container

**Command container**:
The per-invocation container created for one command run, one lifetime band below
the app container. Every command run gets exactly one.
_Avoid_: request container (the underlying scope), wrapper container

**Action scope**:
A short-lived container nested inside the command container, opened on demand. A
single command run may open many — one per unit of work (e.g. per item in a batch).
_Avoid_: child container, sub-scope, nested container

**DI marker**:
The annotation that flags a command parameter for injection, naming the provider or
type to resolve. Distinct from the resolved value it stands in for.
_Avoid_: dependency annotation, injection token
