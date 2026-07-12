"""
Service-boundary DTOs for the posting feature.

Postings are derived records — they are never submitted by a caller,
so this module defines an output-only view model only. There is no
input DTO: PostingService derives LedgerPosting instances directly
from an already-validated JournalEntry. There is no update DTO either,
since LedgerPosting is frozen by design.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, computed_field

# ViewModels — data coming OUT of the service


class PostingViewModel(BaseModel):
    """Read-only view of a single ledger posting.

    Provides the service layer's public representation of a posting.
    Callers consume this model instead of the underlying LedgerPosting
    domain model — the same boundary rule AccountViewModel and
    JournalViewModel enforce for their respective domains.

    ``is_debit`` is a computed field derived from ``debit_amount`` so
    that it can never be inconsistent with the stored amounts. A debit
    posting always has a non-None ``debit_amount`` and a None
    ``credit_amount``; a credit posting is the reverse.
    """

    account: str
    debit_amount: Decimal | None
    credit_amount: Decimal | None
    journal_number: int
    posting_date: datetime

    @computed_field
    @property
    def is_debit(self) -> bool:
        """Return True when this view model represents a debit posting.

        Derived from ``debit_amount`` so that it remains consistent with
        the amount fields regardless of how the view model was constructed.
        """
        return self.debit_amount is not None
