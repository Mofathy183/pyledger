"""Public HTTP request/response contracts for the journal feature.

Structurally similar to `modules/journal/dtos.py`'s DTOs and
`JournalLineViewModel`/`JournalViewModel` by design -- the journal-entry
resource has one natural shape -- but kept as separate classes so the
public HTTP contract can evolve independently of the service boundary's
DTOs, per `PyLedger API Feature & Testing Prompt` Section 2.

Request schemas perform FastAPI/Pydantic structural validation only.
Accounting rules -- account existence, debit/credit exclusivity, entry
balance, posting-date bounds -- fire later, inside
`JournalService.create_journal_entry()` and the `JournalLine`/
`JournalEntry` domain models, and are translated to the standard error
envelope by `api/shared/errors/handlers.py`.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field
from pyledger.api.shared.response import SuccessResponse


class JournalLineRequest(BaseModel):
    """A single debit/credit line within a journal-entry creation request.

    Field constraints mirror `JournalLineInput` (`modules/journal/dtos.py`)
    so a malformed line fails fast at the transport layer (422 via
    FastAPI's own request validation) before ever reaching the service.
    Debit/credit exclusivity and account-name validity are not (and
    cannot be) expressed here; they fire inside
    `JournalService.create_journal_entry()`.
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


class CreateJournalEntryRequest(BaseModel):
    """Request body for ``POST /journal-entries``.

    Field constraints mirror `CreateJournalInput`. The journal number is
    intentionally absent from this contract -- it is assigned by
    `JournalService` via `JournalRepo.next_journal_number()`, never
    supplied by the caller, matching `CreateJournalInput`'s own
    omission of the field.
    """

    posting_date: datetime = Field(description="Journal-entry posting date.")
    lines: list[JournalLineRequest] = Field(
        min_length=2,
        description="The lines of the journal entry.",
    )
    description: str | None = Field(
        default=None,
        max_length=255,
        description="An optional short description for the journal entry.",
    )


class JournalLineData(BaseModel):
    """The journal-line resource shape embedded in a journal-entry response.

    Mirrors `JournalLineViewModel` (`modules/journal/dtos.py`) field for
    field.
    """

    account: str
    debit_amount: Decimal
    credit_amount: Decimal


class JournalEntryData(BaseModel):
    """The journal-entry resource shape returned by every journal endpoint.

    Mirrors `JournalViewModel` field for field, including the computed
    totals and balance flag, so clients never need to re-derive them
    from the lines.
    """

    journal_number: int
    posting_date: datetime
    description: str | None
    lines: list[JournalLineData]
    total_debits: Decimal
    total_credits: Decimal
    is_balanced: bool


class JournalEntryResponse(SuccessResponse):
    """Response envelope for endpoints returning a single journal entry.

    Used by create and get. ``entry`` carries the resource;
    ``success``/``timestamp`` are inherited from ``SuccessResponse``.
    """

    entry: JournalEntryData


class JournalEntriesResponse(SuccessResponse):
    """Response envelope for ``GET /journal-entries`` (list all entries)."""

    entries: list[JournalEntryData]
