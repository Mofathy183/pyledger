"""Completion tree for the Trutina interactive shell.

Milestone 3 built this off Typer's own `registered_groups`/
`registered_commands`. Milestone 4 rebuilds it on top of Typer's
underlying Click command tree instead (`typer.main.get_command(app)`),
because Click's `Command.get_short_help_str()` is the same text
`--help` already prints for every group and subcommand -- reusing it
here means menu descriptions (D7) require zero new authored strings
and can never drift from the CLI's own `--help` output.

Still built dynamically -- never a hand-maintained list. Adding a new
feature group to app.py (or a new command to an existing group, or a
new `help=`/docstring) appears here automatically.
"""

from collections.abc import Iterable

import typer
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from trutina.cli.app import app
from trutina.cli.shell_builtins import SHELL_BUILTINS

# One entry per top-level name. For a group (account/journal/posting):
# (group_short_help, {subcommand_name: subcommand_short_help}).
# For a bare top-level command (none exist today, but the tree stays
# generic): (command_short_help, None).
type _Tree = dict[str, tuple[str, dict[str, str] | None]]


def _build_tree() -> _Tree:
    """Build {name: (description, subtree | None)} from the real Click app.

    typer.main.get_command(app) is typed as returning plain
    click.Command, even though the root of a Typer app with registered
    sub-apps is always a group-like command exposing `.commands`. Using
    getattr(..., "commands", {}) rather than assuming/narrowing the
    return type avoids depending on a type ty can't (and shouldn't have
    to) verify statically, and is more robust across Click/Typer
    versions than pinning to one exact class.
    plus the shell's own built-in keywords (exit/quit), which have no
    Typer command and so are added explicitly rather than discovered.
    """
    click_app = typer.main.get_command(app)
    tree: _Tree = {}

    top_level_commands = getattr(click_app, "commands", {})

    for name, command in top_level_commands.items():
        description = (command.get_short_help_str() or "").strip()
        sub_commands = getattr(command, "commands", None)

        if sub_commands:
            subtree = {
                sub_name: (sub_command.get_short_help_str() or "").strip()
                for sub_name, sub_command in sub_commands.items()
            }
            tree[name] = (description, subtree)
        else:
            tree[name] = (description, None)

    for name, description in SHELL_BUILTINS.items():
        tree[name] = (description, None)

    return tree


class _DescribedCompleter(Completer):
    """Two-level (group, subcommand) completer carrying description text.

    Replaces Milestone 3's NestedCompleter + _SlashAwareCompleter pair:
    NestedCompleter has no notion of `display_meta`, so it can't show a
    one-line description alongside each entry (D7). Slash-transparency
    (D6) is folded directly into get_completions() below rather than
    kept as a separate wrapper, since there is now only one completion
    path to make slash-aware.
    """

    def __init__(self) -> None:
        self._tree = _build_tree()

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        text = document.text_before_cursor
        if text.startswith("/"):
            text = text[1:]

        parts = text.split(" ")

        if len(parts) == 1:
            word = parts[0]
            for name, (description, _subtree) in self._tree.items():
                if name.startswith(word):
                    yield Completion(
                        name,
                        start_position=-len(word),
                        display_meta=description,
                    )
            return

        if len(parts) == 2:
            group_name, word = parts
            entry = self._tree.get(group_name)
            if entry is None:
                return
            _description, subtree = entry
            if not subtree:
                return
            for sub_name, sub_description in subtree.items():
                if sub_name.startswith(word):
                    yield Completion(
                        sub_name,
                        start_position=-len(word),
                        display_meta=sub_description,
                    )


def build_completer() -> Completer:
    """Build the shell's tab/live-narrowing completer from the live app.

    Returns:
        A Completer yielding group names then subcommand names, each
        carrying its real `--help` description as `display_meta`,
        transparent to an optional leading '/' per D6.
    """
    return _DescribedCompleter()
