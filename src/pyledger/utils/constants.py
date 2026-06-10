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

from pyledger.core.errors import ErrorCode

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
    ErrorCode.GREATER_THAN: "Provide a value that is above the minimum allowed.",
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
