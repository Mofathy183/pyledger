# src/trutina/cli/features/posting/command.py
"""Typer command group for posting management.

Commands in this module are the CLI's presentation-adapter layer: they
resolve raw input (CLI flags/arguments or interactive prompts) into a
validated value, hand that value to a handler for the actual use case,
and render the result. Commands never call PostingService directly and
never construct domain models — both belong to handler.py and the
service layer respectively.

Unlike account_cmd and journal's command group, this group has no DTO
to construct at all — every command here forwards a single validated
scalar (a journal number or an account name) straight from
parser.py/prompt.py to the handler, since PostingService's own methods
take plain arguments rather than an input DTO (see parser.py's module
docstring for why no input DTO exists for this feature).

This group also has no ``create``/``update``/``delete`` in the
Account/Journal sense — ``post`` is the only mutating operation
(deriving and persisting postings from an already-validated journal
entry), and LedgerPosting is frozen with no update path, so there is
nothing else to expose.
"""

from typing import Annotated

import typer
from trutina.cli.shared.error_boundary import error_boundary
from trutina.cli.state import CliState

from .formatter import print_postings_list
from .handler import (
    get_postings_by_account_handler,
    get_postings_by_journal_number_handler,
    post_journal_entry_handler,
)
from .prompt import prompt_account_identifier, prompt_journal_number

app = typer.Typer(
    help="Manage ledger postings.",
    name="posting",
)


@app.command("post")
def post(
    ctx: typer.Context,
    journal_number: Annotated[
        int | None,
        typer.Argument(help="The journal entry number to post."),
    ] = None,
) -> None:
    """Post a journal entry, deriving and persisting its ledger postings."""
    state: CliState = ctx.obj

    if journal_number is None:
        journal_number = prompt_journal_number()

    with error_boundary():
        postings = state.call(post_journal_entry_handler, state.context, journal_number)

    print_postings_list(
        postings,
        title=f"Postings for Journal Entry #{journal_number}",
    )


@app.command("get-by-account")
def get_by_account(
    ctx: typer.Context,
    account: Annotated[
        str | None,
        typer.Argument(help="An account name."),
    ] = None,
) -> None:
    """List all postings recorded against a given account."""
    state: CliState = ctx.obj

    if account is None:
        account = prompt_account_identifier()

    with error_boundary():
        postings = state.call(get_postings_by_account_handler, state.context, account)

    print_postings_list(postings, title=f'Postings for Account "{account}"')


@app.command("get-by-journal")
def get_by_journal(
    ctx: typer.Context,
    journal_number: Annotated[
        int | None,
        typer.Argument(help="The journal entry number."),
    ] = None,
) -> None:
    """List all postings derived from a specific journal entry."""
    state: CliState = ctx.obj

    if journal_number is None:
        journal_number = prompt_journal_number()

    with error_boundary():
        postings = state.call(
            get_postings_by_journal_number_handler, state.context, journal_number
        )

    print_postings_list(
        postings,
        title=f"Postings for Journal Entry #{journal_number}",
    )
