"""Router for the journal feature.

Follows the project's fixed request workflow:

    HTTP Request -> Router -> Request Schema -> Mapper -> Input DTO ->
    Handler -> Service -> ViewModel -> Presenter -> Response Schema ->
    HTTP Response

Each route below does exactly: resolve the Mapper, call the Handler via
``Depends(get_journal_service)``, resolve the Presenter, return. No
route contains business logic, constructs a domain model, or catches
``AppError``/``ValidationAppError`` -- those propagate uncaught to
``api/shared/errors/handlers.py``, registered once in
``api/composition/app.py::create_app()``.

Prefixed under ``/journal-entries``, matching the resource-per-router
convention the ``account`` router already establishes.
"""

from fastapi import APIRouter, Depends, status
from pyledger.api.composition.dependencies import get_journal_service
from pyledger.core.journal.service import JournalService

from . import handler
from .mapper import to_create_journal_input
from .presenter import to_journal_entries_response, to_journal_entry_response
from .schemas import (
    CreateJournalEntryRequest,
    JournalEntriesResponse,
    JournalEntryResponse,
)

router = APIRouter(prefix="/journal-entries", tags=["journal-entries"])


@router.post(
    "", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED
)
async def create_journal_entry(
    request: CreateJournalEntryRequest,
    service: JournalService = Depends(get_journal_service),
) -> JournalEntryResponse:
    """Create a new journal entry.

    Raises:
        AppError: UNKNOWN_ACCOUNT (translated to 404 by the registered
            exception handlers).
        ValidationAppError: VALIDATION_ERROR (translated to 422).
    """
    dto = to_create_journal_input(request)
    view_model = await handler.create_journal_entry(service, dto)
    return to_journal_entry_response(view_model)


@router.get("", response_model=JournalEntriesResponse)
async def list_journal_entries(
    service: JournalService = Depends(get_journal_service),
) -> JournalEntriesResponse:
    """Return every persisted journal entry."""
    view_models = await handler.list_journal_entries(service)
    return to_journal_entries_response(view_models)


@router.get("/{journal_number}", response_model=JournalEntryResponse)
async def get_journal_entry(
    journal_number: int,
    service: JournalService = Depends(get_journal_service),
) -> JournalEntryResponse:
    """Fetch a single journal entry by its journal number.

    Raises:
        AppError: UNKNOWN_JOURNAL_ENTRY (translated to 404).
    """
    view_model = await handler.get_journal_entry(service, journal_number)
    return to_journal_entry_response(view_model)
