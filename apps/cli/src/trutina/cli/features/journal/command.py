"""Typer command group for journal-entry management.

Commands in this module are the CLI's presentation-adapter layer: they
resolve raw input (CLI flags or interactive prompts) into a validated
DTO, hand that DTO to a handler for the actual use case, and render the
result. Commands never call JournalService directly and never construct
domain models — both belong to handler.py and the service layer
respectively. Commands never print Rich markup directly either — every
user-facing message is composed in formatter.py.

Unlike account_cmd, this group exposes only ``create``, ``get``, and
``list`` — JournalService has no update or delete workflow, so no
corresponding commands exist here. Inventing them would add business
logic the service layer doesn't support.
"""

from typing import Annotated

import typer
from trutina.cli.composition.state import CliState
from trutina.cli.shared.boundary.error_boundary import error_boundary

from .formatter import print_journal_entry, print_journal_list
from .handler import (
    create_journal_entry_handler,
    get_journal_entry_handler,
    list_journal_entries_handler,
)
from .parser import parse_create_journal, parse_line_spec
from .prompt import prompt_create_journal, prompt_journal_number

app = typer.Typer(
    help="Manage journal entries.",
    name="journal",
)

_LINE_HELP = (
    "A journal line as 'Account:Debit:Credit', e.g. 'Cash:100:0'. "
    "Repeat for each line; at least two are required."
)


@app.command("create")
def create(
    ctx: typer.Context,
    posting_date: Annotated[
        str | None,
        typer.Option(help="Posting date, YYYY-MM-DD. Defaults to today if omitted."),
    ] = None,
    description: Annotated[
        str | None, typer.Option(help="Optional short description.")
    ] = None,
    line: Annotated[
        list[str] | None,
        typer.Option("--line", help=_LINE_HELP),
    ] = None,
) -> None:
    """Create a new journal entry.

    Supports two input modes:

    - Explicit CLI arguments: one or more repeated ``--line`` options
        (at least two required), plus optional ``--posting-date`` and
        ``--description``.
    - Fully interactive prompts, when no ``--line`` option is supplied.

    Unlike ``account create``, only the presence of ``--line`` decides
    between the two modes — ``--posting-date`` and ``--description``
    already have sensible defaults (today's date, and no description)
    and are never required for flag mode to activate.
    """
    state: CliState = ctx.obj

    with error_boundary():
        if not line:
            dto = prompt_create_journal()
        else:
            parsed_lines = [parse_line_spec(raw) for raw in line]
            dto = parse_create_journal(
                posting_date=posting_date,
                lines=parsed_lines,
                description=description,
            )

        journal_vm = state.call(create_journal_entry_handler, state.context, dto)

    print_journal_entry(journal_vm)


@app.command("get")
def get(
    ctx: typer.Context,
    journal_number: Annotated[
        int | None,
        typer.Argument(help="The journal entry number."),
    ] = None,
) -> None:
    """Look up a single journal entry by its journal number."""
    state: CliState = ctx.obj

    if journal_number is None:
        journal_number = prompt_journal_number()

    with error_boundary():
        journal_vm = state.call(
            get_journal_entry_handler, state.context, journal_number
        )

    print_journal_entry(journal_vm)


@app.command("list")
def list_entries(ctx: typer.Context) -> None:
    """List every journal entry."""
    state: CliState = ctx.obj

    with error_boundary():
        entries = state.call(list_journal_entries_handler, state.context)

    print_journal_list(entries)
