from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from pyledger.shared.errors import ErrorCode, pydantic_error

from .line import JournalLine


class JournalEntry(BaseModel):
    """A complete double-entry accounting transaction.

    A journal entry records the financial impact of a business event
    before it is posted to the ledger. Each entry must contain at least
    two journal lines and remain balanced, meaning the total value
    recorded as debits equals the total value recorded as credits.

    Posting dates are restricted to supported accounting periods and may
    not be future-dated. Journal numbers provide a positive transaction
    identifier within the bookkeeping workflow.

    Attributes:
        journal_number: Positive identifier assigned to the transaction.
        posting_date: Effective accounting date of the transaction.
        lines: Debit and credit lines that make up the transaction.
        description: Optional explanation of the business event.

    Invariants:
        - Journal numbers must be positive.
        - Posting dates must be later than 2020-01-01 and not in the future.
        - Entries must contain at least two journal lines.
        - Total debits must equal total credits.
    """

    journal_number: Annotated[
        int,
        Field(
            gt=0,
            description="Unique reference number for the journal entry.",
        ),
    ]

    posting_date: Annotated[
        datetime,
        Field(
            description="The Posting Date for the Journal Entry",
            gt=datetime(2020, 1, 1),
        ),
    ]

    lines: Annotated[
        list[JournalLine],
        Field(
            description=(
                "The lines of the journal entry, that include credit and debit accounts"
            ),
            min_length=2,
        ),
    ]

    description: Annotated[
        str | None,
        Field(
            description="A short description for the journal entry and what it do",
            max_length=255,
        ),
    ] = None

    @computed_field()
    @property
    def total_debits(self) -> Decimal:
        """Total debit value recorded by the journal entry.

        Computed from the current journal lines rather than stored
        independently. Storing the value separately could allow the total
        to drift from the underlying transaction lines and produce an
        incorrect balance calculation.
        """
        return sum((line.debit_amount for line in self.lines), Decimal("0"))

    @computed_field()
    @property
    def total_credits(self) -> Decimal:
        """Total credit value recorded by the journal entry.

        Computed from the current journal lines rather than stored
        independently. Storing the value separately could allow the total
        to diverge from the transaction lines and misrepresent the entry's
        accounting impact.
        """
        return sum((line.credit_amount for line in self.lines), Decimal("0"))

    @computed_field()
    @property
    def is_balanced(self) -> bool:
        """Whether the journal entry satisfies double-entry accounting.

        Computed from the current debit and credit totals rather than stored
        independently. A stored balance flag could become inconsistent with
        the underlying transaction lines if either side were modified.
        """
        return self.total_debits == self.total_credits

    @field_validator("posting_date")
    @classmethod
    def validate_posting_date(cls, value: datetime) -> datetime:
        """Ensure transactions are not recorded in the future.

        Journal entries represent business events that have already
        occurred. Allowing future-dated transactions would weaken the
        chronological integrity of the accounting record.

        Args:
            value: Proposed posting date.

        Returns:
            The validated posting date.

        Raises:
            PydanticCustomError: With code ``ErrorCode.FUTURE_DATE`` when the
                posting date is later than the current date.
        """
        if value > datetime.now():
            raise pydantic_error(
                ErrorCode.FUTURE_DATE,
            )
        return value

    @model_validator(mode="after")
    def validate_balances(self) -> Self:
        """Enforce the fundamental balance requirement of double-entry accounting.

        Every transaction must affect accounts equally on both sides of the
        books. An entry whose debit total differs from its credit total
        would leave the accounting records internally inconsistent and
        therefore cannot be accepted.

        Returns:
            The validated journal entry.

        Raises:
            PydanticCustomError: With code ``ErrorCode.UNBALANCED_ENTRY`` when
                total debits and total credits differ.
        """
        if not self.is_balanced:
            raise pydantic_error(
                ErrorCode.UNBALANCED_ENTRY,
            )

        return self
