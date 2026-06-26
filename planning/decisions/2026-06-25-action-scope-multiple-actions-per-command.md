---
status: accepted
summary: Action scope stays caller-driven (`action_scope(ctx)`), preserving multiple actions per command, rather than auto-injecting ACTION params.
supersedes: null
superseded_by: null
---

# Action scope stays caller-driven, multiple per command

**Decision:** Reach `Scope.ACTION` deps through a caller-driven context manager
`action_scope(ctx)`, not by auto-resolving ACTION-scoped `FromDI` parameters into
the command signature.

## Context

When deepening ACTION scope behind `@inject`, two shapes were on the table:

- **(A) Auto-inject** — `@inject` builds one ACTION container per command and
  injects resolved ACTION params alongside REQUEST params. Symmetric and simple.
- **(B) Caller-driven** — a named context manager opens an ACTION container on
  demand; the command resolves from it.

`Scope.ACTION` is *finer* than `Scope.REQUEST`: its purpose is to allow **several**
action-scoped lifetimes within one command (e.g. a loop over a batch, one action
per item). Option (A) builds a single ACTION container per command, so the
injected value is one fixed instance — it removes the multiplicity that is the
whole reason ACTION sits below REQUEST.

## Decision & rationale

Chose **(B)**. It achieves the deepening goal — `modern_di`'s
`build_child_container()` stops appearing at every call site — without changing
what ACTION *means*. Each `with action_scope(ctx)` block is a fresh ACTION
container, so multiple-actions-per-command is preserved. Option (A) was rejected
because it silently destroys the loop case and would surprise anyone using ACTION
as intended.

Sub-decisions taken with it:

- The manager is **ctx-based** (`action_scope(ctx)`), promoting the existing
  private `_build_command_container` concept rather than introducing a new
  injection marker for an opener.
- It yields the **raw `Container`**; `resolve_provider`/`resolve` is `modern_di`'s
  normal interface and not a leak worth hiding — only `build_child_container` was.
- The command container is stashed on **`ctx.meta`** (per-invocation, isolated),
  not `ctx.obj` (shared app state), verified empirically.

## Revisit trigger

If a concrete use case appears where "one action = one command" is the natural
model and the loop case is absent — then auto-injection (A) becomes worth
reconsidering as an additive option.
