"""
Service-boundary DTOs for the journal feature.

Input DTOs carry caller-supplied data into journal workflows.
View models carry service results back to presentation layers such
as the CLI.

This module separates external contracts from the journal domain
schemas. Callers depend on these DTOs rather than the internal
structure of JournalLine or JournalEntry.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

# Input DTOs — data coming IN to the service


class JournalLineInput(BaseModel):
    """Input DTO for a journal-entry line.

    Carries caller-supplied values for a single line of a journal
    entry. Accounting rules are enforced by the JournalLine domain
    model constructed by the service.
    """

    account: str = Field(
        min_length=2,
        max_length=100,
        description="The account name for this journal line.",
    )

    debit_amount: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Debit amount recorded on this journal line.",
    )

    credit_amount: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Credit amount recorded on this journal line.",
    )


class CreateJournalInput(BaseModel):
    """Input DTO for journal-entry creation.

    Carries the data required to create a new journal entry.

    The journal number is intentionally omitted from this contract.
    JournalService obtains the next number from JournalRepo as part of
    the creation workflow.

    Accounting validation is performed when the service constructs
    the JournalEntry domain model.
    """

    posting_date: datetime = Field(description="Journal-entry posting date.")

    lines: list[JournalLineInput] = Field(
        min_length=2,
        description="The lines of the journal entry.",
    )

    description: str | None = Field(
        default=None,
        max_length=255,
        description="An optional short description for the journal entry.",
    )


# ViewModels — data coming OUT of the service


class JournalLineViewModel(BaseModel):
    """Read-only representation of one journal-entry line.

    Returned by the service layer and consumed by presentation code.

    Derived totals and balance status are included explicitly so
    callers do not need to recompute accounting values from the
    underlying journal lines.
    """

    account: str
    debit_amount: Decimal
    credit_amount: Decimal


class JournalViewModel(BaseModel):
    """Read-only view of a single journal entry.

    Provides the service layer's public representation of a journal
    entry. Callers consume this model instead of JournalEntry internals.
    Computed totals and balance state are included so formatters and
    consumers never need to re-derive them.
    """

    journal_number: int
    posting_date: datetime
    description: str | None
    lines: list[JournalLineViewModel]
    total_debits: Decimal
    total_credits: Decimal
    is_balanced: bool
