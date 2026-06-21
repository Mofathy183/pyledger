from decimal import Decimal

import pytest

from pyledger.modules.journal.schemas.journal import JournalEntry
from pyledger.modules.journal.schemas.line import JournalLine
from tests.factories import make_credit_line, make_debit_line, make_journal_entry


@pytest.fixture
def debit_line() -> JournalLine:
    return make_debit_line()


@pytest.fixture
def credit_line() -> JournalLine:
    return make_credit_line()


@pytest.fixture
def balanced_lines() -> list[JournalLine]:
    return [
        make_debit_line(amount=Decimal("100")),
        make_credit_line(amount=Decimal("100")),
    ]


@pytest.fixture
def journal_entry() -> JournalEntry:
    return make_journal_entry()
