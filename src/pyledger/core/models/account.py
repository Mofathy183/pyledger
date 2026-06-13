from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, computed_field, field_validator

from pyledger.core.errors import ErrorCode, validation_error
from pyledger.core.rules.journal_rules import clean_account_name


class AccountCategory(Enum):
    """Classification categories used within the Chart of Accounts.

    Account categories determine how balances are grouped and reported
    in financial statements. Every account must belong to exactly one
    category.

    Categories generally fall into three major groups:

    - Balance Sheet accounts:
        - Asset
        - Liability
        - Equity

    - Income Statement accounts:
        - Revenue
        - Expense

    - Owner-related accounts:
        - Dividend
        - Drawing
    """

    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"

    DIVIDEND = "DIVIDEND"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"
    DRAWING = "DRAWING"


NormalBalance = Literal["debit", "credit"]


NORMAL_BALANCE_BY_CATEGORY: dict[AccountCategory, NormalBalance] = {
    AccountCategory.ASSET: "debit",
    AccountCategory.EXPENSE: "debit",
    AccountCategory.DRAWING: "debit",
    AccountCategory.LIABILITY: "credit",
    AccountCategory.EQUITY: "credit",
    AccountCategory.REVENUE: "credit",
    AccountCategory.DIVIDEND: "credit",
}


class Account(BaseModel):
    """Represents an account within the Chart of Accounts.

    The Chart of Accounts is the foundation of the accounting system.
    Each account records transactions belonging to a specific financial
    category and serves as a destination for journal entry postings.

    Important invariants:

    - Account codes should be unique within the chart.
    - Every account belongs to a single account category.
    - Normal balance nature is derived from the account category and
        cannot be set independently.
    - Account names and aliases are normalized using the same rules
        applied to journal-line account references, so they can be
        matched consistently throughout the system.
    - Alias values provide alternative names or abbreviations that may
        be used when referencing the account.
    """

    code: Annotated[
        int,
        Field(
            gt=0,
            description="The code of the account that will be saved.",
        ),
    ]

    name: Annotated[
        str,
        Field(
            description="The name of the account.",
            max_length=150,
            min_length=2,
        ),
    ]

    category: Annotated[
        AccountCategory,
        Field(description="The classification category of the account."),
    ]

    aliases: Annotated[
        list[str],
        Field(
            description=(
                "Alternative names or abbreviations for the account. "
                "Up to 5 aliases are allowed."
            ),
            max_length=5,
            default_factory=list,
        ),
    ]

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Normalize the account name.

        Account names are normalized using the same rules applied to
        journal-line account references, so that a journal line can be
        reliably matched to its corresponding account.

        Args:
            value: Raw account name.

        Returns:
            The normalized account name.

        Raises:
            PydanticCustomError: If the account name is invalid.
        """
        cleaned = clean_account_name(value)

        if cleaned is None:
            raise validation_error(ErrorCode.INVALID_ACCOUNT_NAME)

        return cleaned

    @field_validator("aliases")
    @classmethod
    def validate_aliases(cls, value: list[str]) -> list[str]:
        """Normalize each alias using account-name rules.

        Aliases must be normalizable account names so they can be
        matched against journal-line account references using the
        same comparison rules as the primary account name.

        Args:
            value: Raw list of alias strings.

        Returns:
            The list of normalized aliases.

        Raises:
            PydanticCustomError: If any alias is invalid.
        """
        cleaned_aliases = []

        for alias in value:
            cleaned = clean_account_name(alias)

            if cleaned is None:
                raise validation_error(ErrorCode.INVALID_ACCOUNT_NAME)

            cleaned_aliases.append(cleaned)

        return cleaned_aliases

    @computed_field
    @property
    def normal_balance(self) -> NormalBalance:
        """Return the normal balance nature derived from the account category.

        The normal balance side is determined entirely by the account
        category and is not an independent attribute. Asset, Expense,
        and Drawing accounts are debit-normal. Liability, Equity,
        Revenue, and Dividend accounts are credit-normal.
        """
        return NORMAL_BALANCE_BY_CATEGORY[self.category]
