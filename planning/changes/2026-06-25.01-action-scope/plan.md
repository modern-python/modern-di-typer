# action-scope — implementation plan

**Goal:** Ship `action_scope(ctx)` so commands reach `Scope.ACTION` deps without
touching `modern_di`'s container interface, preserving multiple actions per command.

**Spec:** [`design.md`](./design.md)

**Branch:** `feat/action-scope`

**Commit strategy:** Single commit (feature + docs + architecture promotion).

---

### Task 1: `action_scope` + wrapper change (TDD)

**Files:**
- Modify: `modern_di_typer/main.py`, `modern_di_typer/__init__.py`
- Modify: `tests/test_commands.py`, `tests/dependencies.py`

- [x] **Step 1: Tracer test (RED)** — `action_scope(ctx)` resolves an ACTION
  provider; fails on `ImportError`.

- [x] **Step 2: Implement (GREEN)** — add `_COMMAND_CONTAINER_KEY`,
  `action_scope`, export it; make `@inject` always build + stash the command
  container on `ctx.meta`.

- [x] **Step 3: Behavior tests** — distinct ACTION instance per iteration;
  cached `Scope.REQUEST` singleton shared with an injected param (add
  `cached_request_factory` to `tests/dependencies.py`).

- [x] **Step 4: Gates** — `just test-ci` (100%), `just lint-ci` (clean).

### Task 2: Docs promotion

**Files:**
- Modify: `README.md`, `CLAUDE.md`
- Modify: `architecture/scopes.md` (the promotion target)

- [x] **Step 1** — README "Action scope" section + API list; CLAUDE.md scope model.
- [x] **Step 2** — promote into `architecture/scopes.md`.

### Task 3: Ship

- [x] **Step 1: Commit + push + PR** — PR #15.
- [x] **Step 2: Watch CI** — all checks green.
