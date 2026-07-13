"""Presentation helpers for the posting API.

Transforms service-layer view models into the HTTP response schemas
returned by the posting endpoints. This module defines the translation
between the application layer and the public API contract without
introducing business rules or transport-specific logic.
"""

from pyledger.core.posting.dtos import PostingViewModel

from .schemas import PostingItem, PostingListResponse


def to_posting_item(view_model: PostingViewModel) -> PostingItem:
    """Convert a posting view model into its HTTP representation.

    Args:
        view_model: The posting produced by the application layer.

    Returns:
        The corresponding API response model.
    """
    return PostingItem(
        account=view_model.account,
        debit_amount=view_model.debit_amount,
        credit_amount=view_model.credit_amount,
        journal_number=view_model.journal_number,
        posting_date=view_model.posting_date,
        is_debit=view_model.is_debit,
    )


def to_posting_list_response(
    view_models: list[PostingViewModel],
) -> PostingListResponse:
    """Convert multiple posting view models into the API response envelope.

    Preserves the order of the supplied postings while wrapping them in
    the feature's standard success response.

    Args:
        view_models: The postings produced by the application layer.

    Returns:
        A successful response containing the mapped postings.
    """
    return PostingListResponse(postings=[to_posting_item(vm) for vm in view_models])
