"""
Terminal formatting for validation errors and journal entry output.

This module translates domain objects and Pydantic validation failures
into Rich-rendered terminal output. Formatting concerns are kept here
and away from the domain layer.
"""

from typing import Any

from pydantic import ValidationError
from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from pyledger.core.errors import ERRORS, Error, ErrorCode
from pyledger.core.models.journal import JournalEntry

from .console import console
from .constants import HINTS


def get_error_detail(error: dict[str, Any]) -> Error:
    """Build a complete user-facing error from a single Pydantic error dict.

    Looks up both the error message and resolution hint by error type.
    Falls back to the unknown error entry when the type is not recognised.

    Args:
        error: A single error dict from ``ValidationError.errors()``.

    Returns:
        An Error containing the matching ErrorDetail and hint string.
    """
    error_type = error["type"]
    detail = ERRORS.get(error_type, ERRORS[ErrorCode.UNKNOWN_ERROR])
    hint = HINTS.get(error_type, HINTS[ErrorCode.UNKNOWN_ERROR])
    return Error(detail=detail, hint=hint)


def error_formatter(errors: ValidationError) -> None:
    """Render Pydantic validation errors as Rich panels in the terminal.

    Each error in the ValidationError is rendered as a separate panel
    showing the field location, error message, error code, and a hint
    to help the user resolve the issue.

    Args:
        errors: The ValidationError raised by a Pydantic model.
    """
    for error in errors.errors():
        field = ".".join(map(str, error.get("loc", []))) or "unknown"

        error_config = get_error_detail(error)

        error_format = (
            "Validation Error\n\n"
            f"Field: {field}\n"
            f"Message: {error_config.detail.message}\n"
            f"Code: [warning]{error_config.detail.code}[/]\n"
            f"Hint:\n"
            f"  [info]{error_config.hint}[/]"
        )

        console.print(
            Panel(error_format, title="Error", style="error", border_style="error")
        )


def journal_entry_formatter(entry: JournalEntry) -> None:
    """Render a journal entry as a Rich panel in the terminal.

    Displays the entry header, posting date, description, a table of
    journal lines with debit and credit amounts, and a totals summary.
    The totals row highlights whether the entry is balanced.

    Args:
        entry: A validated JournalEntry to display.
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
        debit = f"{line.debit_amount:.2f}" if line.debit_amount else ""
        credit = f"{line.credit_amount:.2f}" if line.credit_amount else ""
        row_style = "debit" if line.debit_amount else "credit"
        table.add_row(line.account, debit, credit, style=row_style)

    header = Text(
        f"Journal Entry #{entry.journal_number}\n",
        style="info",
    )

    posting_date = Text(
        f"Posting Date: {entry.posting_date:%Y-%m-%d}",
        style="info",
    )

    description = Text(
        entry.description or "No description provided.",
        style="warning",
    )

    totals_style = "success" if entry.is_balanced else "error"
    totals = Text(
        (
            f"Total Debit:  {entry.total_debits:.2f}\n"
            f"Total Credit: {entry.total_credits:.2f}"
        ),
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
