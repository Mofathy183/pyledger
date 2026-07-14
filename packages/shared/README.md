# pyledger-shared

Reusable validation helpers, utility functions, and the shared domain error
model used across every PyLedger package and application.

## What This Package Is

`pyledger-shared` is the lowest layer of the PyLedger workspace. It has no
dependency on any other PyLedger package — not `core`, not `cli`, not `api`,
not `infrastructure` — and depends only on `pydantic`. Every other package in
the workspace is free to depend on it.

It exists to hold two kinds of code that would otherwise be duplicated across
feature modules, adapters, and interfaces:

- **Accounting-adjacent validation rules** that are reused by more than one
  domain schema (e.g. account name normalization).
- **The stable error contract** (`ErrorCode`, `AppError`, `ValidationAppError`,
  `FieldViolation`) that every service boundary raises and every adapter
  (CLI, API, future interfaces) translates into presentation output.

If a helper is specific to one feature (accounts, journals, postings), it
belongs in that feature's own module, not here. If it's reused by two or more
features, or it defines the cross-cutting error contract, it belongs here.

## Installation

Part of the `uv` workspace; not installed standalone.

```bash
uv sync --package pyledger-shared
```

Other workspace packages depend on it via the workspace member mechanism, not
a version-pinned dependency.

## Public API

### `pyledger.shared.rule`

```python
from pyledger.shared.rule import (
    clean_account_name,
    account_lookup_key,
    is_valid_line_amounts,
)
```

| Function                                                         | Purpose                                                                                                                                                     |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `clean_account_name(value: str) -> str \| None`                  | Trims and validates an account name against the permitted character set. Returns the trimmed name, or `None` if invalid.                                    |
| `account_lookup_key(name: str) -> str`                           | Returns the case-insensitive lookup key for an already-validated account name. Uses `str.casefold()`, not `str.lower()` — this matters for non-ASCII names. |
| `is_valid_line_amounts(debit: Decimal, credit: Decimal) -> bool` | Returns `True` if exactly one of `debit`/`credit` is positive (XOR), enforcing that a journal line represents exactly one side of a transaction.            |

**Example:**

```python
from decimal import Decimal
from pyledger.shared.rule import clean_account_name, account_lookup_key, is_valid_line_amounts

name = clean_account_name("  Accounts Receivable  ")
# "Accounts Receivable"

key = account_lookup_key(name)
# "accounts receivable" — used to detect "Cash" vs "CASH" collisions

is_valid_line_amounts(Decimal("100"), Decimal("0"))   # True
is_valid_line_amounts(Decimal("100"), Decimal("100")) # False — both sides set
is_valid_line_amounts(Decimal("0"), Decimal("0"))     # False — neither side set
```

### `pyledger.shared.errors`

```python
from pyledger.shared.errors import (
    ErrorCode,
    AppError,
    ValidationAppError,
    FieldViolation,
    pydantic_error,
    get_field_violations,
    PYDANTIC_CODES,
)
```

| Symbol                      | Purpose                                                                                                                                                     |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ErrorCode`                 | `StrEnum` of every stable failure identifier in the system — the only vocabulary adapters are allowed to switch on.                                         |
| `AppError`                  | The only exception type permitted to cross a service boundary. Carries `code`, a JSON-primitive-only `context` mapping, and an optional diagnostic `cause`. |
| `ValidationAppError`        | `AppError` subclass carrying a list of `FieldViolation` records for multi-field validation failures.                                                        |
| `FieldViolation`            | A single field-level failure: `code`, `field` (dotted path), `value` (stringified).                                                                         |
| `pydantic_error(code)`      | Raise this from inside a Pydantic validator to tag a domain validation failure with a stable `ErrorCode`.                                                   |
| `get_field_violations(exc)` | Translates a `pydantic.ValidationError` into `list[FieldViolation]`.                                                                                        |
| `PYDANTIC_CODES`            | The explicit allow-list of Pydantic-native error types that map directly to an `ErrorCode`; anything else downgrades to `ErrorCode.UNKNOWN_ERROR`.          |

**Raising a domain validation error from a schema:**

```python
from pydantic import field_validator, BaseModel
from pyledger.shared.errors import pydantic_error, ErrorCode
from pyledger.shared.rule import clean_account_name

