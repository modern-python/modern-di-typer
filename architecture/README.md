# Architecture

The living truth about what `modern-di-typer` does **now** — one file per
capability, updated by hand whenever a change ships. The *why* and *how it got
here* live in [`../planning/changes/`](../planning/changes/) — and decisions
deliberately taken, including options rejected, in
[`../planning/decisions/`](../planning/decisions/); this directory is the
present.

These files carry **no frontmatter** — they are prose, dated by git.

## Capabilities

- [scopes.md](scopes.md) — how `modern_di`'s scopes map onto a Typer command's
  lifecycle: the app container, the per-command container, and action scope
  (`setup_di`, `fetch_di_container`, `action_scope`).
- [injection.md](injection.md) — the `@inject` decorator and the `FromDI`
  marker: decoration-time signature rewriting and call-time resolution.

## Promotion rule

Shipping a change hand-edits the affected capability file(s) here to match the
new reality, in the same PR as the code. The change bundle stays in place under
[`../planning/changes/`](../planning/changes/) — no folder move.
