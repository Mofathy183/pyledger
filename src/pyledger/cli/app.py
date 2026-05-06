import typer

app = typer.Typer(
    name="PyLedger",
    help="CLI for managing ledger operations, accounts, and journal entries.",
    context_settings={"help_option_names": ["-h", "--help"]},
    suggest_commands=True,
)
