"""Completion tree for the Trutina interactive shell.

Milestone 3 built this off Typer's own `registered_groups`/
`registered_commands`. Milestone 4 rebuilt it on top of Typer's
underlying Click command tree instead (`typer.main.get_command(app)`),
because Click's `Command.get_short_help_str()` is the same text
`--help` already prints for every group and subcommand -- reusing it
here means menu descriptions (D7) require zero new authored strings
and can never drift from the CLI's own `--help` output.

This module additionally understands two help shorthands so completion
never lags behind what the shell loop (shell/dispatch.py, shell/loop.py)
actually accepts:

- Trailing `help`: after a group (`/account `) or a group+subcommand
    (`/account list `), `help` is offered as a completion alongside real
    subcommands, since `<command...> help` is equivalent to
    `<command...> --help` (see shell/dispatch.py's trailing-help handling).
- Leading `help <target...>`: after `/help `, completion offers real
  command/subcommand names as the *target*, not the literal word
    "help" again, since `help <target...>` is equivalent to
    `<target...> --help`.

Still built dynamically -- never a hand-maintained list. Adding a new
feature group to app.py (or a new command to an existing group, or a
new `help=`/docstring) appears here automatically.
"""

from collections.abc import Iterable

import typer
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from trutina.cli.composition.app import app

from .builtins import SHELL_BUILTINS

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
    plus the shell's own built-in keywords (exit/quit/help), which have
    no Typer command and so are added explicitly rather than discovered.
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

    for name, builtin in SHELL_BUILTINS.items():
        tree[name] = (builtin.description, None)

    return tree


class _DescribedCompleter(Completer):
    """Command-tree completer carrying description text and help shorthands.

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
        *path, word = parts

        # Leading `help <target...>` -- complete the *target* being
        # typed (a real command/subcommand name), not the literal word
        # "help" again. `help account create` is equivalent to
        # `account create --help`, so the target completes exactly the
        # way typing `account create` directly would -- just without
        # also offering the trailing-help shorthand on top of itself.
        if path and path[0] == "help":
            yield from self._complete_path(path[1:], word, include_builtins=False)
            return

        yield from self._complete_path(path, word, offer_trailing_help=True)

    def _complete_path(
        self,
        path: list[str],
        word: str,
        *,
        offer_trailing_help: bool = False,
        include_builtins: bool = True,
    ) -> Iterable[Completion]:
        """Yield completions for `word`, given the already-typed `path`.

        Args:
            path: Already-completed tokens before the word being typed
                (e.g. ``["account"]`` while typing the second word).
            word: The partial word currently being completed.
            offer_trailing_help: Whether to additionally offer a
                trailing ``help`` completion once `path` names a real
                group, or a real group+subcommand. False when
                completing the target after a leading ``help `` --
                ``help account help`` isn't a shorthand this shell
                supports.
            include_builtins: Whether shell-only keywords (exit/quit/
                help) are valid completions at this position. False
                when completing the target after ``help ``, since
                ``help exit`` isn't a meaningful target.
        """
        if not path:
            for name, (description, _subtree) in self._tree.items():
                if not include_builtins and name in SHELL_BUILTINS:
                    continue
                if name.startswith(word):
                    yield Completion(
                        name, start_position=-len(word), display_meta=description
                    )
            return

        group_name = path[0]
        entry = self._tree.get(group_name)
        if entry is None:
            return
        _description, subtree = entry

        if len(path) == 1:
            if subtree:
                for sub_name, sub_description in subtree.items():
                    if sub_name.startswith(word):
                        yield Completion(
                            sub_name,
                            start_position=-len(word),
                            display_meta=sub_description,
                        )
            if (
                offer_trailing_help
                and group_name not in SHELL_BUILTINS
                and "help".startswith(word)
            ):
                yield Completion(
                    "help",
                    start_position=-len(word),
                    display_meta=f"Show help for {group_name}.",
                )
            return

        if len(path) == 2 and offer_trailing_help:
            _group_name, sub_name = path
            if subtree and sub_name in subtree and "help".startswith(word):
                yield Completion(
                    "help",
                    start_position=-len(word),
                    display_meta=f"Show help for {group_name} {sub_name}.",
                )


def build_completer() -> Completer:
    """Build the shell's tab/live-narrowing completer from the live app.

    Returns:
        A Completer yielding group names then subcommand names, each
        carrying its real `--help` description as `display_meta`,
        transparent to an optional leading '/' per D6, and offering
        `help` as a trailing completion at both the group and
        group+subcommand levels (or real command names as the target
        after a leading `help `).
    """
    return _DescribedCompleter()
