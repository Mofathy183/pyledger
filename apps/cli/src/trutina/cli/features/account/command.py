"""Typer command group for account management.

Commands in this module are the CLI's presentation-adapter layer: they
resolve raw input (CLI flags or interactive prompts) into a validated
DTO, hand that DTO to a handler for the actual use case, and render the
result. Commands never call ``AccountService`` directly and never
construct domain models -- both belong to ``handler.py`` and the
service layer respectively. Commands never print Rich markup directly
either -- every user-facing message, including one-line status text,
is composed in ``formatter.py``.
"""

from typing import Annotated

import typer
from trutina.cli.shared.error_boundary import error_boundary
from trutina.cli.state import CliState

from .formatter import print_aborted, print_account, print_account_list, print_deleted
from .handler import (
    create_account_handler,
    delete_account_handler,
    get_account_handler,
    list_accounts_handler,
    update_account_handler,
)
from .parser import parse_create_account, parse_update_account
from .prompt import (
    confirm_account_deletion,
    prompt_account_identifier,
    prompt_create_account,
    prompt_update_account,
)

app = typer.Typer(
    help="Manage the chart of accounts.",
    name="account",
)

_CATEGORY_HELP = (
    "Asset, Liability, Equity, Revenue, Expense, Dividend, or Drawing "
    "(case-insensitive)."
)


def _fetch_account(state: CliState, identifier: str):
    """Look up an account by code or name, rendering and exiting on failure.

    Shared by ``update`` and ``delete``, both of which need the current
    account record before doing anything else -- ``update`` to seed
    interactive prompt defaults, ``delete`` to display the account's
    name in the confirmation prompt.

    Args:
        state: The current CliState, carrying the CliContext and portal.
        identifier: An account code or account name, as typed or
            prompted.

    Returns:
        The AccountViewModel for the matching account.
    """
    with error_boundary():
        return state.call(get_account_handler, state.context, identifier)


@app.command("create")
def create(
    ctx: typer.Context,
    code: Annotated[
        str | None, typer.Option(help="The account code, e.g. '1000'.")
    ] = None,
    name: Annotated[
        str | None, typer.Option(help="The account's display name.")
    ] = None,
    category: Annotated[str | None, typer.Option(help=_CATEGORY_HELP)] = None,
) -> None:
    """Create a new account.

    Supports two input modes:

    - Explicit CLI arguments (``--code``, ``--name``, ``--category``).
    - Fully interactive prompts, when no option is supplied.

    Mixed input is intentionally not supported. If any CLI option is
    provided, all required options must be supplied. Otherwise the
    command falls back to the interactive workflow.
    """
    state: CliState = ctx.obj

    with error_boundary():
        if code is None and name is None and category is None:
            dto = prompt_create_account()
        elif code is not None and name is not None and category is not None:
            dto = parse_create_account(code=code, name=name, category=category)
        else:
            raise typer.BadParameter(
                "Either provide all required options "
                "(--code, --name, --category) "
                "or omit them all to use interactive mode."
            )

        account_vm = state.call(create_account_handler, state.context, dto)

    print_account(account_vm)


@app.command("get")
def get(
    ctx: typer.Context,
    identifier: Annotated[
        str | None,
        typer.Argument(help="An account code or account name."),
    ] = None,
) -> None:
    """Look up a single account by code or name."""
    state: CliState = ctx.obj

    if identifier is None:
        identifier = prompt_account_identifier()

    account_vm = _fetch_account(state, identifier)

    print_account(account_vm)


@app.command("list")
def list_accounts(ctx: typer.Context) -> None:
    """List every account in the chart of accounts."""
    state: CliState = ctx.obj

    with error_boundary():
        chart_vm = state.call(list_accounts_handler, state.context)

    print_account_list(chart_vm)


@app.command("update")
def update(
    ctx: typer.Context,
    identifier: Annotated[
        str,
        typer.Argument(help="An account code or account name to update."),
    ],
    name: Annotated[str | None, typer.Option(help="New account name.")] = None,
    category: Annotated[str | None, typer.Option(help=_CATEGORY_HELP)] = None,
) -> None:
    """Update an existing account's name and/or category.

    ``identifier`` may be an account code or an account name -- it is
    resolved the same way ``get`` resolves its argument -- and is never
    itself changed by this command. If neither ``--name`` nor
    ``--category`` is supplied, falls back to interactive prompts seeded
    with the account's current values, which requires fetching the
    account first via ``_fetch_account()``.
    """
    state: CliState = ctx.obj

    with error_boundary():
        if name is None and category is None:
            current = _fetch_account(state, identifier)
            dto = prompt_update_account(
                current_code=current.code,
                current_name=current.name,
                current_category=current.category,
            )
        else:
            # The update DTO's own lookup key is the account's code, so a
            # name identifier must be resolved to its code before building
            # the DTO.
            current = _fetch_account(state, identifier)
            dto = parse_update_account(code=current.code, name=name, category=category)

        account_vm = state.call(update_account_handler, state.context, dto)

    print_account(account_vm)


@app.command("delete")
def delete(
    ctx: typer.Context,
    identifier: Annotated[
        str,
        typer.Argument(help="An account code or account name to delete."),
    ],
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip the confirmation prompt.")
    ] = False,
) -> None:
    """Delete an account by code or name.

    ``identifier`` is resolved the same way ``get``'s argument is
    resolved. The account is fetched first purely to display its name
    in the confirmation prompt -- ``--yes`` skips confirmation for
    scripted use.
    """
    state: CliState = ctx.obj

    current = _fetch_account(state, identifier)

    if not yes and not confirm_account_deletion(current.name):
        print_aborted()
        raise typer.Exit(code=0)

    with error_boundary():
        state.call(delete_account_handler, state.context, current.code)

    print_deleted(current.name)
