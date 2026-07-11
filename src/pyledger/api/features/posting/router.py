"""HTTP routes for the posting feature.

Exposes endpoints for posting journal entries and retrieving the
resulting ledger postings. Each route translates HTTP input into the
application layer, delegates the requested workflow to
``PostingService``, and returns the corresponding HTTP response
contract.
"""

from fastapi import APIRouter, Depends, Path, status

from pyledger.api.composition.dependencies import get_posting_service
from pyledger.modules.posting.service import PostingService

from .handler import (
    get_postings_by_account_handler,
    get_postings_by_journal_number_handler,
    post_journal_entry_handler,
)
from .mapper import to_account, to_journal_number
from .presenter import to_posting_list_response
from .schemas import PostingListResponse

router = APIRouter(prefix="/postings", tags=["postings"])


@router.post(
    "/{journal_number}",
    response_model=PostingListResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_journal_entry(
    journal_number: int = Path(gt=0, description="The journal number to post."),
    service: PostingService = Depends(get_posting_service),
) -> PostingListResponse:
    """Post a journal entry and return the derived ledger postings.

    Posting converts a balanced journal entry into the immutable ledger
    by creating one posting for each journal line.

    Args:
        journal_number: The journal entry to post.
        service: The posting service.

    Returns:
        The postings derived from the journal entry.
    """
    mapped_number = to_journal_number(journal_number)
    postings = await post_journal_entry_handler(service, mapped_number)
    return to_posting_list_response(postings)


@router.get(
    "/by-account/{account}",
    response_model=PostingListResponse,
)
async def get_postings_by_account(
    account: str = Path(
        min_length=2, max_length=100, description="Account name to look up."
    ),
    service: PostingService = Depends(get_posting_service),
) -> PostingListResponse:
    """Retrieve the ledger postings recorded against an account.

    Args:
        account: The account whose posting history should be retrieved.
        service: The posting service.

    Returns:
        The postings recorded against the requested account.
    """
    mapped_account = to_account(account)
    postings = await get_postings_by_account_handler(service, mapped_account)
    return to_posting_list_response(postings)


@router.get(
    "/by-journal/{journal_number}",
    response_model=PostingListResponse,
)
async def get_postings_by_journal_number(
    journal_number: int = Path(gt=0, description="Journal number to look up."),
    service: PostingService = Depends(get_posting_service),
) -> PostingListResponse:
    """Retrieve the postings derived from a journal entry.

    Args:
        journal_number: The journal entry whose postings should be retrieved.
        service: The posting service.

    Returns:
        The postings derived from the requested journal entry.
    """
    mapped_number = to_journal_number(journal_number)
    postings = await get_postings_by_journal_number_handler(service, mapped_number)
    return to_posting_list_response(postings)
