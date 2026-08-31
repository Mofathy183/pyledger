"""Shell built-in keywords for the Trutina interactive shell.

Kept as a single source of truth, separate from both shell.py (which
checks against it to decide whether to exit) and shell_completion.py
(which surfaces it in the completion menu) -- so the two can never
silently drift out of agreement the way two hand-maintained ("exit",
"quit") tuples eventually would.

These are shell-loop concepts, not Typer commands -- they have no
corresponding function in app.py's command tree, which is exactly why
they need to be added here rather than discovered from the Click app
the way every other completion entry is.
"""

SHELL_BUILTINS: dict[str, str] = {
    "exit": "Leave the interactive shell.",
    "quit": "Leave the interactive shell.",
}
