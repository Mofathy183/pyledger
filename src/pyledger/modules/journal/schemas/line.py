from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from pyledger.shared.errors import ErrorCode, pydantic_error
from pyledger.shared.rule import clean_account_name, is_valid_line_amounts


class JournalLine(BaseModel):
    """A single debit or credit posting within a journal entry.

    Journal lines are the building blocks of a double-entry transaction.
    Each line affects exactly one account and contributes value to one
    side of the transaction: either the debit side or the credit side.

    Account references are normalized before storage so that account
    matching remains consistent throughout the bookkeeping workflow.

    Attributes:
        account: Canonical account name affected by the transaction.
        debit_amount: Amount recorded on the debit side of the entry.
        credit_amount: Amount recorded on the credit side of the entry.

    Invariants:
        - Account names must be valid after normalization.
        - Amounts cannot be negative.
        - A line must contain either a debit amount or a credit amount.
        - A line cannot contain both a debit and a credit amount.
        - A line cannot contain neither a debit nor a credit amount.
    """

    account: Annotated[
        str,
        Field(
            description="Canonical account name affected by this transaction.",
            max_length=100,
            min_length=2,
        ),
    ]

    debit_amount: Annotated[
        Decimal,
        Field(
            ge=0,
            description="Amount recorded on the debit side of this line.",
        ),
    ] = Decimal("0")

    credit_amount: Annotated[
        Decimal,
        Field(
            ge=0,
            description="Amount recorded on the credit side of this line.",
        ),
    ] = Decimal("0")

    @field_validator("account")
    @classmethod
    def validate_account_names(cls, value: str) -> str:
        """Normalize account references used by journal entries.

        Journal entries refer to accounts by name. Normalizing account
        references ensures that equivalent user input resolves to a single
        canonical representation, allowing account lookups and validation
        to remain consistent throughout the accounting workflow.

        Args:
            value: User-provided account name.

        Returns:
            The normalized account name.

        Raises:
            PydanticCustomError: With code ``ErrorCode.INVALID_ACCOUNT_NAME``
                when the account name cannot be normalized into a valid
                account reference.
        """
        cleaned = clean_account_name(value)

        if cleaned is None:
            raise pydantic_error(ErrorCode.INVALID_ACCOUNT_NAME)

        return cleaned

    @model_validator(mode="after")
    def validate_line_amounts(self) -> Self:
        """Ensure the line represents exactly one side of a transaction.

        A journal line records the effect of a transaction on a single
        account. Recording both a debit and a credit on the same line would
        double-count the transaction's impact, while recording neither would
        contribute nothing to the entry. Every line must therefore carry
        value on exactly one side.

        Returns:
            The validated journal line.

        Raises:
            PydanticCustomError: With code ``ErrorCode.INVALID_LINE_AMOUNTS``
                when the line does not represent exactly one side of the
                transaction.
        """
        if not is_valid_line_amounts(self.debit_amount, self.credit_amount):
            raise pydantic_error(
                ErrorCode.INVALID_LINE_AMOUNTS,
            )

        return self
