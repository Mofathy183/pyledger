"""Minimal interactive shell loop for the Trutina CLI.

Milestone 1 shape only: echoes input, does not dispatch anywhere.
Real dispatch into the existing Typer app arrives in Milestone 2 --
kept as an isolated module specifically so that growth happens here,
never back in main.py's dispatch-decision logic.
"""

from trutina.cli.state import CliState


def run_shell(state: CliState) -> None:
    """Run the interactive shell loop until the user exits.

    Args:
        state: The CliState for this session. Unused in this
            milestone -- accepted now so Milestone 2 can start
            dispatching through it without changing this function's
            call site in main.py again.
    """
    print("Trutina interactive shell. Type 'exit' or 'quit' to leave.")
    while True:
        try:
            line = input("trutina> ")
        except EOFError, KeyboardInterrupt:
            print()
            break

        stripped = line.strip()
        if stripped in ("exit", "quit"):
            break
        if not stripped:
            continue

        print(f"(echo) {stripped}")
