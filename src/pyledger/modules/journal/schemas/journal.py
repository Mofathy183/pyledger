from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from pyledger.shared.errors import ErrorCode, pydantic_error

from .line import JournalLine


class JournalEntry(BaseModel):
    """Represents a single double-entry accounting transaction.

    A journal entry records the financial impact of a business event
    before it is posted to the ledger. Every journal entry must contain
    at least one debit and one credit side of equal value.

    Important invariants:

    - Journal numbers identify individual transactions.
    - Posting dates must fall within the supported accounting period.
    - Debit and credit account names must be valid.
    - Debit and credit amounts must be positive values.
    - Total debits must equal total credits before the entry can be
      accepted into the accounting workflow.
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
        """Return the total debit value of the journal entry.

        The total debits represent the aggregate value recorded on the
        debit side of the transaction and are used to verify that the
        entry satisfies double-entry accounting requirements.
        """
        return sum((line.debit_amount for line in self.lines), Decimal("0"))

    @computed_field()
    @property
    def total_credits(self) -> Decimal:
        """Return the total credit value of the journal entry.

        The total credits represent the aggregate value recorded on the
        credit side of the transaction and are used to verify that the
        entry satisfies double-entry accounting requirements.
        """
        return sum((line.credit_amount for line in self.lines), Decimal("0"))

    @computed_field()
    @property
    def is_balanced(self) -> bool:
        """Determine whether the journal entry is balanced.

        A balanced journal entry satisfies the fundamental double-entry
        accounting rule that total debits must equal total credits.
        """
        return self.total_debits == self.total_credits

    @field_validator("posting_date")
    @classmethod
    def validate_posting_date(cls, value: datetime) -> datetime:
        """Prevent future-dated accounting transactions.

        Journal entries represent business events that have already
        occurred. Rejecting future posting dates helps preserve the
        integrity and chronological accuracy of accounting records.

        Args:
            value: The proposed posting date.

        Returns:
            The validated posting date.

        Raises:
            PydanticCustomError: If the posting date is in the future.
        """
        if value > datetime.now():
            raise pydantic_error(
                ErrorCode.FUTURE_DATE,
            )
        return value

    @model_validator(mode="after")
    def validate_balances(self) -> Self:
        """Enforce the double-entry accounting balance rule.

        Every journal entry must remain balanced. The total value
        recorded on the debit side must equal the total value recorded
        on the credit side.

        Returns:
            The validated journal entry instance.

        Raises:
            PydanticCustomError: If debit and credit totals are not equal.
        """
        if not self.is_balanced:
            raise pydantic_error(
                ErrorCode.UNBALANCED_ENTRY,
            )

        return self
