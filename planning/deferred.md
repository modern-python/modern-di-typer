# Deferred work

Items intentionally not actioned in the current work, kept here so they aren't
lost. Each has enough context to pick up cold.

## Give the app-container seam a single owner — from 2026-06-25 architecture review

`setup_di` writes the app container to `app.info.context_settings["obj"]["di_container"]`
and `fetch_di_container` reads `ctx.obj["di_container"]` (`modern_di_typer/main.py`).
The seam "where the app container lives" is a stringly-typed key in Typer's
user-facing `ctx.obj`, duplicated across two functions with no single owner, and
its behaviour under nested `add_typer` sub-apps is untested. A deepening would let
one small accessor own the key and the read/write, making the seam a typed
interface rather than a convention.

**Revisit trigger:** if nested `add_typer` apps become a supported case, or if a
collision with a user's own `ctx.obj` usage is reported. Until then the leverage
is modest and the current convention works. See the 2026-06-25 architecture
review (candidate 2).
