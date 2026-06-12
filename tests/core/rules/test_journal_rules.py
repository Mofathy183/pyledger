from decimal import Decimal

import pytest

from pyledger.core.rules.journal_rules import clean_account_name, is_valid_line_amounts


@pytest.mark.unit
class TestCleanAccountName:
    def test_returns_trimmed_name(self):
        account_name = "  Cash  "

        result = clean_account_name(account_name)

        assert result == "Cash"

    @pytest.mark.parametrize(
        "name, expected",
        [
            (
                "  Cash 2026  ",
                "Cash 2026",
            ),
            ("L&B", "L&B"),
            ("PP&E", "PP&E"),
            ("Owner's Equity", "Owner's Equity"),
            ("Non-current Assets", "Non-current Assets"),
        ],
    )
    def test_accepts_valid_account_names(self, name, expected):
        result = clean_account_name(name)

        assert result == expected

    def test_returns_none_when_name_is_empty_after_trimming(self):
        account_name = "     "

        result = clean_account_name(account_name)

        assert result is None

    def test_returns_none_when_name_starts_with_digit(self):
        account_name = "123Cash"

        result = clean_account_name(account_name)

        assert result is None

    @pytest.mark.parametrize(
        "name, expected",
        [
            ("343A/R", None),
            ("A/P %4", None),
            ("L&B.....", None),
            ("PP&&&&&&&E", None),
            ("Owner'''''''''s Equity", None),
            ("Non------current Assets", None),
        ],
    )
    def test_returns_none_for_invalid_account_names(self, name, expected):
        result = clean_account_name(name)

        assert result is expected


@pytest.mark.unit
class TestIsValidLineAmounts:
    @pytest.mark.parametrize(
        "debit, credit",
        [
            (Decimal("0"), Decimal("511")),
            (Decimal("422"), Decimal("0")),
        ],
    )
    def test_returns_true_for_valid_posting_amounts(self, debit, credit):
        result = is_valid_line_amounts(debit, credit)

        assert result is True

    @pytest.mark.parametrize(
        "debit, credit",
        [
            (Decimal("244"), Decimal("244")),
            (Decimal("0"), Decimal("0")),
        ],
    )
    def test_returns_false_for_invalid_posting_amounts(self, debit, credit):
        result = is_valid_line_amounts(debit, credit)

        assert result is False
