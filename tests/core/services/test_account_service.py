import pytest

from pyledger.core.services.account import resolve_account
from tests.helpers import make_account


@pytest.mark.unit
class TestResolveAccount:
    def test_returns_account_when_name_matches(self, account):
        accounts = [account]

        result = resolve_account("Cash", accounts)

        assert result in accounts

    def test_returns_account_when_alias_matches(self):
        account = make_account(aliases=["Bank Account"])
        accounts = [account]

        result = resolve_account("Bank Account", accounts)

        assert result in accounts

    def test_returns_none_when_account_does_not_exist(self):
        accounts = [
            make_account(name="Cash"),
            make_account(
                code=2001,
                name="Accounts Payable",
            ),
        ]

        result = resolve_account("Equipment", accounts)

        assert result is None

    def test_returns_none_when_accounts_are_empty(self):
        result = resolve_account("Cash", [])

        assert result is None

    def test_returns_account_from_multiple_accounts_when_name_matches(self):
        cash = make_account(name="Cash")
        payable = make_account(
            code=2001,
            name="Accounts Payable",
        )

        accounts = [cash, payable]

        result = resolve_account("Accounts Payable", accounts)

        assert result in accounts

    def test_returns_account_from_multiple_accounts_when_alias_matches(self):
        cash = make_account(
            aliases=["Bank Account"],
        )
        payable = make_account(
            code=2001,
            name="Accounts Payable",
        )

        accounts = [cash, payable]

        result = resolve_account("Bank Account", accounts)

        assert result is cash

    def test_returns_first_matching_account_when_duplicate_names_exist(self):
        first = make_account(
            code=1001,
            name="Cash",
        )
        second = make_account(
            code=1002,
            name="Cash",
        )

        accounts = [first, second]

        result = resolve_account("Cash", accounts)

        assert result is first
        assert result.code == 1001

    def test_returns_first_matching_account_when_duplicate_aliases_exist(self):
        first = make_account(
            code=1001,
            aliases=["Bank Account"],
        )
        second = make_account(
            code=1002,
            name="Petty Cash",
            aliases=["Bank Account"],
        )

        accounts = [first, second]

        result = resolve_account("Bank Account", accounts)

        assert result is first
        assert result.code == 1001
