# PyLedger

PyLedger is a Python CLI bookkeeping application built around double-entry accounting.

## Current State

- `AccountService` is implemented end to end.
- `JournalService` is implemented end to end for create, get, and list workflows.
- `LedgerPosting` is implemented as an immutable derived model.
- `AccountRepo`, `JournalRepo`, and `PostingRepo` are async repository contracts.
- `src/pyledger/cli/` contains the Typer app, Rich console setup, themes, formatters, CLI constants, and a journal
  command scaffold.
- `src/pyledger/modules/posting/` still contains scaffold code for DTOs, rules, and service behavior.
- There is no concrete storage layer, reporting pipeline, or operational CLI workflow yet.

## Repository Layout

- `src/pyledger/main.py` is the console entry point.
- `src/pyledger/cli/` contains the Typer app, Rich console setup, themes, formatters, CLI constants, and the journal
  command scaffold.
- `src/pyledger/modules/account/` contains the account domain, DTOs, repository contract, service, and tests.
- `src/pyledger/modules/journal/` contains the journal domain, DTOs, repository contract, service, and tests.
- `src/pyledger/modules/posting/` contains the posting schema, repository contract, scaffolded DTOs, scaffolded
  service, and tests.
- `src/pyledger/shared/` contains reusable validation helpers and the shared error model.
- `tests/` contains shared fixtures, factories, and fakes.

## Tooling

- Python 3.14+
- UV
- Typer
- Rich
- Pydantic v2
- Pytest
- Ruff
- Ty