class Account(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = clean_account_name(value)
        if cleaned is None:
            raise pydantic_error(ErrorCode.INVALID_ACCOUNT_NAME)
        return cleaned
```

**Translating a `ValidationError` at a service boundary:**

```python
from pydantic import ValidationError
from pyledger.shared.errors import ValidationAppError

try:
    Account(name="")
except ValidationError as exc:
    raise ValidationAppError.validation(exc)
```

**Constructing service-level errors directly:**

```python
from pyledger.shared.errors import AppError, ErrorCode

AppError.not_found(ErrorCode.UNKNOWN_ACCOUNT, resource="account", identifier="9999")
AppError.conflict(ErrorCode.DUPLICATE_ACCOUNT_CODE, resource="account", field_name="code", value="1000")
AppError.storage_unavailable(cause=some_connection_error)
AppError.storage_timeout(cause=some_timeout_error)
AppError.unknown(cause=some_unexpected_error)
```

> **Known behavior to be aware of:** `get_field_violations` only maps
> Pydantic's own built-in error types (the `PYDANTIC_CODES` allow-list) to
> their matching `ErrorCode`. A domain error raised via `pydantic_error(...)`
> currently downgrades to `ErrorCode.UNKNOWN_ERROR` on `violation.code` — the
> original domain code survives only as a string in `violation.value`. Code
> that needs to react to the specific domain code must currently read
> `violation.value`, not `violation.code`.

### `pyledger.shared.util`

```python
from pyledger.shared.util import default_posting_date
```

`default_posting_date() -> datetime` returns today's date with the time
component zeroed out. **Not currently called anywhere in the active
workflow** — it exists but nothing wires it in yet. Don't assume it backs any
current default-date behavior in journal or posting creation.

## Integration With the Rest of the Workspace

- Domain schemas (`modules/*/schemas/`) import `shared.rule` for
  normalization and `shared.errors` (via `pydantic_error`) to raise
  ErrorCode-backed validation failures.
- Services import `shared.errors` (`AppError`, `ValidationAppError`) to raise
  the only exception types permitted to cross a service boundary.
- CLI and API adapters catch `AppError`/`ValidationAppError` and translate
  `ErrorCode` into presentation-layer messages, hints, and status codes —
  none of that presentation text lives in this package.
- `pyledger.shared` itself imports nothing from `core`, `cli`, `api`, or
  `infrastructure`. That direction is one-way.

## Extending This Package

- **New reusable validation rule** (used by 2+ domain schemas): add it to
  `rule.py`, next to the existing functions, with the same "business rule,
  not mechanical check" documentation style.
- **New failure condition**: add a member to `ErrorCode` in `codes.py` in the
  appropriately-grouped section (Generic, Account, Journal, Posting,
  Storage, etc.). Never repurpose an existing member for an unrelated
  failure.
- **New `AppError` constructor pattern**: add a `classmethod` to `AppError`
  following the shape of `not_found`/`conflict`/`storage_unavailable` —
  keep `context` JSON-primitive-only.
- Do **not** add CLI, Rich, Typer, FastAPI, or any presentation-specific
  logic here. If a helper needs to know about terminal output or HTTP
  status codes, it belongs in the adapter package, not `shared`.

See `CONTEXT.md` for the reasoning behind these boundaries and the
invariants that must not be broken.

## Testing

Tests live under `packages/shared/tests/` (rule tests) and
`packages/shared/src/pyledger/shared/errors/tests/` (error-model and
translator tests).

```bash
uv run pytest -m unit packages/shared
```

Rule functions are tested through pure input/output assertions — no
mocking. Error translation is tested against real `pydantic.ValidationError`
instances raised from small inline models, asserting the specific
`ErrorCode` on each `FieldViolation`, not just the exception type.
