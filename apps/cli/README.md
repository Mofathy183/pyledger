# Trutina CLI

This document describes the design and internals of the **Trutina command-line interface** — the `src/trutina/cli/` package. It is a developer guide for contributors who need to understand how the CLI is put together or who want to add a new CLI feature. It is not the root project README, and it does not describe the accounting domain itself (see `ARCHITECTURE.md`, `PROJECT_CONTEXT.md`, and `AGENTS.md` at the repository root for that).

Everything described here reflects the CLI as it exists in the repository today. Where something is planned but not yet built, it is called out explicitly in [Future Work](#18-future-work) rather than described as current behavior.

---

## Table of Contents

- [Trutina CLI](#trutina-cli)
  - [Table of Contents](#table-of-contents)
  - [1. Introduction](#1-introduction)
  - [2. Design Principles](#2-design-principles)
  - [3. High-Level Architecture](#3-high-level-architecture)
  - [4. Folder Structure](#4-folder-structure)
  - [5. Composition Root](#5-composition-root)
  - [6. CliContext](#6-clicontext)
  - [7. CliState](#7-clistate)
  - [8. Bootstrap Process](#8-bootstrap-process)
  - [9. Command Lifecycle](#9-command-lifecycle)
  - [10. CLI Layers](#10-cli-layers)
  - [11. Error Handling](#11-error-handling)
  - [12. Async Execution Model](#12-async-execution-model)
  - [13. Dependency Rules](#13-dependency-rules)
  - [14. Rich UI](#14-rich-ui)
  - [15. Testing](#15-testing)
  - [16. Adding a New Feature](#16-adding-a-new-feature)
  - [17. Best Practices](#17-best-practices)
  - [18. Future Work](#18-future-work)

---

## 1. Introduction

Trutina is a double-entry bookkeeping application. Its accounting rules — balanced journal entries, chart-of-accounts validation, ledger posting derivation — live entirely in `src/trutina/modules/` and are described in the project's root documentation. The CLI (`src/trutina/cli/`) is the _only_ user-facing entry point into that domain today.

The CLI's job is narrow and deliberate: turn command-line flags or interactive prompts into validated input, hand that input to the service layer, and render whatever comes back — a view model or a structured error — as readable terminal output. It is a **presentation adapter**, not a second place where accounting rules live.

This separation exists for a concrete reason: the domain and service layers are already fully async, fully tested against fakes and real MongoDB, and completely ignorant of Typer, Rich, or terminal concerns. The CLI's job is to bridge a synchronous command-dispatch model (Typer/Click) onto that async service layer without leaking either direction — Typer never appears below the command layer, and no domain or service code ever imports `typer` or `rich`.

Currently, the CLI exposes three command groups — `account`, `journal`, and `posting` — each wired straight through to its corresponding feature service (`AccountService`, `JournalService`, `PostingService`).

---

## 2. Design Principles

- **Thin presentation layer.** Commands parse input and render output. They never decide whether a journal entry balances or whether an account code is valid — that's the domain's job.
- **Business logic lives in services.** `AccountService`, `JournalService`, and `PostingService` are the only place business workflows are orchestrated. The CLI calls them; it never reimplements them.
- **Domain independence.** Nothing under `modules/` imports from `cli/`. The dependency arrow points one way: CLI → services → domain.
- **Feature-oriented organization.** Each bounded area of functionality (account, journal, posting) owns its own command, parser, prompt, handler, and formatter modules, colocated under `cli/features/<feature>/`, instead of being split across parallel `commands/`, `parsers/`, `formatters/` trees.
- **Dependency inversion.** Commands depend on handler functions and a `CliContext` abstraction, never directly on concrete repository or MongoDB types.
- **Async service layer, synchronous CLI.** Typer/Click commands are plain synchronous functions. Every async boundary (service and repository calls) is crossed through a single `BlockingPortal`, never through an ad hoc `asyncio.run()`.
- **Lazy dependency creation.** No MongoDB connection is opened, and no repository or service is constructed, until a command actually needs one.
- **Testability.** Every layer can be exercised in isolation: parsers and prompts with plain values, handlers against a fake-backed `CliContext`, commands end-to-end against `typer.testing.CliRunner`, all without a real database.
- **Extensibility.** Adding a new feature means adding a new `cli/features/<name>/` package and registering it — it does not require touching existing features.

---

## 3. High-Level Architecture

```text
User
  │
  ▼
Typer Command            (cli/features/<feature>/command.py)
  │
  ▼
Parser / Prompt          (cli/features/<feature>/parser.py, prompt.py)
  │
  ▼
Handler                  (cli/features/<feature>/handler.py)
  │
  ▼
Service                  (modules/<feature>/service.py)
  │
  ▼
Repository               (modules/<feature>/repo.py → infrastructure/mongo/<feature>/)
  │
  ▼
MongoDB
```

Rich rendering happens in exactly one place per feature: `formatter.py`. Commands call a `print_*()` function from their feature's formatter once a handler has returned a view model — no other layer touches the console.

Error handling happens in exactly one place per command invocation: the `error_boundary()` context manager (`cli/shared/error_boundary.py`), which wraps the single call into the handler layer. It is the only code that catches `AppError`, `ValidationAppError`, or a raw Pydantic `ValidationError` and turns them into rendered panels plus a clean process exit.

---

## 4. Folder Structure

```text
src/trutina/cli/
├── app.py                     # Root Typer app; registers feature sub-apps
├── bootstrap.py                # build_context() — the composition root
├── context.py                  # CliContext — lazy dependency container
├── state.py                    # CliState — bridges sync Typer to the async event loop
│
├── features/
│   ├── account/
│   │   ├── command.py           # Typer command group: create/get/list/update/delete
│   │   ├── parser.py            # CLI-flag input → DTO
│   │   ├── prompt.py             # Interactive input → DTO (via parser.py)
│   │   ├── handler.py            # DTO → AccountService call
│   │   ├── formatter.py          # ViewModel → Rich renderable
│   │   └── tests/
│   ├── journal/
│   │   ├── command.py           # create/get/list (no update/delete — JournalService has none)
│   │   ├── parser.py, prompt.py, handler.py, formatter.py
│   │   └── tests/
│   └── posting/
│       ├── command.py           # post/get-by-account/get-by-journal
│       ├── parser.py, prompt.py, handler.py, formatter.py
│       └── tests/
│
├── shared/
│   ├── error_boundary.py        # Combines error formatting + console + typer.Exit
│   ├── state.py                  # (re-exported from cli/state.py where applicable)
│   ├── interaction/
│   │   └── prompt.py             # ask(), confirm(), select() — generic Rich prompt primitives
│   ├── ui/
│   │   ├── console.py            # Shared themed Console singleton
│   │   ├── theme/                # ConsoleThemes enum, THEME_MAP, terminal color detection
│   │   └── widgets.py             # panel(), rule(), table() — generic Rich widget factories
│   ├── errors/
│   │   ├── errors.py              # ERRORS: ErrorCode → user-facing message
│   │   └── hint.py                 # HINTS, FIELD_LABELS: resolution guidance per ErrorCode
│   └── formatters/
│       └── error.py               # Pydantic/AppError → FormattedError → Rich Panel
│
└── tests/                       # CliContext, CliState, bootstrap, and app-level tests
```

Root-level files:

- **`main.py`** (`src/trutina/main.py`) — the console-script entry point. Opens the CLI's one and only `BlockingPortal`, constructs `CliState`, and dispatches the Typer app.

---

## 5. Composition Root

`bootstrap.py` is the CLI's single composition root. Its only function, `build_context()`, decides which `Settings` to use and constructs a `CliContext` from it:

```python
def build_context(settings: Settings | None = None) -> CliContext:
    return CliContext(settings=settings)
```

Constructing a `CliContext` performs **no I/O**. It doesn't open a MongoDB connection, and it doesn't build any repository or service. Every dependency — repositories and services alike — is created lazily, the first time a command actually asks for it, and cached for the remainder of that invocation.

This matters for two reasons:

- **Startup cost stays flat regardless of which command runs.** `trutina account --help` never touches MongoDB, because nothing in the `--help` path ever calls one of `CliContext`'s `get_*` accessors.
- **Testability.** A `CliContext` built with injected fake repositories (`account_repo=`, `journal_repo=`, `posting_repo=`) can never open a real connection, because the lazy-creation branch in each accessor only runs when the corresponding repository is `None`.

Ownership is equally explicit: in production, `main.py` is the sole owner of a `CliContext`'s lifetime for the life of one process invocation. Repositories injected by a caller (typically a test) are **caller-owned** — the context never tears them down. Repositories the context builds itself are **context-owned** — they're discarded on `aclose()` so a later access rebuilds them against a fresh connection.

---

## 6. CliContext

`CliContext` (`cli/context.py`) is the per-invocation dependency container for the entire CLI dependency graph.

**Responsibilities:**

- Lazily establish and cache the shared MongoDB connection (`connect()` from `infrastructure/mongo`) and Beanie document registration, on first use only.
- Lazily construct and cache each repository (`AccountRepo`, `JournalRepo`, `PostingRepo`) against a single shared `MongoExecutor`.
- Lazily construct and cache each service (`AccountService`, `JournalService`, `PostingService`), wiring `JournalService` to `AccountService` and `PostingService` to `JournalService` exactly as production code requires.
- Translate MongoDB connection failures into structured `AppError`s (`STORAGE_TIMEOUT` for `ServerSelectionTimeoutError`, `STORAGE_UNAVAILABLE` for `ConnectionFailure`) at the moment the connection is first opened, so a startup failure surfaces through the same `AppError` contract as any other storage failure.
- Release the connection and reset context-owned cached state on `aclose()`.

**Lazy resolution in practice** — every accessor follows the same shape:

```python
async def get_account_repo(self) -> AccountRepo:
    if self._account_repo is None:
        await self._get_connection()
        self._account_repo = MongoAccountRepo(self._executor)
    return self._account_repo
```

Services compose on top of repositories the same way — `get_journal_service()` calls `get_journal_repo()` and `get_account_service()` internally, so requesting a service is enough; callers never need to separately request the repository first.

**Lifetime:** one `CliContext` per CLI invocation. `__aenter__`/`__aexit__` support `async with context: ...` for callers that manage it directly (chiefly tests); production code goes through `main.py`'s portal-based flow instead (see [Bootstrap Process](#8-bootstrap-process)).

**Cleanup (`aclose()`):** idempotent. Closes the MongoDB connection if one was opened, clears cached services unconditionally, and clears cached repositories _unless_ they were injected by the caller.

**Testing overrides:** `CliContext(settings=..., account_repo=..., journal_repo=..., posting_repo=...)` accepts any subset of repositories directly. `tests/factories/cli.py`'s `make_fake_cli_context()` is the standard way tests build a `CliContext` that can never touch a network — every omitted repository defaults to its `Fake*Repo` counterpart from `tests/fakes/`.

---

## 7. CliState

`CliState` (`cli/state.py`) is a small, frozen dataclass that gets threaded through every Typer command via `ctx.obj`:

```python
@dataclass(frozen=True, slots=True)
class CliState:
    context: CliContext
    portal: BlockingPortal

    def call(self, func, *args: object):
        return self.portal.call(func, *args)
```

**Why it exists:** Typer/Click command functions are plain, synchronous `def`s — they cannot be `async def` and still dispatch normally through Click's machinery. But `CliContext`'s accessors, and every service/repository method beneath them, are `async`. `CliState` is the seam that lets a synchronous command body reach into that async world without each command reinventing its own event-loop bridge.

**Relationship with `BlockingPortal`:** `state.call(func, *args)` is the _only_ sanctioned way a command body calls an async accessor. It blocks the calling (main) thread until `func(*args)` resolves on the portal's background event loop, then returns the plain result. Commands never call `asyncio.run()`, `await`, or construct their own event loop.

**Relationship with `CliContext`:** `CliState` pairs exactly one `CliContext` with exactly one `BlockingPortal`. It owns no state of its own beyond that pairing — it is a bridge, not a cache.

**Lifetime:** created once per process invocation, alongside the portal, in `main.py::run()` (production) or directly in test fixtures (`fake_cli_state`, `real_cli_state`, and various feature-local `*_cli_state` fixtures).

---

## 8. Bootstrap Process

```text
┌──────────┐     ┌────────────────┐     ┌─────────────┐     ┌───────────┐     ┌─────────┐
│  main()  │────▶│ build_context()│────▶│ start_       │────▶│ CliState  │────▶│ app(obj=│
│          │     │ (bootstrap.py) │     │ blocking_    │     │ (context, │     │  state) │
│          │     │                │     │ portal()     │     │  portal)  │     │         │
└──────────┘     └────────────────┘     └─────────────┘     └───────────┘     └────┬────┘
                                                                                     │
                                                                          Typer dispatches
                                                                          the matched command
                                                                                     │
                                                                                     ▼
                                                                         command runs synchronously,
                                                                         using state.call(...) for
                                                                         any async work
                                                                                     │
                                                                                     ▼
                                                                    finally: portal.call(context.aclose)
```

1. **`main()`** (`src/trutina/main.py`) calls `build_context()` with no explicit `Settings`, so the constructed `CliContext` falls back to the cached, environment-sourced `get_settings()`.
2. **`main()`** calls **`run(context)`**, which:
   - opens the CLI's single event loop via `start_blocking_portal(backend="asyncio")`,
   - constructs `CliState(context=context, portal=portal)`,
   - dispatches Typer synchronously via `app(obj=state)` on the calling (main) thread,
   - guarantees `portal.call(context.aclose)` runs in a `finally` block — whether `app(obj=state)` returns normally, raises an application exception, or exits via Click's `SystemExit`-based `--help`/usage-error handling.
3. **`app.py`**'s `main_callback()` is a defensive fallback: if `ctx.obj` is ever `None` (i.e., something invoked the Typer app without going through `main.py`'s managed flow — chiefly `CliRunner` in tests that don't pass `obj=`), it calls `build_context()` itself. This path performs no I/O either, but a context built this way is _not_ wrapped in `main.py`'s `finally`, so it must only ever be used with a context that can never open a real connection.
4. **Click/Typer resolves eager options (`--help`) before invoking `main_callback()`**, so `trutina --help` never triggers any context construction at all.

There is exactly one `BlockingPortal`, and therefore exactly one event loop, for the life of the process. No command, service, or repository is permitted to open a second one.

---

## 9. Command Lifecycle

```text
User types a command
        │
        ▼
Typer parses argv into command + options
        │
        ▼
Command function runs (cli/features/<feature>/command.py)
        │
        ├─ if CLI flags/arguments were given → parser.py validates and builds a DTO
        └─ if required flags were omitted    → prompt.py interactively collects them,
                                                 still funneling through parser.py
        │
        ▼
state.call(handler_fn, state.context, dto)   — crosses into the async world via the portal
        │
        ▼
Handler (handler.py) resolves the relevant service from CliContext
        │
        ▼
Service (modules/<feature>/service.py) orchestrates domain construction,
validation, and repository calls
        │
        ▼
Repository (modules/<feature>/repo.py → MongoDB adapter) persists/reads data
        │
        ▼
Service returns a ViewModel (or raises AppError / ValidationAppError)
        │
        ├─ success → formatter.py builds a Rich renderable from the ViewModel,
        │            command calls print_*(), Rich Console renders it
        │
        └─ failure → error_boundary() catches the exception, formats it via
                     cli/shared/formatters/error.py, prints panel(s), and raises
                     typer.Exit(code=1)
```

Every stage is intentionally narrow:

- **Parser/Prompt** never call a service or touch the console.
- **Handler** never touches Typer, Click, or Rich — it is a plain `async def` callable identically from a command or directly from a test.
- **Formatter** never calls a service — it only turns an already-fetched ViewModel into a renderable, and is split into pure `build_*()` functions (return a renderable) and thin `print_*()` wrappers (build, then `console.print(...)`).
- **error_boundary()** wraps exactly one `state.call(...)` per command body — never more.

---

## 10. CLI Layers

| Layer                                                                                                      | Responsibility                                                                                                                                               | Allowed dependencies                                                                                     | Forbidden dependencies                                | Inputs                                | Outputs                                                                                  |
| ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------- |
| **Commands** (`command.py`)                                                                                | Typer wiring, decide flag-mode vs. interactive-mode, call handler via `state.call`, call formatter                                                           | `typer`, `state.py`, own feature's `parser.py`/`prompt.py`/`handler.py`/`formatter.py`, `error_boundary` | Repositories, services, domain models, raw Rich calls | CLI args/options, `ctx.obj: CliState` | Console output (via formatter), process exit code                                        |
| **Parsers** (`parser.py`)                                                                                  | Convert raw strings (CLI flags) into a DTO; normalize incidental whitespace; resolve enums like account category                                             | Application DTOs, `typer.BadParameter`                                                                   | Services, repositories, Rich, prompting               | Raw strings                           | DTO instance, or raises `typer.BadParameter` / lets `pydantic.ValidationError` propagate |
| **Prompts** (`prompt.py`)                                                                                  | Collect the same values interactively via `cli.shared.interaction`, then delegate to the feature's own `parser.py`                                           | `cli.shared.interaction` (`ask`, `confirm`, `select`), own feature's `parser.py`                         | Services, repositories, business validation           | Terminal input                        | Same DTO type the parser would build                                                     |
| **Handlers** (`handler.py`)                                                                                | Resolve the right service from `CliContext`, call exactly one service method, let exceptions propagate                                                       | `CliContext`, the feature's own service type                                                             | `typer`, `rich`, prompting, printing                  | `CliContext` + DTO/scalar             | ViewModel(s), or raises `AppError`/`ValidationAppError`                                  |
| **Formatters** (`formatter.py`)                                                                            | Turn a ViewModel into a Rich renderable (`build_*`), then print it (`print_*`)                                                                               | `cli.shared.ui` (`console`, `panel`, `rule`, `table`), the feature's own DTOs                            | Services, repositories, domain schemas                | ViewModel(s)                          | Rich `Panel`/`Text`/`Table`, or printed console output                                   |
| **Shared UI** (`cli/shared/ui/`)                                                                           | Generic Rich widget factories (`panel`, `rule`, `table`) and the themed `console` singleton                                                                  | `rich`, theme definitions                                                                                | Any feature-specific ViewModel or DTO                 | Renderable content + style names      | Configured `Panel`/`Rule`/`Table`                                                        |
| **Shared Errors** (`cli/shared/errors/`, `cli/shared/formatters/error.py`, `cli/shared/error_boundary.py`) | Map `ErrorCode` → user-facing message/hint; format `AppError`/`ValidationAppError`/`ValidationError` into panels; own the try/except + `typer.Exit` boundary | `shared.errors` (domain `ErrorCode`/`AppError`), `cli.shared.ui`                                         | Feature-specific formatters or DTOs                   | Raised exceptions                     | Printed panels + `typer.Exit(code=1)`                                                    |

---

## 11. Error Handling

The CLI never lets a raw domain or Pydantic exception reach the terminal as a traceback. Every command body wraps its one call into the async world in `error_boundary()`:

```python
with error_boundary():
    account_vm = state.call(create_account_handler, state.context, dto)
```

**Error flow:**

1. A service (or a DTO's own Pydantic validation) raises one of:
   - `pydantic.ValidationError` — raw structural validation failure from a DTO or domain model.
   - `AppError` — a single structured service-layer failure (e.g. `DUPLICATE_ACCOUNT_CODE`, `UNKNOWN_JOURNAL_ENTRY`, `STORAGE_UNAVAILABLE`).
   - `ValidationAppError` — a subclass of `AppError` carrying a list of `FieldViolation`s (e.g. multiple invalid fields at once).
2. `error_boundary()` catches `ValidationAppError` first (since it _is_ an `AppError`, subclass ordering matters), then plain `AppError`, then raw `pydantic.ValidationError`.
3. Each branch resolves the failure through `cli/shared/formatters/error.py`:
   - `format_validation_errors(exc)` — Pydantic errors → `list[FormattedError]`.
   - `format_app_error(exc)` — a single `AppError` → one `FormattedError`.
   - `format_validation_app_error(exc)` — a `ValidationAppError`'s `FieldViolation`s → `list[FormattedError]`, restoring the real domain `ErrorCode` from `FieldViolation.value` when the violation was downgraded to `UNKNOWN_ERROR` upstream.
4. Message text and resolution hints are resolved from two CLI-owned catalogs, **not** from `shared/errors`: `cli/shared/errors/errors.py` (`ERRORS: dict[ErrorCode, ErrorDetail]`) and `cli/shared/errors/hint.py` (`HINTS`, `FIELD_LABELS`). This keeps user-facing wording entirely in the CLI layer — the shared error model stays free of presentation text.
5. `build_error_panels(...)` turns each `FormattedError` into a Rich `Panel` titled `"Validation Error"`.
6. `error_boundary()` prints every panel via the shared `console`, then raises `typer.Exit(code=1)` — chained `from None` so the original traceback is not re-surfaced to the user.

Any exception outside this contract (e.g. a bare `KeyError`) is **not** caught by `error_boundary()` — it propagates unchanged, since only `AppError`/`ValidationAppError`/`pydantic.ValidationError` are part of the CLI's error contract.

**Exit codes:**

- `0` — command succeeded.
- `1` — a domain/validation error occurred and was rendered as a panel (via `error_boundary()`).
- `2` — a Typer/Click usage error (e.g. malformed `--line` flag caught in `parser.py` and raised as `typer.BadParameter`, or a missing required argument).

---

## 12. Async Execution Model

- **Typer remains synchronous** because Click's dispatch machinery (`app(obj=state)`) is itself synchronous; there is no supported way to make a Typer command body `async def` and still have Click await it directly.
- **Services and repositories are async** because they perform I/O — MongoDB reads/writes via Beanie/PyMongo — and the domain layer is designed to be storage-agnostic and non-blocking.
- **`BlockingPortal`** (from `anyio.from_thread`) is the bridge: it runs a background thread hosting one asyncio event loop, and exposes `portal.call(func, *args)`, which blocks the calling (main) thread until the async `func` completes and returns its plain result.
- **`state.call(...)`** is `CliState`'s thin wrapper around `portal.call(...)` — the only API surface a command body uses to reach an async accessor.
- **Single event loop:** `start_blocking_portal()` is called exactly once, in `main.py::run()`. No command, service, handler, or repository may create a second loop or a second portal — doing so would fragment MongoDB client state across event loops, which PyMongo's async client does not support (see `tests/fixtures/cli.py`'s `real_cli_state` docstring for a documented example of exactly this hazard and how it's avoided).
- **`asyncio.run()` is never used inside commands** because it always creates a brand-new event loop, which would both violate the single-loop invariant and be unable to reuse a `CliContext`'s already-open MongoDB connection from a previous accessor call in the same invocation.

---

## 13. Dependency Rules

**Commands must never:**

- Call a repository or service directly (`AccountService(...)`, `MongoAccountRepo(...)`, etc.) — only `CliContext` constructs these, and only handlers call them.
- Contain business logic (balance checks, uniqueness checks, category resolution) — that belongs to parsers (structural resolution) or the domain/service layer (business rules).
- Construct domain models (`Account(...)`, `JournalEntry(...)`) directly.
- Render Rich components directly — every printed message goes through the feature's `formatter.py`, even one-line status text like "Aborted — no changes made."

**Handlers must never:**

- `print(...)` or call `console.print(...)`.
- Import `typer` or construct `typer.BadParameter`/`typer.Exit`.
- Perform interactive prompting.

**Formatters must never:**

- Contain business logic (e.g. deciding whether an entry is balanced — they only render the `is_balanced` flag a ViewModel already carries).
- Access a repository or service.
- Import domain schemas directly — only the DTOs/ViewModels a service returns.

**Services must remain UI-independent** — nothing under `modules/*/service.py` imports `rich`, `typer`, or anything under `cli/`.

---

## 14. Rich UI

- **Console** (`cli/shared/ui/console.py`) — a single themed `Console` singleton, shared by every feature's formatter and by `error_boundary()`. Configured with `highlight=True`, `soft_wrap=True`, and an installed Rich traceback handler styled with the `error` theme.
- **Theme** (`cli/shared/ui/theme/`) — `ConsoleThemes` is an enum of named styles (`SUCCESS`, `ERROR`, `WARNING`, `INFO`, `DEBIT`, `CREDIT`, `ASSETS`, `LIABILITIES`, `EQUITY`, `JOURNAL_ENTRIES`, `T_ACCOUNT`), each a Rich style string. `THEME_MAP` derives the theme dict actually passed to `Console(theme=Theme(THEME_MAP))`. `detection.py` inspects terminal environment variables (`COLORTERM`, `WT_SESSION`, `TERM_PROGRAM`, etc.) to decide whether to layer in a background color, so the same theme degrades gracefully on terminals without true-color support.
- **Widgets** (`cli/shared/ui/widgets.py`) — three generic factories used by every formatter:
  - `panel(content, title, style="success")` — a bordered `Panel` with consistent padding.
  - `rule(style="success")` — a horizontal `Rule` divider between panel sections.
  - `table(*columns)` — a `Table` shell (box style `SIMPLE`, `expand=True`) with columns pre-configured from `(header, justify, style)` tuples; callers add rows themselves.
- **Panels and Tables** — every feature's `build_*()` function composes these three primitives; no formatter constructs a bare `rich.panel.Panel` or `rich.table.Table` directly.
- **Formatting philosophy** — build functions are pure (construct and return a renderable, no I/O); print functions are thin (`console.print(build_*(...))`). Debit/credit-oriented rows are consistently styled with the `"debit"`/`"credit"` theme names across the account, journal, and posting formatters, so a debit-normal account, a debit journal line, and a debit posting all read the same way at a glance.

---

## 15. Testing

The CLI test suite (colocated under `cli/features/<feature>/tests/` and `cli/tests/`) is split along the same layer boundaries as the production code, plus a unit/integration split driven by whether MongoDB is actually touched.

- **Fake repositories** (`tests/fakes/{account,journal,posting}_repo.py`) — in-memory implementations of each `*Repo` contract. `FakeJournalRepo` issues sequential journal numbers starting at 1 regardless of whether the caller ultimately saves the entry, matching the real `MongoJournalRepo`'s allocation contract closely enough for service-level assertions.
- **`CliContext` fixtures** — `tests/factories/cli.py::make_fake_cli_context()` builds a `CliContext` with every repository defaulted to its `Fake*Repo`, so it can never open a real connection. `tests/fixtures/cli.py::fake_cli_context` wraps this with the shared `chart_of_accounts` fixture; `real_cli_context`/`real_cli_state` build a genuine, MongoDB-backed `CliContext` for the integration tier.
- **`CliState` fixtures** — `fake_cli_state` pairs `fake_cli_context` with its own `BlockingPortal` (safe, since no Mongo I/O is involved). `real_cli_state` does the same against real MongoDB, with extra care taken (documented in its fixture docstring) to re-register Beanie's document classes against the session-scoped connection afterward, since `init_beanie()` mutates global class state.
- **Unit tests** (`@pytest.mark.unit`) — exercise parsers and prompts with plain values (no I/O at all); handlers directly as `async def` coroutines against a fake-backed `CliContext` (never through a portal, to avoid a cross-event-loop hazard between pytest-asyncio's own loop and a fixture's portal loop); formatters by rendering into `console.capture()` and asserting on the captured text or the renderable's structure; and full commands via `typer.testing.CliRunner` against a fake-backed `CliState`.
- **Integration tests** (`@pytest.mark.integration`) — the same `CliRunner`-based command tests, but against `real_cli_state`, proving the full stack (command → parser → handler → real service → real MongoDB repository) end to end, including duplicate-key and connection-failure translation paths.
- **End-to-end command tests** — every feature's `test_command_unit.py` (fake-backed) and `test_command_integration.py` (Mongo-backed) invoke the Typer app exactly as a user would (`runner.invoke(app, [...], obj=state, input=...)`), asserting on both `result.exit_code` and console output captured independently via `console.capture()`.

Commands are tested without touching MongoDB by depending only on `fake_cli_state`/`fake_cli_context`-family fixtures, which are constructed so that no code path inside them can reach `CliContext._get_connection()`.

---

## 16. Adding a New Feature

1. **Create the feature folder** — `src/trutina/cli/features/<name>/`, with an `__init__.py` that exports `app` from `command.py`.
2. **Create the parser** (`parser.py`) — functions that turn raw CLI-flag strings into the feature's application DTO(s), normalizing incidental whitespace and resolving any enums. Raise `typer.BadParameter` for CLI-level input errors; let DTO/domain validation errors propagate as `pydantic.ValidationError`.
3. **Create the prompt** (`prompt.py`) — interactive counterparts that collect the same values via `cli.shared.interaction` (`ask`, `confirm`, `select`) and delegate to the same parser functions, so both input paths converge on one DTO-construction path.
4. **Create the handler** (`handler.py`) — plain `async def` functions that resolve the relevant service from a `CliContext` (add a `get_<feature>_service()` accessor to `CliContext` if the service doesn't already have one) and call exactly one service method.
5. **Create the formatter** (`formatter.py`) — `build_*()` functions that turn ViewModels into Rich renderables using `cli.shared.ui`'s `panel`/`rule`/`table`, plus thin `print_*()` wrappers.
6. **Create the command** (`command.py`) — a `typer.Typer()` sub-app with one function per operation, each choosing between flag-mode and interactive-mode input, calling its handler via `state.call(...)` inside `error_boundary()`, then calling the matching `print_*()`.
7. **Register the Typer app** — add `app.add_typer(<name>_app, name="<name>")` in `cli/app.py`.
8. **Add tests** — mirror the structure of an existing feature: `test_parser.py`, `test_prompt.py`, `test_handler.py`, `test_formatter.py`, `test_command_unit.py` (fake-backed), and `test_command_integration.py` (Mongo-backed, `@pytest.mark.integration`).
9. **Update documentation** — note the new command group in this README's folder structure and layer tables if it introduces any new pattern; update the root `ARCHITECTURE.md`/`PROJECT_CONTEXT.md` if the feature's service/repository layer changed.

---

## 17. Best Practices

- Keep commands small — a command function should be little more than "choose input mode → call handler → call formatter."
- Keep handlers thin — one service call per handler function; no branching business logic.
- Prefer ViewModels over raw domain models everywhere below the service boundary — formatters, in particular, should never need to import a domain schema.
- Never bypass a service to reach a repository directly from CLI code.
- Never duplicate validation that the DTO or domain model already performs — parsers normalize input noise (whitespace, casing) and resolve CLI-specific shorthand; they don't re-implement business rules.
- Reuse `cli.shared.ui` for anything Rich-related instead of constructing `Panel`/`Table`/`Rule` inline in a feature formatter.
- Reuse `error_boundary()` and the shared error-formatting pipeline instead of writing feature-specific `try`/`except` blocks around service calls.
- Keep async boundaries centralized — every crossing into async code goes through `state.call(...)`; don't introduce a second bridging mechanism.
- Favor composition over inheritance, consistent with the rest of the codebase's stated development rules.

---

## 18. Future Work

The following are not implemented in the current codebase and should not be inferred from this document as available today:

- Additional CLI features beyond `account`, `journal`, and `posting` (e.g. reporting or trial-balance commands — see the root `ROADMAP.md`).
- Shell completion improvements beyond whatever Typer/Click provide out of the box.
- Richer interactive workflows (e.g. multi-step wizards spanning more than one command).
- Reporting commands (trial balance, account balance summaries, historical views) — these depend on reporting support that does not yet exist at the service/domain layer.
- A plugin system for third-party CLI command groups.
- Multi-company or multi-ledger command support.
