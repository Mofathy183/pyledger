from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from pyledger.core.errors import ErrorCode, validation_error
from pyledger.core.rules.journal_rules import (
    clean_account_name,
    is_valid_line_amounts,
)


class JournalLine(BaseModel):
    """Represents a single posting line within a journal entry.

    A journal line records the effect of a transaction on a specific
    account. Each line references one account and contributes either a
    debit amount or a credit amount to the overall transaction.

    Important invariants:

    - Account references must resolve to a valid account name.
    - Account names are normalized before storage.
    - Debit and credit amounts cannot be negative.
    - A line must carry either a debit amount or a credit amount, not both
      and not either.
    """

    account: Annotated[
        str,
        Field(
            description="The Account name, or its Abbreviations",
            max_length=100,
            min_length=2,
        ),
    ]

    debit_amount: Annotated[
        Decimal,
        Field(
            ge=0,
            description="Debit amount recorded on this journal line.",
        ),
    ] = Decimal("0")

    credit_amount: Annotated[
        Decimal,
        Field(
            ge=0,
            description="Credit amount recorded on this journal line.",
        ),
    ] = Decimal("0")

    @field_validator("account")
    @classmethod
    def validate_account_names(cls, value: str) -> str:
        """Validate and normalize account references.

        Account names may be entered using either their full names or
        approved abbreviations. Names are normalized before storage to
        ensure consistent account matching throughout the system.

        Args:
            value: User-provided account name.

        Returns:
            The normalized account name.

        Raises:
            PydanticCustomError: If the account reference is invalid.
        """
        cleaned = clean_account_name(value)

        if cleaned is None:
            raise validation_error(ErrorCode.INVALID_ACCOUNT_NAME)

        return cleaned

    @model_validator(mode="after")
    def validate_line_amounts(self) -> Self:
        """Validate the accounting structure of a journal line.

        A journal line must represent a valid posting according to the
        application's double-entry accounting rules. This validation
        prevents invalid debit and credit combinations from entering the
        accounting workflow.

        Returns:
            The validated journal line instance.

        Raises:
            PydanticCustomError: If the line violates posting rules.
        """
        if not is_valid_line_amounts(self.debit_amount, self.credit_amount):
            raise validation_error(
                ErrorCode.INVALID_LINE_AMOUNTS,
            )

        return self


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
            raise validation_error(
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
            raise validation_error(
                ErrorCode.UNBALANCED_ENTRY,
            )

        return self
