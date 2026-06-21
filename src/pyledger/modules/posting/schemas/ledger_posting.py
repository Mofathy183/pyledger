"""
Domain model for a posted accounting transaction line.

A ledger posting is a derived, immutable record produced when a journal
entry is posted to the ledger. Each posting represents the effect of a
single journal line on one account and carries a back-reference to the
originating journal entry for audit and tracing purposes.

Postings are read-only once created. The journal entry is the source of
truth; postings are a derived view of that truth distributed by account.
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from pyledger.shared.errors import ErrorCode, pydantic_error
from pyledger.shared.rule import clean_account_name, is_valid_line_amounts


class LedgerPosting(BaseModel):
    """Represents the effect of a single journal line on one account.

    A ledger posting is created when a balanced journal entry is posted
    to the ledger. It records the account affected, the amount posted,
    and a reference back to the originating journal entry.

    Postings are immutable. Once created they must not be modified,
    because they represent a permanent accounting record.

    Important invariants:

    - A posting must carry either a debit amount or a credit amount,
      not both and not neither.
    - Amounts must not be negative.
    - The account reference must be a valid, normalized account name.
    - The journal number must reference a valid journal entry.
    - The posting date must not be in the future.
    """

    model_config = ConfigDict(frozen=True)

    account: Annotated[
        str,
        Field(
            description="The account affected by this posting.",
            min_length=2,
            max_length=100,
        ),
    ]

    debit_amount: Annotated[
        Decimal,
        Field(
            ge=0,
            description="Debit amount posted to the account. Zero when this is a credit posting.",
        ),
    ] = Decimal("0")

    credit_amount: Annotated[
        Decimal,
        Field(
            ge=0,
            description="Credit amount posted to the account. Zero when this is a debit posting.",
        ),
    ] = Decimal("0")

    journal_number: Annotated[
        int,
        Field(
            gt=0,
            description="Journal entry number this posting was derived from.",
        ),
    ]

    posting_date: Annotated[
        datetime,
        Field(
            description="Date this posting was recorded. Inherited from the source journal entry.",
            gt=datetime(2020, 1, 1),
        ),
    ]

    @field_validator("account")
    @classmethod
    def validate_account(cls, value: str) -> str:
        """Validate and normalize the account reference.

        Account names must conform to the same naming rules used by
        journal lines. Leading and trailing whitespace is removed and
        the name is validated against the permitted character set.

        Args:
            value: Raw account name from the posting source.

        Returns:
            The normalized account name.

        Raises:
            PydanticCustomError: If the account name is invalid.
        """
        cleaned = clean_account_name(value)
        if cleaned is None:
            raise pydantic_error(ErrorCode.INVALID_ACCOUNT_NAME)
        return cleaned

    @field_validator("posting_date")
    @classmethod
    def validate_posting_date(cls, value: datetime) -> datetime:
        """Prevent future-dated postings.

        A posting date represents when the transaction was recorded.
        Postings cannot be dated in the future because they must reflect
        events that have already occurred.

        Args:
            value: Proposed posting date.

        Returns:
            The validated posting date.

        Raises:
            PydanticCustomError: If the date is in the future.
        """
        if value > datetime.now():
            raise pydantic_error(ErrorCode.FUTURE_DATE)
        return value

    @model_validator(mode="after")
    def validate_amounts(self) -> Self:
        """Enforce the single-side posting rule.

        A posting line must carry exactly one side of the accounting
        entry. Lines that carry both a debit and a credit, or neither,
        violate the structure of double-entry accounting.

        Returns:
            The validated posting instance.

        Raises:
            PydanticCustomError: If the posting amounts are invalid.
        """
        if not is_valid_line_amounts(self.debit_amount, self.credit_amount):
            raise pydantic_error(ErrorCode.INVALID_LINE_AMOUNTS)
        return self

    @property
    def is_debit(self) -> bool:
        """Return True when this posting records a debit movement."""
        return self.debit_amount > 0
