"""ViewModel -> Response Schema mapping for the journal feature.

Pure, synchronous, no I/O, no business rules -- mirrors the account
feature's ``presenter.py``. Each function turns an already-fetched
``JournalViewModel``/``list[JournalViewModel]`` into its public HTTP
response shape; it never calls a service.
"""

from pyledger.core.journal.dtos import JournalLineViewModel, JournalViewModel

from .schemas import (
    JournalEntriesResponse,
    JournalEntryData,
    JournalEntryResponse,
    JournalLineData,
)


def _to_journal_line_data(line: JournalLineViewModel) -> JournalLineData:
    """Map a single JournalLineViewModel to its wire-level shape."""
    return JournalLineData(
        account=line.account,
        debit_amount=line.debit_amount,
        credit_amount=line.credit_amount,
    )


def _to_journal_entry_data(view_model: JournalViewModel) -> JournalEntryData:
    """Map a JournalViewModel to its wire-level JournalEntryData shape."""
    return JournalEntryData(
        journal_number=view_model.journal_number,
        posting_date=view_model.posting_date,
        description=view_model.description,
        lines=[_to_journal_line_data(line) for line in view_model.lines],
        total_debits=view_model.total_debits,
        total_credits=view_model.total_credits,
        is_balanced=view_model.is_balanced,
    )


def to_journal_entry_response(view_model: JournalViewModel) -> JournalEntryResponse:
    """Build the response envelope for a single-entry result.

    Used by create and get -- both return one ``JournalViewModel`` from
    the service.

    Args:
        view_model: The service's view model for one journal entry.

    Returns:
        The response body for ``POST /journal-entries`` and
        ``GET /journal-entries/{journal_number}``.
    """
    return JournalEntryResponse(entry=_to_journal_entry_data(view_model))


def to_journal_entries_response(
    view_models: list[JournalViewModel],
) -> JournalEntriesResponse:
    """Build the response envelope for the full journal-entries listing.

    Args:
        view_models: The service's list of journal-entry view models.

    Returns:
        The response body for ``GET /journal-entries``.
    """
    return JournalEntriesResponse(
        entries=[_to_journal_entry_data(vm) for vm in view_models]
    )
