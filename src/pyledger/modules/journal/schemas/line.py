from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from pyledger.shared.errors import ErrorCode, pydantic_error
from pyledger.shared.rule import clean_account_name, is_valid_line_amounts


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
            raise pydantic_error(ErrorCode.INVALID_ACCOUNT_NAME)

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
            raise pydantic_error(
                ErrorCode.INVALID_LINE_AMOUNTS,
            )

        return self
