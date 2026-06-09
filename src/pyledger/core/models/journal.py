from datetime import datetime
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    Field,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError

from pyledger.core.rules.journal_rules import (
    clean_account_name,
    debits_equal_credits,
)


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
            description="Unique Reference Number for the journal entry",
        ),
    ]

    posting_date: Annotated[
        datetime,
        Field(
            description="The Posting Date for the Journal Entry",
            gt=datetime(2020, 1, 1),
            le=datetime.today(),
        ),
    ]

    debit_account: Annotated[
        StrictStr,
        Field(
            description="The Debit Account name, or its Abbreviations",
            max_length=150,
            min_length=2,
        ),
    ]

    credit_account: Annotated[
        StrictStr,
        Field(
            description="The Credit Account name, or its Abbreviations",
            max_length=150,
            min_length=2,
        ),
    ]

    debit_balance: Annotated[
        StrictInt,
        Field(
            gt=0,
            description="the balance for the credit account",
        ),
    ]

    credit_balance: Annotated[
        StrictInt,
        Field(
            gt=0,
            description="the balance for the credit account",
        ),
    ]

    description: Annotated[
        str | None,
        Field(
            description="A short description for the journal entry and what it do",
            max_length=50,
        ),
    ]

    @field_validator("debit_account", "credit_account")
    @classmethod
    def validate_account_names(cls, value: str, info) -> str:
        """Validate and normalize account references.

        Account names may be entered using either their full names or
        approved abbreviations. Names are normalized before storage to
        ensure consistent account matching throughout the system.

        Args:
            value: User-provided account name.
            info: Validation context supplied by Pydantic.

        Returns:
            The normalized account name.

        Raises:
            PydanticCustomError: If the account reference is invalid.
        """
        cleaned = clean_account_name(value)

        if cleaned is None:
            raise PydanticCustomError(
                "invalid_account_name",
                "",
                {
                    "field": info.field_name,
                },
            )

        return cleaned

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
        if not debits_equal_credits(self.debit_balance, self.credit_balance):
            raise PydanticCustomError(
                "balances_not_equal",
                "",
                {"field": "balances"},
            )

        return self
