from datetime import datetime
from decimal import Decimal

import pytest
from pyledger.core.posting.dtos import PostingViewModel


@pytest.mark.unit
class TestPostingViewModel:
    def test_creates_view_model(self):
        vm = PostingViewModel(
            account="Cash",
            debit_amount=Decimal("100.00"),
            credit_amount=None,
            journal_number=1,
            posting_date=datetime(2025, 1, 1),
        )

        assert vm.account == "Cash"
        assert vm.debit_amount == Decimal("100.00")
        assert vm.credit_amount is None
        assert vm.journal_number == 1
        assert vm.posting_date == datetime(2025, 1, 1)

    @pytest.mark.parametrize(
        ("debit_amount", "credit_amount", "expected"),
        [
            (Decimal("100.00"), None, True),
            (None, Decimal("100.00"), False),
        ],
    )
    def test_calculates_is_debit(
        self,
        debit_amount,
        credit_amount,
        expected,
    ):
        vm = PostingViewModel(
            account="Cash",
            debit_amount=debit_amount,
            credit_amount=credit_amount,
            journal_number=1,
            posting_date=datetime(2025, 1, 1),
        )

        assert vm.is_debit is expected
