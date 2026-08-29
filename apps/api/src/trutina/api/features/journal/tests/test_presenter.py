"""Unit tests for the journal feature's ViewModel -> Response Schema mapping.

Pure construction only -- no service calls.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from pyledger.api.features.journal.presenter import (
    to_journal_entries_response,
    to_journal_entry_response,
)
from pyledger.api.features.journal.schemas import (
    JournalEntriesResponse,
    JournalEntryResponse,
)
from pyledger.core.journal.dtos import JournalLineViewModel, JournalViewModel


def _make_view_model(
    journal_number: int = 1,
    posting_date: datetime = datetime(2025, 1, 1),
    description: str | None = "Sale transaction",
) -> JournalViewModel:
    return JournalViewModel(
        journal_number=journal_number,
        posting_date=posting_date,
        description=description,
        lines=[
            JournalLineViewModel(
                account="Cash", debit_amount=Decimal("100"), credit_amount=Decimal("0")
            ),
            JournalLineViewModel(
                account="Sales Revenue",
                debit_amount=Decimal("0"),
                credit_amount=Decimal("100"),
            ),
        ],
        total_debits=Decimal("100"),
        total_credits=Decimal("100"),
        is_balanced=True,
    )


@pytest.mark.unit
class TestToJournalEntryResponse:
    def test_maps_journal_number(self):
        response = to_journal_entry_response(_make_view_model(journal_number=7))

        assert response.entry.journal_number == 7

    def test_maps_posting_date(self):
        posting_date = datetime(2024, 6, 15)

        response = to_journal_entry_response(
            _make_view_model(posting_date=posting_date)
        )

        assert response.entry.posting_date == posting_date

    def test_maps_description(self):
        response = to_journal_entry_response(_make_view_model(description="Payroll"))

        assert response.entry.description == "Payroll"

    def test_maps_lines(self):
        response = to_journal_entry_response(_make_view_model())

        assert len(response.entry.lines) == 2
        assert response.entry.lines[0].account == "Cash"
        assert response.entry.lines[0].debit_amount == Decimal("100")
        assert response.entry.lines[1].account == "Sales Revenue"
        assert response.entry.lines[1].credit_amount == Decimal("100")

    def test_maps_totals_and_balance(self):
        response = to_journal_entry_response(_make_view_model())

        assert response.entry.total_debits == Decimal("100")
        assert response.entry.total_credits == Decimal("100")
        assert response.entry.is_balanced is True

    def test_success_is_true(self):
        response = to_journal_entry_response(_make_view_model())

        assert response.success is True

    def test_returns_journal_entry_response_instance(self):
        response = to_journal_entry_response(_make_view_model())

        assert isinstance(response, JournalEntryResponse)


@pytest.mark.unit
class TestToJournalEntriesResponse:
    def test_maps_empty_entries(self):
        response = to_journal_entries_response([])

        assert response.entries == []

    def test_maps_single_entry(self):
        response = to_journal_entries_response([_make_view_model()])

        assert len(response.entries) == 1
        assert response.entries[0].journal_number == 1

    def test_maps_multiple_entries_in_order(self):
        response = to_journal_entries_response(
            [_make_view_model(journal_number=1), _make_view_model(journal_number=2)]
        )

        assert [e.journal_number for e in response.entries] == [1, 2]

    def test_returns_journal_entries_response_instance(self):
        response = to_journal_entries_response([])

        assert isinstance(response, JournalEntriesResponse)
