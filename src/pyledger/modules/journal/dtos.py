"""
Data transfer objects for the journal feature.

Input DTOs carry raw user or API input into the service layer without
enforcing accounting rules. ViewModels carry service results back to
the CLI or API without exposing domain internals.

The formatter depends only on the ViewModels defined here, never on
JournalEntry or JournalLine directly.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Input DTOs — data coming IN to the service
# ---------------------------------------------------------------------------


class JournalLineInput(BaseModel):
    """Input shape for a single journal line.

    Carries raw user-supplied values. No accounting validation is
    applied here — the service constructs a JournalLine domain object
    from this input, and the domain enforces the rules at that point.
    """

    account: str = Field(
        description="Account name or recognised alias.",
        min_length=1,
        max_length=100,
    )
    debit_amount: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Debit amount for this line. Zero means no debit posting.",
    )
    credit_amount: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Credit amount for this line. Zero means no credit posting.",
    )


class CreateJournalInput(BaseModel):
    """Input DTO for journal entry creation.

    The posting_date is optional — the service defaults to today when
    not supplied. The description is always optional. Lines must contain
    at least two entries, but balance enforcement happens in the domain,
    not here.
    """

    posting_date: datetime | None = Field(
        default=None,
        description="Posting date. Defaults to today if not provided.",
    )
    description: str | None = Field(
        default=None,
        max_length=255,
        description="Optional short description of the transaction.",
    )
    lines: list[JournalLineInput] = Field(
        min_length=2,
        description="Journal lines. Must balance when passed to the domain.",
    )


# ---------------------------------------------------------------------------
# ViewModels — data coming OUT of the service
# ---------------------------------------------------------------------------


class JournalLineViewModel(BaseModel):
    """Read-only view of a single journal line.

    Amounts are always present as Decimal. Zero means no posting on
    that side. The formatter uses _is_debit_line() to determine which
    side is active rather than checking for None.
    """

    account: str
    debit_amount: Decimal
    credit_amount: Decimal


class JournalViewModel(BaseModel):
    """Read-only view of a complete journal entry.

    This is the stable output contract between the service layer and
    all callers — CLI formatters, future API routes, tests. It does not
    expose JournalEntry internals and can be changed independently of
    the domain model.

    posting_date is carried as datetime to match the domain model.
    Formatters extract the date portion for display using fstr time.
    """

    journal_number: int
    posting_date: datetime
    description: str | None
    total_debits: Decimal
    total_credits: Decimal
    lines: list[JournalLineViewModel]
