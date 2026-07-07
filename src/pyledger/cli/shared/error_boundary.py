"""
Command-layer error boundary for the PyLedger CLI.

Wraps a single service-layer call site (invoked via AppState.call())
and translates AppError / ValidationAppError into rendered Rich panels
plus a clean typer.Exit, so command.py bodies never handle exception
formatting or exit codes themselves.

This module is the only place that combines the pure error-formatting
functions in cli/shared/formatters/error.py with actual terminal output
(via cli/shared/ui/console) and the CLI's exit-code contract. It sits
above shared/errors/, shared/formatters/, and shared/ui/ rather than
inside any one of them, since it depends on all three.
"""

from collections.abc import Iterator
from contextlib import contextmanager

import typer
from pydantic import ValidationError

from pyledger.cli.shared.formatters.error import (
    build_error_panels,
    format_app_error,
    format_validation_app_error,
    format_validation_errors,
)
from pyledger.cli.shared.ui import console
from pyledger.shared.errors import AppError, ValidationAppError


@contextmanager
def error_boundary() -> Iterator[None]:
    """Render service-layer errors as panels and exit(1) instead of propagating.

    Scopes exactly the one state.call(...) invocation that can raise
    AppError or ValidationAppError. ValidationAppError is caught first
    since it is a subclass of AppError, and is formatted through
    format_validation_app_error() so each FieldViolation renders as its
    own panel; a bare AppError renders as a single panel via
    format_app_error(). Both paths end in typer.Exit(code=1) so the
    command process exits cleanly rather than dumping a raw traceback.

    Usage:

        with error_boundary():
            account_vm = state.call(create_account_handler, state.context, dto)

    Raises:
        typer.Exit: Code 1, if the wrapped block raises AppError or
            ValidationAppError. The error has already been rendered to
            the console before this is raised.
    """
    try:
        yield
    except ValidationAppError as exc:
        for p in build_error_panels(format_validation_app_error(exc)):
            console.print(p)
        raise typer.Exit(code=1) from None
    except AppError as exc:
        for p in build_error_panels([format_app_error(exc)]):
            console.print(p)
        raise typer.Exit(code=1) from None
    except ValidationError as exc:
        for p in build_error_panels(format_validation_errors(exc)):
            console.print(p)
        raise typer.Exit(code=1) from None
