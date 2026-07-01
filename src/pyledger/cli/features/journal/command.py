"""
Journal entry command group.

This command namespace contains operations related to journal entry
workflows. Journal entries are the foundation of double-entry
accounting and represent financial transactions before they are
posted to the ledger.

Subcommands defined under this namespace should focus on creating,
validating, viewing, and managing journal entries.
"""

import typer

journal_app = typer.Typer(
    help="Manage journal entries.",
    name="journal",
)
