# pyledger

A simple command-line bookkeeping system built in Python that simulates how a real accounting system works.

## Folder Structure:
```text
pyledger/
│
├── pyproject.toml
├── README.md
├── uv.lock
├── ruff.toml       # config of the linter and the formatter
│
├── src/
│   └── pyledger/
│       │
│       ├── __init__.py
│       ├── main.py              # CLI entry point
│       │
│       ├── core/
│       │   ├── models.py       # JournalEntry, Account, LineItem
│       │
│       ├── cli/
│       │   ├── app.py      # have the entry point of the typer app and its config
│       │
│       └── utils/
│           └── common.py       # helper functions
│           ├── formatting.py   # pretty printing tables
│           └── constants.py    # the success and error messages and extensions
│           └── console.py      # the config of the rich and export the console from it
```