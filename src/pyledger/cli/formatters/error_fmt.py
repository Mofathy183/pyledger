"""
Validation error formatting for the PyLedger CLI.

Translates Pydantic ValidationError instances and service-layer
AppError instances into display-ready structures and renders them as
Rich panels. Hint and field label resolution happens here — these are
CLI-only presentation concerns and must not live in shared/.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from pyledger.cli.console import console
from pyledger.cli.constants import ERRORS, FIELD_LABELS, HINTS
from pyledger.cli.formatters.base import console_panel
from pyledger.shared.errors import AppError
from pyledger.shared.errors.codes import ErrorCode


@dataclass(frozen=True)
class FormattedError:
    """Validation error prepared for terminal rendering.

    This is a CLI-only construct. It carries the display field,
    the resolved error message, and the corrective hint.
    """

    field: str
    message: str
    code: str
    hint: str


def _resolve_field(error: Mapping[str, Any]) -> str:
    """Resolve a display field name for a Pydantic error.

    Prefers the dotted location path Pydantic provides. Falls back to
    a CLI-owned label when loc is empty, e.g. for model-level
    validators that don't target a single field.

    Args:
        error: A single error dict from ValidationError.errors().

    Returns:
        A display-ready field name.
    """
    loc = ".".join(map(str, error.get("loc", [])))
    if loc:
        return loc
    return FIELD_LABELS.get(error["type"], "unknown")


def format_validation_errors(exc: ValidationError) -> list[FormattedError]:
    """Convert a Pydantic ValidationError into display-ready errors.

    Args:
        exc: The ValidationError raised during model construction.

    Returns:
        List of FormattedError ready for print_errors().
    """
    result = []
    for error in exc.errors():
        error_type = error["type"]
        detail = ERRORS.get(error_type, ERRORS[ErrorCode.UNKNOWN_ERROR])
        hint = HINTS.get(error_type, HINTS[ErrorCode.UNKNOWN_ERROR])

        result.append(
            FormattedError(
                field=_resolve_field(error),
                message=detail.message,
                code=detail.code,
                hint=hint,
            )
        )
    return result


def format_app_error(exc: AppError) -> FormattedError:
    """Convert a service-layer AppError into a display-ready error.

    AppError carries only a code and a context dict — message and
    hint are resolved here, from the CLI's own lookup tables, the
    same way they're resolved for Pydantic errors. This keeps AppError
    itself free of any CLI-specific wording.

    Args:
        exc: The AppError raised by a service method.

    Returns:
        A single FormattedError ready for print_errors().
    """
    detail = ERRORS.get(exc.code, ERRORS[ErrorCode.UNKNOWN_ERROR])
    hint = HINTS.get(exc.code, HINTS[ErrorCode.UNKNOWN_ERROR])
    field = exc.context.get("field", FIELD_LABELS.get(exc.code, "unknown"))

    return FormattedError(
        field=field,
        message=detail.message,
        code=detail.code,
        hint=hint,
    )


def print_errors(errors: list[FormattedError]) -> None:
    """Render a list of FormattedErrors as Rich panels to the terminal."""
    for error in errors:
        content = (
            f"Field:   {error.field}\n"
            f"Message: {error.message}\n"
            f"Code:    [warning]{error.code}[/]\n\n"
            f"Hint:\n  [info]{error.hint}[/]"
        )
        console.print(console_panel(content, title="Validation Error", style="error"))
