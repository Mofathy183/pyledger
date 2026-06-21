from dataclasses import dataclass

from pyledger.shared.errors import ErrorCode


@dataclass(frozen=True, slots=True)
class ErrorDetail:
    """Represents a user-facing validation error message.

    Attributes:
        code: Stable machine-readable error identifier.
        message: Human-readable explanation of the validation failure.
    """

    code: ErrorCode
    message: str


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

"""
User-facing resolution hints for validation errors.

This module provides actionable guidance that helps users correct
validation failures. Hints are intentionally kept separate from error
messages so that message copy and resolution guidance can be updated
independently.

Like the error map, hints are keyed by error type rather than field
name. This ensures hints remain valid as the domain model evolves and
dynamic field paths such as ``lines.0.account`` are handled without
any changes to this file.
"""

type HintMap = dict[str, str]
"""
Maps a validation error type to a plain-text resolution hint.

Keys match the error type strings in ``ERRORS`` from. Values are plain text with no
Rich markup. Markup is applied by the formatter at display time.
"""


HINTS: HintMap = {
    #
    # Generic validation
    #
    ErrorCode.UNKNOWN_ERROR: (
        "An unexpected validation error occurred. Check the field value and try again."
    ),
    ErrorCode.REQUIRED_FIELD: "Provide a value for this field before continuing.",
    ErrorCode.INVALID_NUMBER: (
        "Enter a whole number for the journal entry, "
        "or leave it blank and one will be assigned automatically."
    ),
    ErrorCode.INVALID_DECIMAL: "Enter a monetary amount such as 100 or 100.50.",
    ErrorCode.STRING_TOO_SHORT: "Provide a longer value.",
    ErrorCode.STRING_TOO_LONG: "Shorten the value and try again.",
    ErrorCode.TOO_SHORT: "Provide at least the minimum number of items required.",
    ErrorCode.TOO_LONG: "Remove items until the list meets the maximum allowed length.",
    ErrorCode.GREATER_THAN: "Provide a value that is above the minimum allowed.",
    ErrorCode.GREATER_THAN_EQUAL: (
        "Provide a value that meets or exceeds the minimum allowed."
    ),
    ErrorCode.LESS_THAN_EQUAL: (
        "Provide a value that does not exceed the allowed limit."
    ),
    #
    # Posting date
    #
    ErrorCode.FUTURE_DATE: (
        "Use today's date or a date in the past. "
        "Leave it blank and today's date will be used automatically."
    ),
    ErrorCode.PAST_DATE: (
        "Use a more recent posting date. "
        "Dates before 2020 are outside the supported accounting period."
    ),
    #
    # Account names
    #
    ErrorCode.INVALID_ACCOUNT_NAME: (
        "Use the full account name or a recognised abbreviation, "
        "such as Cash, Accounts Receivable, or A/R. "
        "Numbers and special characters are not allowed."
    ),
    ErrorCode.UNKNOWN_ACCOUNT: (
        "This account does not exist in the chart of accounts. "
        "Use an existing account name or alias, or add the account "
        "to the chart of accounts before posting."
    ),
    #
    # Journal lines
    #
    ErrorCode.INVALID_LINE_AMOUNTS: (
        "Set either the debit amount or the credit amount to a value "
        "greater than zero. A single line cannot carry both a debit and "
        "a credit, and it cannot carry neither."
    ),
    #
    # Journal entry
    #
    ErrorCode.UNBALANCED_ENTRY: (
        "Check that the total of all debit amounts equals the total of "
        "all credit amounts across every line in the entry."
    ),
}

FIELD_LABELS: dict[str, str] = {
    ErrorCode.UNBALANCED_ENTRY: "lines (balance)",
    ErrorCode.INVALID_LINE_AMOUNTS: "lines (amounts)",
    ErrorCode.FUTURE_DATE: "posting_date",
    ErrorCode.DUPLICATE_ACCOUNT_CODE: "Account Code",
}
