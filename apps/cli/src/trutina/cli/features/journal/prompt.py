"""
Interactive prompt adapter for the Journal CLI feature.

Mirrors cli/features/account/prompt.py: collects values through the
shared themed Rich prompts (cli.shared.interaction) and hands them to
parser.py to become application DTOs. Never constructs
CreateJournalInput or JournalLineInput directly.

    User -> Rich Prompt -> Python values -> parser.py -> DTO

Explicitly NOT this module's responsibility (identical to the Account
prompt module): calling services or repositories, business/domain
validation, or rendering result panels for command output — those live
in formatter.py.
"""

from pyledger.cli.shared.interaction import ask, confirm
from pyledger.cli.shared.ui import console
from pyledger.core.journal.dtos import CreateJournalInput, JournalLineInput
from rich.text import Text

from .parser import parse_create_journal, parse_journal_line


def _prompt_posting_date() -> str | None:
    """Prompt for the posting date, or blank to accept today's date.

    Returns:
        The raw posting-date string as entered, or None if left blank
        (parser.parse_posting_date() resolves that to today's date).
    """
    value = ask("Posting Date (YYYY-MM-DD, blank for today)", default="")
    return value or None


def _prompt_description() -> str | None:
    """Prompt for an optional journal-entry description.

    Returns:
        The description as entered, or None if left blank.
    """
    value = ask("Description (optional)", default="")
    return value or None


def _prompt_line(index: int) -> JournalLineInput:
    """Prompt for a single journal line's account and amounts.

    Args:
        index: 1-based position of this line, used only for the prompt
            label.

    Returns:
        The JournalLineInput built by parser.parse_journal_line() from
        the collected values.
    """
    account = ask(f"Line {index} — Account")
    debit_amount = ask(f"Line {index} — Debit Amount", default="0")
    credit_amount = ask(f"Line {index} — Credit Amount", default="0")

    return parse_journal_line(
        account=account,
        debit_amount=debit_amount,
        credit_amount=credit_amount,
    )


def _prompt_lines() -> list[JournalLineInput]:
    """Prompt for journal lines until the user stops adding them.

    A journal entry requires at least two lines, so the first two are
    always collected before the "add another?" option appears.

    Returns:
        The collected JournalLineInput list, in entry order.
    """
    lines = [_prompt_line(1), _prompt_line(2)]

    index = 3
    while confirm("Add another line?", default=False):
        lines.append(_prompt_line(index))
        index += 1

    return lines


def prompt_create_journal() -> CreateJournalInput:
    """Interactively collect the fields required to create a journal entry.

    Prompts for the posting date, at least two journal lines, and an
    optional description, then delegates DTO construction to
    parse_create_journal(). This function never constructs
    CreateJournalInput directly.

    Returns:
        The CreateJournalInput DTO built by the parser from the
        collected values.
    """
    posting_date = _prompt_posting_date()
    lines = _prompt_lines()
    description = _prompt_description()

    return parse_create_journal(
        posting_date=posting_date,
        lines=lines,
        description=description,
    )


def prompt_journal_number() -> int:
    """Prompt the user for a journal entry number.

    Returns:
        The journal number as an int. Re-prompts on non-numeric input,
        printing a warning first so the user knows *why* the prompt
        repeated instead of appearing to silently ignore their input.
    """
    while True:
        raw = ask("Journal Number")
        try:
            return int(raw)
        except ValueError:
            console.print(
                Text(f'"{raw}" is not a valid journal number.', style="warning")
            )
