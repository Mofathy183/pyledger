from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


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


class Account(BaseModel):
    """Represents an account within the Chart of Accounts.

    The Chart of Accounts is the foundation of the accounting system.
    Each account records transactions belonging to a specific financial
    category and serves as a destination for journal entry postings.

    Important invariants:

    - Account codes should be unique within the chart.
    - Every account belongs to a single account category.
    - Every account has a defined normal balance nature.
    - Alias values provide alternative names or abbreviations that may
        be used when referencing the account.
    """

    code: Annotated[
        int,
        Field(
            gt=0,
            description="The code of the account that will be save",
        ),
    ]

    name: Annotated[
        str,
        Field(
            description="The name of the account",
            max_length=150,
            min_length=2,
        ),
    ]

    category: Annotated[
        AccountCategory,
        Field(description="The Categories of the account and it should be one of them"),
    ]

    normal_balance: Annotated[
        NormalBalance,
        Field(
            description=(
                "The normal balance nature of an account whether it be credit or debit"
            )
        ),
    ]

    aliases: Annotated[
        list[str],
        Field(
            description=(
                "The aliases names of an accounts, "
                "you can add up to 5 whether it aliases names or "
                "Abbreviations"
            ),
            max_length=5,
            default_factory=list,
        ),
    ]
