"""
Centralized validation and domain error definitions.

This module provides structured error metadata used throughout
PyLedger. Validation logic raises domain-specific error identifiers,
which are then mapped to user-friendly messages and corrective guidance.

Keeping error definitions centralized ensures consistency across CLI
commands, domain models, and future application interfaces.
"""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class ErrorCode(StrEnum):
    """Stable application error identifiers.

    Error codes provide a machine-readable representation of validation
    and domain failures. Unlike user-facing messages, error codes are
    intended to remain stable and can be safely used for:

    - Testing and assertions
    - Error mapping
    - Future API responses
    - Logging and diagnostics
    - Localization of user-facing messages

    The human-readable message and hint associated with an error may
    change over time, but the error code should remain stable.
    """

    # Journal number
    INVALID_NUMBER = "invalid_number"

    # Posting date
    FUTURE_DATE = "future_date"
    PAST_DATE = "past_date"

    # Account names
    INVALID_ACCOUNT_NAME = "invalid_account_name"
    TOO_SHORT_DEBIT_ACCOUNT = "too_short_debit_account"
    TOO_SHORT_CREDIT_ACCOUNT = "too_short_credit_account"

    # Balances
    UNBALANCED_ENTRY = "unbalanced_entry"


@dataclass(frozen=True)
class ErrorDetail:
    """Represents a user-facing validation error.

    Attributes:
        code: Stable machine-readable error identifier.
        message: Human-readable explanation of the validation failure.
        hint: Guidance that helps the user resolve the issue.
    """

    code: ErrorCode
    message: str
    hint: str


type ErrorMap = dict[str, dict[str, ErrorDetail]]
"""
Maps validation errors to user-facing metadata.

Structure:

    {
        field_name: {
            validation_error_type: ErrorDetail
        }
    }

The outer key typically corresponds to a domain model field, while
the inner key corresponds to a Pydantic validation error type or
custom application error identifier.
"""


JOURNAL_ENTRY_ERRORS: ErrorMap = {
    "journal_number": {
        "int_parsing": ErrorDetail(
            message="The posting number must be a number",
            code=ErrorCode.INVALID_NUMBER,
            hint=(
                "you must add a number for the journal entry, "
                "[underline]or skip and we'll add it 😁, 👍 .[/]"
            ),
        )
    },
    "posting_date": {
        "less_than_equal": ErrorDetail(
            message=(
                "the date must not in the Future, "
                f"you can't post a journal in the 2050 and we in {date.today().year}"
            ),
            code=ErrorCode.FUTURE_DATE,
            hint=(
                "Try to add a date in the current year, not in the future, "
                "[underline]or skip it and we'll add it 😁, 👍 .[/]"
            ),
        ),
        "greater_than": ErrorDetail(
            message=(
                "the date must not in the Past, "
                f"you can't post a journal in the 2020 and we in {date.today().year}"
            ),
            code=ErrorCode.PAST_DATE,
            hint=(
                "Try to add a date in the current year, not in the Past, "
                "[underline]or skip it and we'll add it 😁, 👍 .[/]"
            ),
        ),
    },
    "debit_account": {
        "string_too_short": ErrorDetail(
            message=(
                "There is no debit account with one letter, "
                "so pleases try to add the account name or its abbreviations at least."
            ),
            code=ErrorCode.TOO_SHORT_DEBIT_ACCOUNT,
            hint=(
                "Try to add the full name of the account or abbreviations of it 😌, 😐, "
                "Like Account Receivable or its abbreviations A/R."
            ),
        ),
    },
    "credit_account": {
        "string_too_short": ErrorDetail(
            message=(
                "There is no credit account with one letter, "
                "so pleases try to add the account name or its abbreviations at least."
            ),
            code=ErrorCode.TOO_SHORT_CREDIT_ACCOUNT,
            hint=(
                "Try to add the full name of the account or abbreviations of it 😌, 😐, "
                "Like Account Payable or its abbreviations A/P."
            ),
        ),
    },
    "account_name": {
        "invalid_account_name": ErrorDetail(
            message="Account names can only contain letters, spaces, / and commas.",
            code=ErrorCode.INVALID_ACCOUNT_NAME,
            hint=(
                "Try using normal account names like Cash or abbreviations "
                "like A/R 😌, not symbols or random characters."
            ),
        ),
    },
    "balances": {
        "balances_not_equal": ErrorDetail(
            message="Debit balance must equal credit balance.",
            code=ErrorCode.UNBALANCED_ENTRY,
            hint=(
                "Every journal entry must stay balanced "
                "according to the double-entry accounting system."
            ),
        ),
    },
}
