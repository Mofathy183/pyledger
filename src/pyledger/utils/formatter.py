"""
Terminal formatting for validation errors and journal entry output.

This module translates domain objects and Pydantic validation failures
into Rich-rendered terminal output. Formatting concerns are kept here
and away from the domain layer.
"""

from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from pyledger.core.errors import ERRORS, Error, ErrorCode, ErrorDetail
from pyledger.core.models.journal import JournalEntry

from .constants import FIELD_LABELS, HINTS


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


def _resolve_field(error: dict[str, Any]) -> str:
    """Resolve the display field associated with a validation error.

    Pydantic field-level validation errors include a location path that
    identifies the affected field. Model-level validation errors do not
    provide a location, so a synthetic field label is derived from the
    error type to produce more useful CLI output.

    Args:
        error: A single error dict from ``ValidationError.errors()``.

    Returns:
        A user-facing field name suitable for validation reporting.
    """
    loc = ".".join(map(str, error.get("loc", [])))
    if loc:
        return loc
    # Model-level validators produce an empty loc — fall back to a
    # human-readable label derived from the error type.
    return FIELD_LABELS.get(error["type"], "unknown")


@dataclass(frozen=True)
class FormattedError:
    """User-facing validation error prepared for terminal rendering.

    Stores the display field, resolved error metadata, and corrective
    hint required by the CLI presentation layer.
    """

    field: str
    detail: ErrorDetail
    hint: str


def format_validation_errors(errors: ValidationError) -> list[FormattedError]:
    """Convert Pydantic validation failures into display-ready errors.

    Resolves domain error metadata and user guidance for each validation
    failure so the CLI layer can render consistent error messages without
    depending on Pydantic's internal error structure.

    Args:
        errors: Validation error raised during model validation.

    Returns:
        A list of formatted validation errors ready for presentation.
    """
    formatted_errors = []
    for error in errors.errors():
        field = _resolve_field(error)

        error_config = get_error_detail(error)

        formatted_errors.append(
            FormattedError(
                field=field, detail=error_config.detail, hint=error_config.hint
            )
        )

    return formatted_errors


@dataclass(frozen=True)
class FormattedJournalLine:
    """Display-ready representation of a journal entry line.

    Stores account and posting amounts as formatted strings suitable
    for terminal rendering.
    """

    account: str
    debit: str
    credit: str
    is_debit: bool


@dataclass(frozen=True)
class FormattedJournalEntry:
    """Display-ready representation of a journal entry.

    Contains journal metadata, formatted posting lines, and summary
    totals required for rendering an accounting transaction in the CLI.
    Balance status is included to allow visual indication of whether
    total debits equal total credits.
    """

    journal_number: int
    posting_date: str
    description: str
    lines: list[FormattedJournalLine]
    total_debits: str
    total_credits: str
    is_balanced: bool


def format_journal_entry(entry: JournalEntry) -> FormattedJournalEntry:
    """Convert a journal entry into a CLI-friendly representation.

    Transforms domain values into formatted strings and presentation
    models suitable for terminal rendering. Accounting calculations
    and balance validation are assumed to have already been performed
    by the domain layer.

    Args:
        entry: Journal entry to prepare for display.

    Returns:
        A formatted journal entry ready for terminal presentation.
    """
    lines = [
        FormattedJournalLine(
            account=line.account,
            debit=f"{line.debit_amount:.2f}" if line.debit_amount else "",
            credit=f"{line.credit_amount:.2f}" if line.credit_amount else "",
            is_debit=bool(line.debit_amount),
        )
        for line in entry.lines
    ]

    return FormattedJournalEntry(
        journal_number=entry.journal_number,
        posting_date=f"{entry.posting_date:%Y-%m-%d}",
        description=entry.description or "No description provided.",
        lines=lines,
        total_debits=f"{entry.total_debits:.2f}",
        total_credits=f"{entry.total_credits:.2f}",
        is_balanced=entry.is_balanced,
    )
