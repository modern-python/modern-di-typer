# The app container is read from the root command, not from `ctx.obj`

`setup_di` stores the app container in the Typer app's context settings, and `fetch_di_container`
reads it back from the root command those settings become, however deep in the context tree the
calling command sits. Nothing reads `ctx.obj`.

The context settings are the only channel from a Typer app into a Click context, so the write side
has no alternative. The read side did. `ctx.obj` was the original choice, and it is Typer's
user-facing slot: assigning it in the app callback is Typer's documented way to carry user state,
and a sub-app with its own settings shadows it for every command beneath. In both cases the
container was gone by the time a command looked for it, and the error blamed a `setup_di` call
that had been made. Namespacing the key inside `ctx.obj` fixes neither, because the whole object is
replaced.

The key keeps its old name. It is off the read path now, so renaming it would break anyone who read
it directly and buy nothing.

Revisit when Typer grows a per-app slot that reaches the Click context without going through the
user's object, or when a single-command app whose one command declares its own context settings is
reported: Typer then builds the root command from the command's settings rather than the app's, and
this read finds nothing.
