"""
Centralized validation and domain error definitions.

This module provides structured error metadata used throughout
PyLedger. Validation logic raises domain-specific error identifiers,
which are then mapped to user-friendly messages and corrective guidance.

Keeping error definitions centralized ensures consistency across CLI
commands, domain models, and future application interfaces.
"""

from dataclasses import dataclass
from enum import StrEnum

from pydantic_core import PydanticCustomError


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

    The human-readable message associated with an error may change
    over time, but the error code should remain stable.
    """

    #
    # Generic validation
    #
    UNKNOWN_ERROR = "unknown_error"
    REQUIRED_FIELD = "missing"
    INVALID_NUMBER = "int_parsing"
    INVALID_DECIMAL = "decimal_parsing"
    STRING_TOO_SHORT = "string_too_short"
    STRING_TOO_LONG = "string_too_long"
    TOO_SHORT = "too_short"
    TOO_LONG = "too_long"
    GREATER_THAN = "greater_than"
    GREATER_THAN_EQUAL = "greater_than_equal"
    LESS_THAN_EQUAL = "less_than_equal"

    #
    # Domain errors — posting date
    #
    FUTURE_DATE = "future_date"
    PAST_DATE = "past_date"

    #
    # Domain errors — account names
    #
    INVALID_ACCOUNT_NAME = "invalid_account_name"
    UNKNOWN_ACCOUNT = "UNKNOWN_ACCOUNT"
    #
    # Domain errors — journal lines
    #
    INVALID_LINE_AMOUNTS = "invalid_line_amounts"

    #
    # Domain errors — journal entry
    #
    UNBALANCED_ENTRY = "unbalanced_entry"


@dataclass(frozen=True, slots=True)
class ErrorDetail:
    """Represents a user-facing validation error message.

    Attributes:
        code: Stable machine-readable error identifier.
        message: Human-readable explanation of the validation failure.
    """

    code: ErrorCode
    message: str


@dataclass(frozen=True, slots=True)
class Error:
    detail: ErrorDetail
    hint: str


type ErrorMap = dict[str, ErrorDetail]
"""
Maps a validation error type to its user-facing metadata.

The key is the Pydantic error type string or custom domain error
identifier raised by the validator. The value is the ErrorDetail
describing the failure.

Keying by error type rather than field name means this map remains
valid as the domain model evolves. Dynamic field paths such as
``lines.0.account`` or ``lines.3.credit_amount`` resolve to the same
error type regardless of their position, so no updates to this map
are required when the model structure changes.
"""
ERRORS: ErrorMap = {
    #
    # Generic validation
    #
    ErrorCode.UNKNOWN_ERROR: ErrorDetail(
        code=ErrorCode.UNKNOWN_ERROR,
        message="An unexpected validation error occurred.",
    ),
    ErrorCode.REQUIRED_FIELD: ErrorDetail(
        code=ErrorCode.REQUIRED_FIELD,
        message="This field is required.",
    ),
    ErrorCode.INVALID_NUMBER: ErrorDetail(
        code=ErrorCode.INVALID_NUMBER,
        message="The journal number must be a valid number.",
    ),
    ErrorCode.INVALID_DECIMAL: ErrorDetail(
        code=ErrorCode.INVALID_DECIMAL,
        message="A valid decimal amount is required.",
    ),
    ErrorCode.STRING_TOO_SHORT: ErrorDetail(
        code=ErrorCode.STRING_TOO_SHORT,
        message="The value is too short.",
    ),
    ErrorCode.STRING_TOO_LONG: ErrorDetail(
        code=ErrorCode.STRING_TOO_LONG,
        message="The value exceeds the allowed length.",
    ),
    ErrorCode.TOO_SHORT: ErrorDetail(
        code=ErrorCode.TOO_SHORT,
        message="The list does not meet the minimum required length.",
    ),
    ErrorCode.TOO_LONG: ErrorDetail(
        code=ErrorCode.TOO_LONG,
        message="The list exceeds the maximum allowed length.",
    ),
    ErrorCode.GREATER_THAN: ErrorDetail(
        code=ErrorCode.GREATER_THAN,
        message="The value is below the minimum allowed value.",
    ),
    ErrorCode.GREATER_THAN_EQUAL: ErrorDetail(
        code=ErrorCode.GREATER_THAN_EQUAL,
        message="The value must be at or above the minimum allowed value.",
    ),
    ErrorCode.LESS_THAN_EQUAL: ErrorDetail(
        code=ErrorCode.LESS_THAN_EQUAL,
        message="The value exceeds the allowed limit.",
    ),
    #
    # Posting date
    #
    ErrorCode.FUTURE_DATE: ErrorDetail(
        code=ErrorCode.FUTURE_DATE,
        message="The posting date cannot be in the future.",
    ),
    ErrorCode.PAST_DATE: ErrorDetail(
        code=ErrorCode.PAST_DATE,
        message="The posting date is outside the supported accounting period.",
    ),
    #
    # Account names
    #
    ErrorCode.INVALID_ACCOUNT_NAME: ErrorDetail(
        code=ErrorCode.INVALID_ACCOUNT_NAME,
        message="Account names can only contain letters, spaces, commas, and '/'.",
    ),
    ErrorCode.UNKNOWN_ACCOUNT: ErrorDetail(
        code=ErrorCode.UNKNOWN_ACCOUNT,
        message="The referenced account does not exist in the chart of accounts.",
    ),
    #
    # Journal lines
    #
    ErrorCode.INVALID_LINE_AMOUNTS: ErrorDetail(
        code=ErrorCode.INVALID_LINE_AMOUNTS,
        message=(
            "A journal line must contain either a debit amount or a credit amount, "
            "not both and not neither."
        ),
    ),
    #
    # Journal entry
    #
    ErrorCode.UNBALANCED_ENTRY: ErrorDetail(
        code=ErrorCode.UNBALANCED_ENTRY,
        message="The journal entry is not balanced. Total debits must equal total credits.",
    ),
}


def validation_error(code: ErrorCode) -> PydanticCustomError:
    """Construct a Pydantic-compatible domain validation error.

    Wraps a domain error code in a PydanticCustomError so validators
    can raise it directly. The error message is intentionally empty
    because user-facing messages are resolved from ERRORS at the
    presentation layer rather than embedded in the exception.

    Args:
        code: The domain error code identifying the validation failure.

    Returns:
        A PydanticCustomError carrying the error code as its type.
    """
    # noinspection PyTypeChecker
    return PydanticCustomError(code, "")
