# The app container is read from the root command's context settings, not from `ctx.obj`

**Decision:** `setup_di` stores the app container under one key in the Typer app's
`context_settings["obj"]`, and `fetch_di_container(ctx)` reads it back from
`ctx.find_root().command.context_settings["obj"]`. The key, the write and the read live together in
`modern_di_typer/main.py`; nothing reads `ctx.obj`.

`context_settings["obj"]` is the only channel from a Typer app into a Click context: `setup_di` runs
against the `typer.Typer` instance, the Click command is built from it later, and `obj` is the one
setting Click hands to the root context unchanged. The write side has no alternative.

The read side did. Reading `ctx.obj` is the obvious choice and was the original one, but `ctx.obj`
is Typer's user-facing slot and users overwrite it. Typer's own documentation assigns `ctx.obj` in
the app callback; a sub-app added with `add_typer` may declare its own `context_settings["obj"]`,
which shadows the parent's for every command under it. In both cases the container was gone by the
time `@inject` looked for it, and the error blamed a missing `setup_di` call that had in fact been
made. Namespacing the key inside `ctx.obj` fixes neither: the whole object is replaced, not one
key.

The root command's `context_settings` is the dict `setup_di` wrote to, reached from any depth of
the context tree, and untouched by anything a callback or a sub-app does to `ctx.obj`. The key
stays `"di_container"`: it is no longer part of the read path, so renaming it would break anyone
who had followed the old README's advice to read it directly and buy nothing.

**Revisit trigger:** Typer grows a per-app slot that reaches the Click context without going
through `obj` — at that point the container belongs there and `obj` returns fully to the user — or
a single-command app whose one command declares its own `context_settings` is reported: Typer then
builds the root command from the command's settings rather than the app's, and this read finds
nothing.
