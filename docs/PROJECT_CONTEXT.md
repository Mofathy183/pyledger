# PyLedger Project Context

## Overview

PyLedger is a Python command-line bookkeeping application for double-entry accounting. The current repository is a
feature-oriented domain prototype with a working account service, validated journal and posting models, shared error
translation, and Rich-based journal rendering. Storage-backed workflows, reporting, and operational CLI commands are
not implemented yet.

## Repository Shape

- `src/pyledger/main.py` boots the Typer application.
- `src/pyledger/cli/` contains the Typer app, Rich console setup, themes, formatters, CLI constants, and a journal
  command scaffold.
- `src/pyledger/modules/account/` contains the active account domain, DTOs, async repository contract, service layer,
  and tests.
- `src/pyledger/modules/journal/` contains journal schemas, DTOs, a partial mapping service, an empty repository
  scaffold, an empty rule scaffold, and tests.
- `src/pyledger/modules/posting/` contains the immutable posting schema, an async repository contract, an empty DTO
  scaffold, an empty rule scaffold, a commented service scaffold, and tests.
- `src/pyledger/shared/` contains reusable validation helpers, utility code, and the shared error model.
- `tests/` contains shared fixtures, factories, and fakes, not application test cases.
- Module-local tests live under `src/pyledger/modules/**/tests/`.
- Shared error tests live under `src/pyledger/shared/errors/tests/`.

## Current State

- `Account` enforces code, name, and category validation and derives `normal_balance` from category.
- `ChartOfAccounts` enforces unique codes and unique canonical names, and resolves accounts with `get_by_code()` and
  `get_by_name()`.
- `JournalLine` enforces account normalization and debit/credit exclusivity.
- `JournalEntry` enforces minimum line count, positive journal number, supported posting dates, and balanced totals.
- `LedgerPosting` is an immutable derived record with the same single-side amount rule.
- `AccountService` is complete end to end for create, update, lookup, list, resolve, and delete workflows.
- `JournalService` only maps journal schemas to view models.
- `PostingService` is not executable code; it remains a commented scaffold.
- `cli/formatters/journal_fmt.py` renders journal view models.
- `cli/formatters/error_fmt.py` and `cli/constants/errors.py` exist and import, but no command currently uses them.
- There is no persistent storage layer, trial balance, or reporting pipeline.

## Accounting Model

PyLedger follows standard double-entry accounting.

```text
Journal Entry -> Ledger Posting
```

Only the first two stages exist in code today. There is no trial balance pipeline or downstream reporting layer.

## Domain Models

### Account

- Fields: `code`, `name`, `category`, and computed `normal_balance`.
- `code` is limited to 1 to 20 characters and must match the account code pattern.
- `name` is normalized by `clean_account_name()` and must be 2 to 150 characters long.
- `category` is one of `ASSET`, `LIABILITY`, `EQUITY`, `REVENUE`, `EXPENSE`, `DIVIDEND`, or `DRAWING`.
- `normal_balance` is derived from the category and is not stored independently.
- Account aliases are not implemented.

### ChartOfAccounts

- Enforces unique account codes.
- Enforces unique canonical names case-insensitively.
- Resolves by code with `get_by_code()`.
- Resolves by canonical name with `get_by_name()`.
- Does not expose a `resolve()` method.
- Does not implement aliases.

### JournalLine

- Fields: `account`, `debit_amount`, and `credit_amount`.
- `account` is normalized with `clean_account_name()`.
- A line must carry either a debit amount or a credit amount, not both and not neither.
- Negative amounts are rejected by the schema.

### JournalEntry

- Fields: `journal_number`, `posting_date`, `lines`, and optional `description`.
- `journal_number` must be positive.
- `posting_date` must be later than `2020-01-01` and must not be in the future.
- `lines` must contain at least two `JournalLine` records.
- `total_debits`, `total_credits`, and `is_balanced` are computed fields.
- Unbalanced entries are rejected.

### LedgerPosting

- Fields: `account`, `debit_amount`, `credit_amount`, `journal_number`, and `posting_date`.
- `LedgerPosting` is frozen after creation.
- `account` is normalized with `clean_account_name()`.
- `journal_number` must be positive.
- `posting_date` must be later than `2020-01-01` and must not be in the future.
- `is_debit` is a derived boolean helper.

## DTOs

- `modules/account/dtos.py` defines `CreateAccountInput`, `UpdateAccountInput`, `AccountViewModel`, and
  `ChartOfAccountsViewModel`.
- `modules/journal/dtos.py` defines `JournalLineInput`, `CreateJournalInput`, `JournalLineViewModel`, and
  `JournalViewModel`.
- `modules/posting/dtos.py` is currently empty.

## Service Layer And CLI

- `AccountService` exposes `create_account()`, `update_account()`, `get_account()`, `get_chart()`,
  `resolve_account()`, `list_accounts()`, and `delete_account()`.
- `AccountService` raises `AppError` for business conflicts and `ValidationAppError` for domain validation failures.
- `AccountService.delete_account()` currently checks existence only; posting-history safeguards are not implemented.
- `JournalService` only contains `_to_line_view()` and `_to_entry_view()` mapping helpers.
- `PostingService` is commented out and references stale API concepts, so it should be treated as a scaffold only.
- The CLI currently registers the root app and a `journal` command group, but there are no operational subcommands.
- The journal formatter can render `JournalViewModel` instances, but no command currently feeds it data.
- The error formatter and CLI error catalog are present, but no live command path uses them yet.

## Error System

- `src/pyledger/shared/errors/` defines `ErrorCode`, `AppError`, `ValidationAppError`, `FieldViolation`, and the
  Pydantic translation helpers.
- `pydantic_error()` is used by schema validators to raise domain error codes through Pydantic.
- `get_field_violations()` converts Pydantic validation output into stable `FieldViolation` records.
- The CLI owns the user-facing message catalog in `cli/constants/errors.py` and the render path in
  `cli/formatters/error_fmt.py`.
- The CLI error copy for invalid account names is currently stale; it still mentions commas even though the validator
  does not allow them.

## Testing

- Pytest is configured to collect tests from `tests/` and `src/pyledger/`.
- Root-level `tests/` contains `conftest.py`, `fixtures/`, `factories/`, and `fakes/`.
- `tests/conftest.py` registers the fixture modules as pytest plugins.
- Feature tests live beside the feature code under `src/pyledger/modules/**/tests/`.
- Shared error tests live under `src/pyledger/shared/errors/tests/`.
- `src/pyledger/cli/tests/test_formatter.py` is an empty placeholder file.
- Current automated coverage is concentrated on domain models, shared validation helpers, shared error translation, and
  `AccountService`.

## Known Issues

- Alias support is not implemented anywhere in the active code path.
- `JournalService._to_entry_view()` is currently declared as a staticmethod but still takes a `self` parameter.
- `PostingService` is commented out and should not be treated as executable workflow code.
- The CLI invalid-account-name message is out of sync with the actual account-name validator.
- There are no storage-backed repositories, no operational CLI commands, and no reporting pipeline yet.

## Long-Term Direction

- Add concrete repository implementations behind the existing async contracts.
- Add storage adapters and persistence tests.
- Wire operational account, journal, and posting commands into the CLI.
- Build trial balance and reporting support from validated data.
- Add import/export and integration surfaces once the core bookkeeping workflow is stable.
