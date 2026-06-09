# PyLedger Project Context

## Overview

PyLedger is a Python command-line bookkeeping application built around double-entry accounting. Its purpose is to model
the core bookkeeping workflow in a small, strict, and well-validated domain: users describe journal entries, the system
enforces accounting rules, and the resulting records can be carried forward into ledger and trial balance views.

The project is designed as a clean-architecture style codebase:

- `core/` holds the accounting domain models and business rules.
- `cli/` contains Typer commands only.
- `utils/` contains formatting, console, and shared presentation helpers.

The current implementation focuses on journal-entry validation and terminal presentation. The broader project direction
is to grow from validated journal entries into a complete bookkeeping workflow with ledger posting and trial balance
generation.

## Accounting Model

PyLedger follows the standard double-entry accounting model. Every financial event is represented as a balanced journal
entry with matching debits and credits. This keeps the accounting equation intact and makes downstream reporting
reliable.

The core concepts are:

- `Journal Entry`: the source record that captures a business transaction.
- `Ledger Posting`: the process of distributing journal-entry amounts into individual account records.
- `Trial Balance`: the summary check that verifies total debits equal total credits across the ledger.

This flow is intentional:

`Journal Entry -> Ledger Posting -> Trial Balance`

Each stage transforms the same underlying transaction data into progressively more structured accounting output.

## Journal Entries

A journal entry is the atomic bookkeeping record in PyLedger. It identifies:

- a unique journal number,
- a posting date,
- a debit account,
- a credit account,
- a debit amount,
- a credit amount,
- an optional description.

Journal entries are the first line of defense for accounting correctness. They must be internally consistent before they
can move into any ledger or reporting process.

In the current codebase, journal entries are represented with Pydantic models and validated before display. This keeps
validation close to the domain model and independent of CLI concerns.

## Journal Entry Design

PyLedger should support compound journal entries rather than limiting transactions to a single debit account and a
single credit account.

The current implementation uses:

- debit_account
- credit_account
- debit_balance
- credit_balance

This design is suitable for simple transactions but does not accurately model real-world accounting systems.

The target design is:

JournalEntry
├── JournalLine
├── JournalLine
├── JournalLine
└── ...

Each JournalLine represents the effect of a transaction on a single account.

Example:

Journal Entry: Sale Transaction

- Cash ................ Debit 100
- Sales Revenue ....... Credit 100

More complex transactions may contain three or more lines.

Example:

Journal Entry: Equipment Purchase

- Equipment ........... Debit 1,000
- VAT Recoverable ..... Debit 150
- Cash ................ Credit 1,150

Validation Rule:

The sum of all debit amounts must equal the sum of all credit amounts.

A JournalEntry is considered valid only when:

Total Debits == Total Credits

## Ledger

The ledger is the account-level view of accounting activity. While a journal entry records a transaction once, the
ledger organizes that same transaction by account so that each account can be inspected over time.

Conceptually, ledger posting does the following:

- takes each balanced journal entry,
- posts the debit and credit sides into the relevant accounts,
- accumulates running balances per account,
- preserves a trace back to the original journal entry.

The ledger is the bridge between transaction capture and reporting. It is the place where journal entries become durable
account histories.

## Trial Balance

The trial balance is a control report used to verify that the ledger remains mathematically correct. It groups balances
by account and compares the total debits and total credits.

The trial balance exists to answer one question:

- Does the accounting system still balance?

If the ledger was posted correctly and every journal entry was balanced, the trial balance should also balance. A
mismatch indicates an error in entry capture, posting, or account classification.

In a mature PyLedger workflow, the trial balance becomes a central checkpoint before financial statements or other
summaries are produced.

## Core Business Rules

PyLedger enforces a small set of non-negotiable accounting rules:

- Every journal entry must balance.
- Total debits must equal total credits.
- Negative amounts are invalid.
- Empty account names are invalid.
- Business logic must remain independent of Typer and Rich.

These rules are not presentation details. They define the integrity of the accounting domain and should remain inside
the core business layer.

Additional domain constraints already visible in the current implementation include:

- posting dates must be valid and bounded,
- account names must use permitted characters,
- journal numbers should be unique and sequential in normal usage,
- descriptive text is optional but constrained.

## Account Types and Normal Balances

PyLedger uses the standard five core account categories:

- Asset: normal debit
- Liability: normal credit
- Equity: normal credit
- Revenue: normal credit
- Expense: normal debit

These normal balances matter because they define what a "positive" balance means for each account type.

- Debit-normal accounts increase with debits and decrease with credits.
- Credit-normal accounts increase with credits and decrease with debits.

That distinction is fundamental to correct posting, account summaries, and trial balance logic.

The current domain model also leaves room for additional classifications as the project evolves, but the five account
types above are the accounting foundation.

## Long-Term Project Vision

The long-term vision for PyLedger is to become a compact but complete bookkeeping tool that remains easy to reason about
and safe to extend.

That means:

- a strong domain layer that keeps accounting rules explicit,
- a CLI that stays thin and delegates to core business logic,
- reliable validation for all money-moving operations,
- account-level ledger views derived from validated journal entries,
- trial balance reporting as a system integrity check,
- room for future reporting features such as summaries, exports, and financial statements.

The project should continue to optimize for correctness first. Features are valuable only if they preserve the
accounting model and keep the codebase maintainable under clean-architecture principles.
