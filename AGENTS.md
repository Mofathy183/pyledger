# PyLedger

PyLedger is a Python CLI bookkeeping application built around double-entry accounting.

## Tech Stack

- Python 3.14+
- UV
- Typer
- Rich
- Pydantic v2
- Pytest
- Ruff
- Ty

## Repository Layout

- `src/pyledger/main.py` is the console entry point.
- `src/pyledger/cli/` contains the Typer app, Rich console setup, themes, formatters, CLI constants, and the journal command scaffold.
- `src/pyledger/modules/` contains the account, journal, and posting feature packages.
- `src/pyledger/shared/` contains reusable validation helpers, utility functions, and the shared error model.
- `tests/` contains shared test infrastructure only: `conftest.py`, `fixtures/`, `factories/`, and `fakes/`.
- Feature tests live beside the feature code under `src/pyledger/modules/**/tests/`.
- Shared error tests live under `src/pyledger/shared/errors/tests/`.
- `src/pyledger/cli/tests/test_formatter.py` exists but is currently empty.

## Current Domain Rules

- Every journal entry must balance.
- Total debits must equal total credits.
- A journal line must contain either a debit amount or a credit amount, never both and never neither.
- Negative amounts are invalid.
- Empty account names are invalid.
- Account names are normalized by `clean_account_name()` and matched case-insensitively with `account_lookup_key()`.
- Account aliases are not implemented.
- Account categories are `Asset`, `Liability`, `Equity`, `Revenue`, `Expense`, `Dividend`, and `Drawing`.
- Normal balance is derived from the account category.
- A `JournalEntry` must contain at least two lines.
- `JournalEntry.journal_number` must be positive.
- `JournalEntry.posting_date` and `LedgerPosting.posting_date` must be later than `2020-01-01` and must not be in the future.
- `LedgerPosting` is frozen after creation.

## Current Implementation Notes

- `AccountService` is the only feature service that is currently coherent end to end.
- `JournalService` currently exposes only private mapping helpers and no public workflow methods.
- `PostingService` is a commented scaffold and is not a usable workflow service.
- `cli/formatters/error_fmt.py` and `cli/constants/errors.py` exist and import, but no CLI command currently wires them into a user-facing workflow.
- `modules/journal/repo.py`, `modules/journal/rule.py`, `modules/posting/dtos.py`, and `modules/posting/rule.py` are empty scaffolds.
- `cli/constants/errors.py` still has wording drift for invalid account names; its copy mentions commas even though `clean_account_name()` does not allow them.
- `JournalService._to_entry_view()` is currently misdeclared as a staticmethod with a `self` parameter, so it should be treated as broken until fixed.

## Development Rules

- Keep business logic independent of Typer and Rich.
- Keep domain validation inside the feature modules.
- Use Pydantic models for domain validation and DTOs for service boundaries.
- Prefer composition to inheritance.
- Use strict typing.
- Keep CLI code thin and presentation-only.
- Keep repository contracts async when they are meant to sit behind storage adapters.
- Do not document alias support, chart resolution helpers, or service methods as implemented unless the code actually provides them.

## Tooling

- Use `ruff format` and `ruff check` for formatting and linting.
- Use `ty check` for static type checking.
- Use `pytest` for tests.
- The pytest configuration enables coverage by default. If Windows file locking interferes with local runs, `pytest -o addopts=""` is the quickest way to inspect the raw test results.

## Testing Guidance

- Domain tests live beside the feature code under `src/pyledger/modules/**/tests/`.
- Shared error tests live under `src/pyledger/shared/errors/tests/`.
- Shared fixtures, factories, and fakes live under `tests/`.
- Current automated coverage is concentrated on domain models, shared validation helpers, and `AccountService`.
- There are no concrete storage, reporting, or user-facing CLI workflow tests yet.

## Error Handling

- `pyledger.shared.errors` is the shared error boundary.
- `ErrorCode`, `AppError`, `ValidationAppError`, and `FieldViolation` are the stable public error types.
- Pydantic validation is translated through `pydantic_error()` and `get_field_violations()`.
- CLI wording belongs in the CLI layer, not in shared errors.
- Keep `AppError` as the only exception type that should cross a service boundary.
- Reconcile `cli/constants/errors.py` and `cli/formatters/error_fmt.py` with the shared error model before relying on them in new code.

## Service And Repository Boundaries

- `AccountRepo` and `PostingRepo` are abstract contracts only.
- There is no concrete repository implementation in the repository today.
- `JournalRepo` is not defined yet.
- Service methods that talk to repos remain async.
- Services should orchestrate domain objects and repositories, not render terminal output.
- CLI code should consume DTOs or view models, not repository implementations or domain internals.
