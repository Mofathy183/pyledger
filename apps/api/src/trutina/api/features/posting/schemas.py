"""HTTP request and response schemas for the posting API.

The posting feature exposes only read-side HTTP contracts. Ledger
postings are derived from validated journal entries by
``PostingService`` rather than submitted directly by clients, so this
module defines response schemas only.

``PostingItem`` represents a single derived ledger posting returned to
API clients, while ``PostingListResponse`` wraps the collection returned
by each posting endpoint.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field
from pyledger.api.shared.response import SuccessResponse


class PostingItem(BaseModel):
    """Read-only representation of a single ledger posting.

    A ledger posting records one side of a posted journal entry after it
    has been converted into the immutable accounting history. The schema
    mirrors the information exposed by the service layer while defining
    the HTTP response contract independently from internal view models.
    """

    account: str = Field(description="The account this posting was recorded against.")
    debit_amount: Decimal | None = Field(
        description="Debit amount, present only on a debit posting."
    )
    credit_amount: Decimal | None = Field(
        description="Credit amount, present only on a credit posting."
    )
    journal_number: int = Field(
        description="Journal entry number this posting was derived from."
    )
    posting_date: datetime = Field(
        description="Effective accounting date, inherited from the source journal entry."
    )
    is_debit: bool = Field(description="True when this is a debit posting.")


class PostingListResponse(SuccessResponse):
    """Successful response containing one or more ledger postings.

    Returned by every posting endpoint. The collection represents the
    postings derived from a journal entry or the postings matching a
    requested account, depending on the endpoint invoked.
    """

    postings: list[PostingItem]
