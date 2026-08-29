"""Request Schema -> Input DTO mapping for the journal feature.

Pure, synchronous, no I/O, no business rules -- per
`Trutina API Feature & Testing Prompt` Section 2/3.
`CreateJournalEntryRequest`/`JournalLineRequest` were deliberately built
to mirror `CreateJournalInput`/`JournalLineInput` field-for-field (see
`schemas.py`), so this is thin construction. Accounting validation
(account existence, balance, debit/credit exclusivity) fires later,
inside `JournalService.create_journal_entry()`.
"""

from trutina.core.journal.dtos import CreateJournalInput, JournalLineInput

from .schemas import CreateJournalEntryRequest, JournalLineRequest


def _to_journal_line_input(line: JournalLineRequest) -> JournalLineInput:
    """Map a single request line to its Input DTO counterpart."""
    return JournalLineInput(
        account=line.account,
        debit_amount=line.debit_amount,
        credit_amount=line.credit_amount,
    )


def to_create_journal_input(request: CreateJournalEntryRequest) -> CreateJournalInput:
    """Map a create request body to the service's Input DTO.

    Args:
        request: The validated ``POST /journal-entries`` request body.

    Returns:
        The ``CreateJournalInput`` ready to pass into
        ``JournalService.create_journal_entry()``.
    """
    return CreateJournalInput(
        posting_date=request.posting_date,
        lines=[_to_journal_line_input(line) for line in request.lines],
        description=request.description,
    )
