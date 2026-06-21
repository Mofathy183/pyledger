"""
Centralized Rich console configuration for PyLedger.

This module defines the visual presentation layer used throughout the
CLI application. It provides a shared console instance, reusable themes,
and enhanced traceback rendering.

Accounting-specific styles are included to visually distinguish concepts
such as debits, credits, assets, liabilities, and journal entries,
improving readability during bookkeeping workflows.
"""

import os
import sys
from enum import Enum

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.traceback import install

from .formatter import FormattedError, FormattedJournalEntry


def _detect_color_level() -> str:
    """Determine whether enhanced background colors should be enabled.

    Different terminals expose different environment variables to signal
    support for true-color rendering. This helper attempts to detect
    modern terminal environments and enables background styling when
    supported.

    Returns:
        A Rich style fragment used to apply a background color when
        true-color support is available. Returns an empty string when
        enhanced styling should not be applied.
    """
    colorterm = os.environ.get("COLORTERM", "").lower()
    if colorterm in ("truecolor", "24bit"):
        return " on #EDE9E6"

    if os.environ.get("WT_SESSION"):
        return " on #EDE9E6"

    if os.environ.get("TERM_PROGRAM"):
        return " on #EDE9E6"

    if os.environ.get("PYCHARM_HOSTED") == "1":
        return " on #EDE9E6"

    term = os.environ.get("TERM", "")
    if "256color" in term:
        return " on #EDE9E6"

    if os.environ.get("PSModulePath"):
        return " on #EDE9E6"

    if sys.platform == "win32" and not os.environ.get("CONEMUANSI"):
        return ""

    return ""


_BG = _detect_color_level()


class ConsoleThemes(Enum):
    """Visual styles used throughout the PyLedger CLI.

    These themes provide a consistent visual language across the
    application.

    Categories include:

    - User interaction states:
        - Success
        - Error
        - Warning
        - Information

    - Accounting concepts:
        - Debit balances
        - Credit balances
        - Account classifications

    - Accounting reports and views:
        - Journal entries
        - T-accounts

    Enum values are Rich style definitions that are later converted
    into a Rich Theme instance.
    """

    SUCCESS = f"bold green{_BG}"
    ERROR = f"bold red{_BG}"
    WARNING = f"italic #7a6200{_BG}"
    INFO = f"italic #0f5a72{_BG}"

    DEBIT = f"bold #5C4F4A{_BG}"
    CREDIT = f"bold #8B6914{_BG}"

    ASSETS = f"bold #547A95{_BG}"
    LIABILITIES = f"bold #2a7a6e{_BG}"
    EQUITY = f"bold #744577{_BG}"

    JOURNAL_ENTRIES = f"bold #5E0006{_BG}"
    T_ACCOUNT = f"bold #462C7D{_BG}"


THEME_MAP = {theme.name.lower(): theme.value for theme in ConsoleThemes}

install(
    theme=THEME_MAP[ConsoleThemes.ERROR.name.lower()],
    show_locals=True,
)

console = Console(
    theme=Theme(THEME_MAP),
    highlight=True,
    soft_wrap=True,
)


def print_validation_errors(errors: list[FormattedError]) -> None:
    """Display validation errors in a user-friendly terminal format.

    Each error is rendered as a separate panel showing the affected
    field, validation message, error code, and a corrective hint.
    This function is intended for CLI presentation and assumes the
    supplied errors have already been formatted for display.

    Args:
        errors: Validation errors prepared for user-facing output.
    """
    for error in errors:
        error_format = (
            "Validation Error\n\n"
            f"Field: {error.field}\n"
            f"Message: {error.detail.message}\n"
            f"Code: [warning]{error.detail.code}[/]\n"
            f"Hint:\n"
            f"  [info]{error.hint}[/]"
        )

        console.print(
            Panel(error_format, title="Error", style="error", border_style="error")
        )


def print_journal_entry(entry: FormattedJournalEntry):
    """Render a journal entry as a formatted accounting report.

    Displays the journal entry header, posting date, description,
    transaction lines, and debit/credit totals in a tabular layout.
    The presentation highlights debit and credit postings separately
    and visually indicates whether the entry remains balanced.

    This function is responsible only for CLI rendering. It assumes
    all accounting validation, balancing checks, and formatting have
    already been performed by upstream layers.

    Args:
        entry: Journal entry data prepared for display.
    """
    table = Table(
        box=box.SIMPLE,
        border_style="journal_entries",
        header_style="journal_entries",
        expand=True,
    )

    table.add_column("Account", style="assets")
    table.add_column("Debit", justify="right", style="debit")
    table.add_column("Credit", justify="right", style="credit")

    for line in entry.lines:
        row_style = "debit" if line.is_debit else "credit"
        table.add_row(line.account, line.debit, line.credit, style=row_style)

    header = Text(
        f"Journal Entry #{entry.journal_number}\n",
        style="info",
    )

    posting_date = Text(
        f"Posting Date: {entry.posting_date}",
        style="info",
    )

    description = Text(
        entry.description,
        style="warning",
    )

    totals_style = "success" if entry.is_balanced else "error"
    totals = Text(
        f"Total Debit:  {entry.total_debits}\nTotal Credit: {entry.total_credits}",
        style=totals_style,
    )

    content = Group(
        header,
        posting_date,
        Rule(style="success"),
        table,
        Rule(style="success"),
        description,
        Rule(style="success"),
        totals,
    )

    console.print(
        Panel(
            content,
            title="Journal Entry",
            style="success",
            border_style="success",
            padding=(1, 2),
        )
    )
