from typing import Annotated, Self

from pydantic import BaseModel, Field, PrivateAttr, model_validator

from pyledger.shared.errors import ErrorCode, pydantic_error
from pyledger.shared.rule import account_lookup_key

from .account import Account


class ChartOfAccounts(BaseModel):
    """The authoritative Chart of Accounts for the bookkeeping system.

    The chart defines every account that may participate in journal entries
    and postings. It ensures account references remain unambiguous by
    enforcing unique account codes and unique canonical account names across
    the entire chart.

    Account names preserve the casing provided at creation time. Uniqueness
    is enforced case-insensitively through :func:`account_lookup_key`, so
    "Cash" and "CASH" are treated as the same account name.

    Important invariants:

    - Every account code maps to exactly one account.
    - Every canonical account name maps to exactly one account.
    - Account-name comparisons are performed using the chart's canonical
      lookup rules rather than raw string comparison.
    """

    accounts: Annotated[
        list[Account],
        Field(description="All accounts available for posting."),
    ]

    _by_code: dict[str, Account] = PrivateAttr(default_factory=dict)
    _by_name: dict[str, Account] = PrivateAttr(default_factory=dict)

    @model_validator(mode="after")
    def validate_unique_codes(self) -> Self:
        """Ensure every account code uniquely identifies an account.

        Account codes act as stable identifiers throughout the bookkeeping
        system. Reusing a code would make journal references and posting
        operations ambiguous, since a single identifier could refer to more
        than one account.

        Returns:
            The validated chart of accounts.

        Raises:
            PydanticCustomError: If an account code is reused.
        """
        for account in self.accounts:
            if account.code in self._by_code:
                raise pydantic_error(ErrorCode.DUPLICATE_ACCOUNT_CODE)
            self._by_code[account.code] = account

        return self

    @model_validator(mode="after")
    def validate_unique_names(self) -> Self:
        """Ensure every canonical account name resolves to one account.

        Journal entries frequently reference accounts by name. Each account
        name must therefore resolve to a single account within the chart.
        Comparison uses :func:`account_lookup_key` so accounts that normalize
        to the same lookup key are treated as duplicates.

        Returns:
            The validated chart of accounts.

        Raises:
            PydanticCustomError: If two accounts share the same canonical
                lookup name.
        """
        for account in self.accounts:
            key = account_lookup_key(account.name)
            if key in self._by_name:
                raise pydantic_error(ErrorCode.DUPLICATE_ACCOUNT_NAME)
            self._by_name[key] = account

        return self

    def get_by_name(self, name: str) -> Account | None:
        """Resolve an account by name using the chart's lookup rules.

        Args:
            name: The account name supplied by a caller.

        Returns:
            The matching account if the name resolves to a known account;
            otherwise None.
        """
        return self._by_name.get(account_lookup_key(name))

    def get_by_code(self, code: str) -> Account | None:
        """Resolve an account by its chart code.

        Args:
            code: The account code.

        Returns:
            The matching account if the code exists in the chart;
            otherwise None.
        """
        return self._by_code.get(code)
