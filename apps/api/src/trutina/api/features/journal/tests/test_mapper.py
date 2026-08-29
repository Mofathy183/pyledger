"""Unit tests for the journal feature's Request Schema -> Input DTO mapping.

Pure construction only -- no service calls, no accounting validation
(that fires later, inside the Handler's call into JournalService).
"""

from datetime import datetime
from decimal import Decimal

import pytest
from trutina.api.features.journal.mapper import to_create_journal_input
from trutina.api.features.journal.schemas import (
    CreateJournalEntryRequest,
    JournalLineRequest,
)
from trutina.core.journal.dtos import CreateJournalInput


def _make_request(
    *,
    posting_date: datetime = datetime(2025, 1, 1),
    description: str | None = None,
) -> CreateJournalEntryRequest:
    return CreateJournalEntryRequest(
        posting_date=posting_date,
        lines=[
            JournalLineRequest(account="Cash", debit_amount=Decimal("100")),
            JournalLineRequest(account="Sales Revenue", credit_amount=Decimal("100")),
        ],
        description=description,
    )


@pytest.mark.unit
class TestToCreateJournalInput:
    def test_maps_posting_date(self):
        request = _make_request(posting_date=datetime(2025, 1, 1))

        dto = to_create_journal_input(request)

        assert dto.posting_date == datetime(2025, 1, 1)

    def test_maps_lines(self):
        request = _make_request()

        dto = to_create_journal_input(request)

        assert len(dto.lines) == 2
        assert dto.lines[0].account == "Cash"
        assert dto.lines[0].debit_amount == Decimal("100")
        assert dto.lines[1].account == "Sales Revenue"
        assert dto.lines[1].credit_amount == Decimal("100")

    def test_maps_description_when_provided(self):
        request = _make_request(description="Sale transaction")

        dto = to_create_journal_input(request)

        assert dto.description == "Sale transaction"

    def test_maps_none_description_when_omitted(self):
        request = _make_request(description=None)

        dto = to_create_journal_input(request)

        assert dto.description is None

    def test_returns_create_journal_input_instance(self):
        dto = to_create_journal_input(_make_request())

        assert isinstance(dto, CreateJournalInput)
