"""
Interactive prompt adapter for the Posting CLI feature.

Mirrors cli/features/account/prompt.py and cli/features/journal/prompt.py:
collects a single raw value through the shared themed Rich prompts
(cli.shared.interaction) and delegates validation to parser.py. Since
PostingService takes plain scalars rather than a DTO (see parser.py's
module docstring), these functions return validated primitives
(int, str) rather than a constructed DTO — there is nothing to
construct.
"""

import typer
from rich.text import Text

from pyledger.cli.shared.interaction import ask
from pyledger.cli.shared.ui import console

from .parser import parse_account_identifier, parse_journal_number


def prompt_journal_number() -> int:
    """Prompt the user for a journal entry number.

    Returns:
        The journal number as an int. Re-prompts on invalid input,
        printing the same message parse_journal_number() would raise
        as typer.BadParameter in flag mode, so both input paths give
        equivalent feedback for equivalent mistakes.
    """
    while True:
        raw = ask("Journal Number")
        try:
            return parse_journal_number(raw)
        except typer.BadParameter as exc:
            console.print(Text(str(exc), style="warning"))


def prompt_account_identifier() -> str:
    """Prompt the user for an account identifier.

    Returns:
        The cleaned account identifier, as resolved by
        parse_account_identifier().
    """
    return parse_account_identifier(ask("Account name"))
