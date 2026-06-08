# PyLedger

PyLedger is a Python CLI bookkeeping application that implements double-entry accounting.

## Tech Stack

- Python 3.13+
- Typer
- Rich
- Pydantic v2
- Ruff
- UV

## Core Rules

- Every JournalEntry must balance.
- Total debits must equal total credits.
- Negative amounts are invalid.
- Empty account names are invalid.
- Business logic must remain independent of Typer and Rich.

## Accounting Flow

Journal Entry → Ledger Posting → Trial Balance

## Account Types

- Asset (normal debit)
- Liability (normal credit)
- Equity (normal credit)
- Revenue (normal credit)
- Expense (normal debit)

## Accounting Design Rules

- Prefer JournalEntry + JournalLine architecture.
- Do not introduce new two-account transaction models.
- Support compound journal entries.
- Total debits must equal total credits.

## Architecture

core/
domain models and accounting logic

cli/
Typer commands only

utils/
formatting, console, constants

## Development Guidelines

- Use Pydantic for validation.
- Use strict typing.
- Prefer composition to inheritance.
- Follow clean architecture principles.
- Keep CLI code thin.
- Write tests for business rules.

## Documentation Standards

- Use Google-style docstrings.
- Document business rules and accounting concepts.
- Avoid documenting obvious implementation details.
- Prefer documenting why rather than what.
- Public domain models, services, and repositories should have docstrings.
- Private helpers should only be documented when their intent is non-obvious.