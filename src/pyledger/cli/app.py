"""
Root command-line application for PyLedger.

This module defines the main CLI entry point and registers the
available command groups. Each command group represents a bounded
area of accounting functionality, such as journal entry management.

The CLI layer is responsible only for user interaction and command
routing. Business rules and accounting validations belong to the
domain and service layers.
"""

import typer

from .commands.journal_command import journal_app

app = typer.Typer(
    name="PyLedger",
    help="CLI for managing ledger operations, accounts, and journal entries.",
    context_settings={"help_option_names": ["-h", "--help"]},
    suggest_commands=True,
)

app.add_typer(journal_app, name="journal")
