"""
Account domain model and account-category definitions.

Defines the core Chart of Accounts entities used throughout the
accounting domain. Depended on by account services, chart models,
and journal validation workflows. Must not import from the CLI layer.
"""

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, computed_field, field_validator
from trutina.shared.errors import ErrorCode, pydantic_error
from trutina.shared.rule import clean_account_name


class AccountCategory(Enum):
    """Classification categories used within the Chart of Accounts.

    Account categories determine how accounts are grouped for financial
    reporting and which side of the ledger represents their normal
    balance. Every account belongs to exactly one category, and that
    category controls whether increases are normally recorded as debits
    or credits.

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

# Maps each account category to the ledger side that normally increases
# the account's value. This relationship is derived from accounting
# principles and is used by Account.normal_balance.
NORMAL_BALANCE_BY_CATEGORY: dict[AccountCategory, NormalBalance] = {
    AccountCategory.ASSET: "debit",
    AccountCategory.EXPENSE: "debit",
    AccountCategory.DRAWING: "debit",
    AccountCategory.LIABILITY: "credit",
    AccountCategory.EQUITY: "credit",
    AccountCategory.REVENUE: "credit",
    AccountCategory.DIVIDEND: "credit",
}

ACCOUNT_CODE_PATTERN = r"^[0-9A-Za-z\-]+$"


class Account(BaseModel):
    """Represents an account within the Chart of Accounts.

    The Chart of Accounts is the foundation of the accounting system.
    Each account records transactions belonging to a specific financial
    category and serves as a destination for journal entry postings.

    Important invariants:

    - Account codes must be unique within the chart.
    - Every account belongs to a single account category.
    - Normal balance is derived from the account category and cannot be
        set independently.
    - Account names are normalized using the same rules applied to
        journal-line account references, so they can be matched
        consistently throughout the system.
    """

    code: Annotated[
        str,
        Field(
            min_length=1,
            max_length=20,
            pattern=ACCOUNT_CODE_PATTERN,  # digits, letters, hyphens only
            description="Chart of accounts code, e.g. '1000', '1010-A'.",
        ),
    ]

    name: Annotated[
        str,
        Field(
            description="The canonical name of the account.",
            max_length=150,
            min_length=2,
        ),
    ]

    category: Annotated[
        AccountCategory,
        Field(description="The classification category of the account."),
    ]

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Normalize the account's canonical name.

        Account names are normalized so that chart lookups and journal-line
        references resolve consistently regardless of differences in user
        input formatting.

        Args:
            value: Raw account name.

        Returns:
            The normalized account name.

        Raises:
            PydanticCustomError: If the account name is invalid.
        """
        cleaned = clean_account_name(value)

        if cleaned is None:
            raise pydantic_error(ErrorCode.INVALID_ACCOUNT_NAME)

        return cleaned

    @computed_field
    @property
    def normal_balance(self) -> NormalBalance:
        """Return the normal balance side derived from the account category.

        Normal balance is computed rather than stored so that an account's
        classification and balance behavior cannot silently diverge. If this
        value were independently editable, an Asset account could incorrectly
        be marked as credit-normal, violating a core accounting invariant.
        """
        return NORMAL_BALANCE_BY_CATEGORY[self.category]
