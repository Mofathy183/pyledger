from datetime import datetime
from decimal import Decimal

import pytest
from pyledger.api.features.posting.presenter import (
    to_posting_item,
    to_posting_list_response,
)
from pyledger.api.features.posting.schemas import PostingItem, PostingListResponse
from pyledger.core.posting.dtos import PostingViewModel


def _debit_vm() -> PostingViewModel:
    return PostingViewModel(
        account="Cash",
        debit_amount=Decimal("100.00"),
        credit_amount=None,
        journal_number=1,
        posting_date=datetime(2025, 1, 1),
    )


def _credit_vm() -> PostingViewModel:
    return PostingViewModel(
        account="Sales Revenue",
        debit_amount=None,
        credit_amount=Decimal("100.00"),
        journal_number=1,
        posting_date=datetime(2025, 1, 1),
    )


@pytest.mark.unit
class TestToPostingItem:
    def test_returns_posting_item_instance(self):
        result = to_posting_item(_debit_vm())

        assert isinstance(result, PostingItem)

    def test_maps_account(self):
        result = to_posting_item(_debit_vm())

        assert result.account == "Cash"

    def test_maps_debit_amount(self):
        result = to_posting_item(_debit_vm())

        assert result.debit_amount == Decimal("100.00")
        assert result.credit_amount is None

    def test_maps_credit_amount(self):
        result = to_posting_item(_credit_vm())

        assert result.credit_amount == Decimal("100.00")
        assert result.debit_amount is None

    def test_maps_journal_number(self):
        result = to_posting_item(_debit_vm())

        assert result.journal_number == 1

    def test_maps_posting_date(self):
        result = to_posting_item(_debit_vm())

        assert result.posting_date == datetime(2025, 1, 1)

    def test_maps_is_debit_true_for_debit_posting(self):
        result = to_posting_item(_debit_vm())

        assert result.is_debit is True

    def test_maps_is_debit_false_for_credit_posting(self):
        result = to_posting_item(_credit_vm())

        assert result.is_debit is False


@pytest.mark.unit
class TestToPostingListResponse:
    def test_returns_posting_list_response_instance(self):
        result = to_posting_list_response([_debit_vm(), _credit_vm()])

        assert isinstance(result, PostingListResponse)

    def test_wraps_every_view_model(self):
        result = to_posting_list_response([_debit_vm(), _credit_vm()])

        assert len(result.postings) == 2

    def test_preserves_order(self):
        result = to_posting_list_response([_debit_vm(), _credit_vm()])

        assert result.postings[0].account == "Cash"
        assert result.postings[1].account == "Sales Revenue"

    def test_returns_empty_postings_for_empty_input(self):
        result = to_posting_list_response([])

        assert result.postings == []

    def test_success_flag_is_true(self):
        result = to_posting_list_response([])

        assert result.success is True
