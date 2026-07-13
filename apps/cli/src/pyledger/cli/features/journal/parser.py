"""
CLI-argument-to-DTO adapter for the Journal CLI feature.

Mirrors cli/features/account/parser.py: both the CLI-flag path and the
interactive path (prompt.py) funnel through these functions so DTO
construction has one source of truth regardless of input origin.

    Typer arguments -----> parse_*() -----> DTO
    Rich prompts (prompt.py) -----> parse_*() -----> DTO

Journal entries carry a nested list of lines rather than Account's flat
scalar fields, so this module adds functions beyond the two top-level
parse_create_*/parse_update_* seen in the Account feature:
parse_journal_line() builds a single JournalLineInput, and
parse_line_spec() additionally understands the colon-delimited
"Account:Debit:Credit" shorthand used by the --line CLI flag. Both the
CLI-flag path (parse_line_spec, once per --line) and the interactive
path (prompt.py, calling parse_journal_line() directly with prompted
values) converge on parse_journal_line() for line construction.

Explicitly NOT this module's responsibility (identical to the Account
parser):

- Business or domain validation — owned by JournalLineInput/
    CreateJournalInput (structural) and JournalEntry/JournalLine
    (business rules via JournalService), both surfacing through the
    existing pydantic.ValidationError -> ValidationAppError path.
- Calling services or repositories.
- Rich prompting, rendering, or console output.

This module must never be imported by service or domain code.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation

import typer
from pyledger.core.journal.dtos import CreateJournalInput, JournalLineInput
from pyledger.shared.util import default_posting_date

_POSTING_DATE_FORMAT = "%Y-%m-%d"


def _clean(value: str) -> str:
    """Strip incidental surrounding whitespace from raw CLI input.

    Mirrors account/parser.py's ``_clean`` exactly — normalization of
    input noise, not domain validation. Genuine validation failures
    still surface unchanged from the DTO/domain layers.
    """
    return value.strip()


def _parse_amount(raw: str) -> Decimal:
    """Resolve a raw amount string to a Decimal, defaulting blank to zero.

    A blank segment means "no amount on this side," matching
    JournalLineInput's own zero defaults for debit_amount/credit_amount
    — it is not itself a validation failure.

    Args:
        raw: Raw amount string, e.g. "100.00" or "".

    Returns:
        The parsed Decimal amount, or Decimal("0") if blank.

    Raises:
        typer.BadParameter: If ``raw`` is non-blank but not a valid
            decimal.
    """
    cleaned = raw.strip()
    if not cleaned:
        return Decimal("0")

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        raise typer.BadParameter(f"'{raw}' is not a valid decimal amount.") from None


def parse_posting_date(raw: str | None) -> datetime:
    """Resolve a raw posting-date string, defaulting to today when blank.

    Mirrors the behavior already documented in cli/constants/errors.py's
    FUTURE_DATE hint ("Leave it blank and today's date will be used
    automatically"). Uses shared.util.default_posting_date() — the
    module's one existing consumer.

    Args:
        raw: Raw date string in YYYY-MM-DD format, or None/blank to use
            today's date.

    Returns:
        The parsed posting date, or today's date if ``raw`` is None or
        blank.

    Raises:
        typer.BadParameter: If ``raw`` is non-blank but does not match
            YYYY-MM-DD.
    """
    if raw is None or not raw.strip():
        return default_posting_date()

    try:
        return datetime.strptime(raw.strip(), _POSTING_DATE_FORMAT)
    except ValueError:
        raise typer.BadParameter(
            f"'{raw}' is not a valid date. Use YYYY-MM-DD."
        ) from None


def parse_journal_line(
    *,
    account: str,
    debit_amount: str = "0",
    credit_amount: str = "0",
) -> JournalLineInput:
    """Build a JournalLineInput from raw single-line values.

    The single place both the CLI-flag path (via parse_line_spec) and
    the interactive path (prompt.py) converge to construct a journal
    line, mirroring how parse_create_account/parse_update_account are
    the Account feature's convergence points.

    Args:
        account: Raw account name, as typed or prompted.
        debit_amount: Raw debit amount string, or "0"/blank for none.
        credit_amount: Raw credit amount string, or "0"/blank for none.

    Returns:
        The constructed JournalLineInput.

    Raises:
        typer.BadParameter: If either amount is non-blank but not a
            valid decimal.
        pydantic.ValidationError: If the account name or amounts fail
            JournalLineInput's structural validation (e.g. both amounts
            zero, or both nonzero).
    """
    return JournalLineInput(
        account=_clean(account),
        debit_amount=_parse_amount(debit_amount),
        credit_amount=_parse_amount(credit_amount),
    )


def parse_line_spec(raw: str) -> JournalLineInput:
    """Parse a single ``--line`` CLI flag value into a JournalLineInput.

    Expects the shorthand "Account:Debit:Credit", e.g. "Cash:100:0" or
    "Sales Revenue::100" (blank segments default to zero). This
    shorthand exists only for the CLI-flag path — the interactive path
    (prompt.py) never builds this string and calls parse_journal_line()
    directly with separately prompted values.

    Args:
        raw: The raw ``--line`` option value.

    Returns:
        The constructed JournalLineInput.

    Raises:
        typer.BadParameter: If ``raw`` does not split into exactly three
            colon-delimited segments, or if either amount segment is
            non-blank but not a valid decimal.
        pydantic.ValidationError: If the resulting line fails
            JournalLineInput's structural validation.
    """
    parts = raw.split(":")
    if len(parts) != 3:
        raise typer.BadParameter(
            f"'{raw}' is not a valid line. "
            "Expected format: 'Account:Debit:Credit', e.g. 'Cash:100:0'."
        )

    account, debit_amount, credit_amount = parts
    return parse_journal_line(
        account=account,
        debit_amount=debit_amount,
        credit_amount=credit_amount,
    )


def parse_create_journal(
    *,
    posting_date: str | None,
    lines: list[JournalLineInput],
    description: str | None = None,
) -> CreateJournalInput:
    """Build a CreateJournalInput from a resolved posting date and lines.

    Unlike parse_create_account, ``lines`` arrives as already-built
    JournalLineInput instances rather than raw scalars — both callers
    (parse_line_spec per --line flag, or prompt.py per prompted line)
    resolve individual lines through parse_journal_line() before
    reaching this function, since CreateJournalInput's minimum-two-lines
    rule applies to the assembled list, not any single line.

    Args:
        posting_date: Raw posting-date string, or None/blank to default
            to today via parse_posting_date().
        lines: The journal lines for this entry, already constructed.
        description: Raw description string, or None to omit.

    Returns:
        The constructed CreateJournalInput.

    Raises:
        typer.BadParameter: If ``posting_date`` is non-blank but not a
            valid YYYY-MM-DD date.
        pydantic.ValidationError: If ``lines`` has fewer than two
            entries or ``description`` exceeds CreateJournalInput's
            structural limits.
    """
    return CreateJournalInput(
        posting_date=parse_posting_date(posting_date),
        lines=lines,
        description=_clean(description) if description is not None else None,
    )
