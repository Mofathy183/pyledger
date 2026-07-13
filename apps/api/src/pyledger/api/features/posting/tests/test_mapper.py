import pytest
from pyledger.api.features.posting.mapper import to_account, to_journal_number


@pytest.mark.unit
class TestToJournalNumber:
    def test_returns_value_unchanged(self):
        result = to_journal_number(5)

        assert result == 5


@pytest.mark.unit
class TestToAccount:
    def test_returns_value_unchanged_when_already_trimmed(self):
        result = to_account("Cash")

        assert result == "Cash"

    def test_strips_leading_and_trailing_whitespace(self):
        result = to_account("  Cash  ")

        assert result == "Cash"

    def test_does_not_alter_internal_whitespace(self):
        result = to_account("  Sales Revenue  ")

        assert result == "Sales Revenue"
