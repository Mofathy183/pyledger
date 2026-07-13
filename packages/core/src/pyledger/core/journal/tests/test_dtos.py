from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError
from pyledger.core.journal import (
    CreateJournalInput,
    JournalLineInput,
    JournalLineViewModel,
    JournalViewModel,
)
from pyledger.shared.errors import ErrorCode


@pytest.mark.unit
class TestJournalLineInput:
    def test_accepts_valid_input(self):
        line = JournalLineInput(
            account="Cash",
            debit_amount=Decimal("100.00"),
            credit_amount=Decimal("0"),
        )

        assert line.account == "Cash"
        assert line.debit_amount == Decimal("100.00")
        assert line.credit_amount == Decimal("0")

    def test_raises_validation_error_when_account_is_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            JournalLineInput(account="A")

        assert any(
            error["type"] == ErrorCode.STRING_TOO_SHORT
            for error in exc_info.value.errors()
        )

    def test_raises_validation_error_when_account_is_too_long(self):
        account = "A" * 101

        with pytest.raises(ValidationError) as exc_info:
            JournalLineInput(account=account)

        assert any(
            error["type"] == ErrorCode.STRING_TOO_LONG
            for error in exc_info.value.errors()
        )

    @pytest.mark.parametrize(
        "field_name, value",
        [
            ("debit_amount", Decimal("-1.00")),
            ("credit_amount", Decimal("-1.00")),
        ],
    )
    def test_raises_validation_error_when_amount_is_negative(
        self,
        field_name,
        value,
    ):
        data = {
            "account": "Cash",
            "debit_amount": Decimal("0"),
            "credit_amount": Decimal("0"),
        }
        data[field_name] = value

        with pytest.raises(ValidationError) as exc_info:
            JournalLineInput(**data)

        assert any(
            error["type"] == ErrorCode.GREATER_THAN_EQUAL
            for error in exc_info.value.errors()
        )


@pytest.mark.unit
class TestCreateJournalInput:
    def test_accepts_valid_input(self):
        journal = CreateJournalInput(
            posting_date=datetime(2025, 1, 1),
            lines=[
                JournalLineInput(
                    account="Cash",
                    debit_amount=Decimal("100.00"),
                ),
                JournalLineInput(
                    account="Revenue",
                    credit_amount=Decimal("100.00"),
                ),
            ],
            description="Sale transaction",
        )

        assert len(journal.lines) == 2
        assert journal.description == "Sale transaction"

    def test_raises_validation_error_when_less_than_two_lines_are_provided(self):
        with pytest.raises(ValidationError) as exc_info:
            CreateJournalInput(
                posting_date=datetime(2025, 1, 1),
                lines=[
                    JournalLineInput(
                        account="Cash",
                        debit_amount=Decimal("100.00"),
                    )
                ],
            )

        assert any(
            error["type"] == ErrorCode.TOO_SHORT for error in exc_info.value.errors()
        )

    def test_accepts_none_description(self):
        journal = CreateJournalInput(
            posting_date=datetime(2025, 1, 1),
            lines=[
                JournalLineInput(
                    account="Cash",
                    debit_amount=Decimal("100.00"),
                ),
                JournalLineInput(
                    account="Revenue",
                    credit_amount=Decimal("100.00"),
                ),
            ],
            description=None,
        )

        assert journal.description is None

    def test_accepts_omitted_description(self):
        journal = CreateJournalInput(
            posting_date=datetime(2025, 1, 1),
            lines=[
                JournalLineInput(
                    account="Cash",
                    debit_amount=Decimal("100.00"),
                ),
                JournalLineInput(
                    account="Revenue",
                    credit_amount=Decimal("100.00"),
                ),
            ],
        )

        assert journal.description is None

    def test_accepts_description_when_provided(self):
        journal = CreateJournalInput(
            posting_date=datetime(2025, 1, 1),
            lines=[
                JournalLineInput(
                    account="Cash",
                    debit_amount=Decimal("100.00"),
                ),
                JournalLineInput(
                    account="Revenue",
                    credit_amount=Decimal("100.00"),
                ),
            ],
            description="Monthly closing entry",
        )

        assert journal.description == "Monthly closing entry"

    def test_raises_validation_error_when_description_exceeds_max_length(self):
        description = "A" * 256

        with pytest.raises(ValidationError) as exc_info:
            CreateJournalInput(
                posting_date=datetime(2025, 1, 1),
                lines=[
                    JournalLineInput(
                        account="Cash",
                        debit_amount=Decimal("100.00"),
                    ),
                    JournalLineInput(
                        account="Revenue",
                        credit_amount=Decimal("100.00"),
                    ),
                ],
                description=description,
            )

        assert any(
            error["type"] == ErrorCode.STRING_TOO_LONG
            for error in exc_info.value.errors()
        )


@pytest.mark.unit
class TestJournalLineViewModel:
    def test_creates_journal_line_view_model(self):
        line = JournalLineViewModel(
            account="Cash",
            debit_amount=Decimal("100.00"),
            credit_amount=Decimal("0"),
        )

        assert line.account == "Cash"
        assert line.debit_amount == Decimal("100.00")
        assert line.credit_amount == Decimal("0")


@pytest.mark.unit
class TestJournalViewModel:
    def test_creates_journal_view_model(self):
        journal = JournalViewModel(
            journal_number=1,
            posting_date=datetime(2025, 1, 1),
            description="Sale transaction",
            lines=[
                JournalLineViewModel(
                    account="Cash",
                    debit_amount=Decimal("100.00"),
                    credit_amount=Decimal("0"),
                ),
                JournalLineViewModel(
                    account="Revenue",
                    debit_amount=Decimal("0"),
                    credit_amount=Decimal("100.00"),
                ),
            ],
            total_debits=Decimal("100.00"),
            total_credits=Decimal("100.00"),
            is_balanced=True,
        )

        assert journal.journal_number == 1
        assert journal.total_debits == Decimal("100.00")
        assert journal.total_credits == Decimal("100.00")
        assert journal.is_balanced is True
        assert len(journal.lines) == 2
