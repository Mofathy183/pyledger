# pyledger-api

The HTTP presentation layer for PyLedger: a FastAPI application exposing the
same double-entry accounting domain (`pyledger-core`) that `pyledger-cli`
exposes over the terminal. No accounting rules live here — this package
translates HTTP requests into service calls and service results into JSON
responses.

## What Is This Package

`pyledger-api` (import path `pyledger.api`) is one of two presentation
layers over `pyledger-core`, the other being `pyledger-cli`. It owns:

- The FastAPI application factory and composition root (`api/composition/`).
- One feature package per resource — `account`, `journal`, `posting`, and
  `system` (`api/features/`) — each following the same fixed request
  pipeline.
- The shared response envelope and the API's own error-to-HTTP translation
  catalog (`api/shared/`).

It does not define accounting rules, does not talk to MongoDB directly, and
does not import anything from `pyledger-cli`.

## Why Does It Exist

`pyledger-core`'s services (`AccountService`, `JournalService`,
`PostingService`) are transport-agnostic — they know nothing about HTTP,
JSON, or status codes. Something has to be the HTTP entry point onto that
domain. `pyledger-api` is that entry point, kept as an independent
workspace package (rather than folded into the CLI) so a second
presentation layer can exist without either layer depending on the other's
presentation concerns.

## Responsibilities

- Parse and validate incoming HTTP requests into the service layer's Input
  DTOs.
- Call exactly one `pyledger-core` service method per request.
- Translate ViewModels into stable, versioned JSON response contracts.
- Translate every `AppError`/`ValidationAppError`/`pydantic.ValidationError`
  the domain can raise into a consistent JSON error envelope with the
  correct HTTP status code.
- Own the FastAPI composition root: building the singleton service graph
  once at process startup and attaching it to `app.state`.

## Package Layout

```text
apps/api/src/pyledger/api/
├── main.py                       # console-script entry point (uvicorn.run)
├── composition/
│   ├── app.py                     # create_app() factory
│   ├── bootstrap.py                # build_container(), make_lifespan()
│   ├── container.py                # Container — frozen service bundle
│   ├── dependencies.py             # per-service Depends() providers
│   └── tests/
├── features/
│   ├── account/
│   │   ├── router.py                # POST/GET/PATCH/DELETE /accounts
│   │   ├── schemas.py               # Request/Response models
│   │   ├── mapper.py                # Request Schema -> Input DTO
│   │   ├── handler.py               # Input DTO -> AccountService call
│   │   ├── presenter.py             # ViewModel -> Response Schema
│   │   └── tests/
│   ├── journal/                    # same shape, /journal-entries
│   ├── posting/                    # same shape, /postings (read + post only)
│   └── system/                     # GET / and GET /health — flat, no mapper/presenter
└── shared/
    ├── response.py                  # BaseResponse, SuccessResponse
    └── errors/
        ├── catalog.py                # ErrorCode -> HTTP status/message/hint
        ├── handlers.py                # register_exception_handlers()
        └── schemas.py                 # ErrorResponse, ValidationErrorResponse
```

## The Request Workflow

Every feature except `system` follows one fixed pipeline, enforced by
convention across every router in this package:

```text
HTTP Request
  -> Router                 (api/features/<feature>/router.py)
  -> Request Schema          (Pydantic structural validation)
  -> Mapper                  (Request Schema -> Input DTO)
  -> Handler                 (Input DTO -> one service call)
  -> Service                 (pyledger-core — business rules, persistence)
  -> ViewModel
  -> Presenter                (ViewModel -> Response Schema)
  -> Response Schema
  -> HTTP Response
```

A route function does exactly: resolve the mapper, call the handler via
`Depends(get_<feature>_service)`, resolve the presenter, return. No route
contains business logic, constructs a domain model, or catches
`AppError`/`ValidationAppError` — those propagate uncaught to the
exception handlers registered once in `create_app()`.

`system` (`GET /`, `GET /health`) is the one documented exception: it has
no request body, no domain model, and nothing to translate, so its router
is flat rather than split across four files. See `CONTEXT.md` for why this
exception exists and why it should not be copied as a template.

## Installation

Within the workspace:

```bash
uv sync --package pyledger-api
```

`pyledger-api` depends on `pyledger-core`, `pyledger-infrastructure`,
`pyledger-config`, `fastapi[standard]`, and `uvicorn[standard]`.

## Usage

### Running the API locally

```bash
uv run --package pyledger-api uvicorn pyledger.api.composition.app:app --reload
```

or via the installed console script, which reads `Settings` and calls
`uvicorn.run(...)` itself:

```bash
uv run pyledger-api
```

Interactive docs are served at `/docs`; the raw OpenAPI schema at
`/openapi.json`.

### Example requests

Create an account:

```bash
curl -X POST http://localhost:8000/accounts \
  -H "content-type: application/json" \
  -d '{"code": "1001", "name": "Cash", "category": "ASSET"}'
```

Create a balanced journal entry:

```bash
curl -X POST http://localhost:8000/journal-entries \
  -H "content-type: application/json" \
  -d '{
        "posting_date": "2025-01-01T00:00:00",
        "lines": [
          {"account": "Cash", "debit_amount": "100", "credit_amount": "0"},
          {"account": "Sales Revenue", "debit_amount": "0", "credit_amount": "100"}
        ]
      }'
```

Post that entry to the ledger:

```bash
curl -X POST http://localhost:8000/postings/1
```

Retrieve postings by account or by journal number:

```bash
curl http://localhost:8000/postings/by-account/Cash
curl http://localhost:8000/postings/by-journal/1
```

## Response Envelope

Every JSON body carries `success: bool` and `timestamp: datetime`
(`api/shared/response.py::BaseResponse`), so a caller can branch on
outcome without inspecting the HTTP status code:

```json
{
  "success": true,
  "timestamp": "2026-07-14T12:00:00Z",
  "account": {
    "code": "1001",
    "name": "Cash",
    "category": "ASSET",
    "normal_balance": "debit"
  }
}
```

Error responses (`success: false`) additionally carry `error_code`,
`message`, an optional `hint`, and — for validation failures — a `details`
array of per-field violations:

```json
{
  "success": false,
  "timestamp": "2026-07-14T12:00:00Z",
  "error_code": "account.unknown",
  "message": "No account was found for '9999'.",
  "hint": "Verify the account code or name, or create it first via POST /accounts."
}
```

Every domain `ErrorCode` PyLedger can currently raise has a status/message/
hint entry in `api/shared/errors/catalog.py`; anything without an entry
falls back to a generic `500` rather than raising inside the handler
itself.

## Integration With the Rest of the Repository

```text
apps/cli, apps/api          <- you are here
        │
        ▼
pyledger-infrastructure     (Mongo* repos)
        │
        ▼
pyledger-core                (AccountService, JournalService, PostingService)
        │
        ▼
pyledger-shared, pyledger-config
```

`pyledger-api` never imports `pyledger-cli`, and vice versa — enforced by
the workspace's `layers` import-linter contract. Both apps depend on the
same `pyledger-core` service graph and the same `pyledger-infrastructure`
Mongo adapters, wired independently in their own composition roots
(`CliContext` for the CLI, `Container`/`bootstrap.py` here).

## Extending This Package

Adding a new feature (e.g. a future `reporting` resource):

1. **Create the feature folder** — `api/features/<name>/`, exporting
   `router` from an `__init__.py`.
2. **Define request/response schemas** (`schemas.py`) — mirror the
   corresponding `pyledger-core` DTO/ViewModel field-for-field where the
   shapes naturally match, but keep them as distinct classes so the public
   HTTP contract can evolve independently.
3. **Write the mapper** (`mapper.py`) — pure, synchronous, no I/O: Request
   Schema -> Input DTO. No business validation here; that fires inside the
   service.
4. **Write the handler** (`handler.py`) — one `async def` per operation,
   each exactly one service call, no FastAPI import, no exception
   handling.
5. **Write the presenter** (`presenter.py`) — pure, synchronous: ViewModel
   -> Response Schema.
6. **Write the router** (`router.py`) — wire mapper -> `Depends(get_*_service)`
   -> handler -> presenter, one function per operation.
7. **Add a dependency provider** in `composition/dependencies.py` if the
   feature needs a service not already exposed, and add the service to
   `Container` (`composition/container.py`) and `build_container()`
   (`composition/bootstrap.py`).
8. **Register the router** in `composition/app.py::create_app()`.
9. **Add tests** mirroring an existing feature: `test_mapper.py`,
   `test_handler.py`, `test_presenter.py`, `test_router_unit.py`
   (fake-backed), `test_router_integration.py` (real MongoDB).

## Testing

Two tiers, mirroring the CLI's fake/real fixture split
(`tests/fixtures/api.py`):

- **Unit tier** (`@pytest.mark.unit`) — `api_app`/`api_client` built via
  `create_app()` with a `fake_container` (every service backed by a
  `Fake*Repo`) attached directly to `app.state.container`. The real
  lifespan is never entered, so no MongoDB connection is ever opened.
- **Integration tier** (`@pytest.mark.integration`) — `real_api_app`/
  `real_api_client` enter the real lifespan (`bootstrap.make_lifespan()`)
  against `TestSettings`, backed by `clean_db`.

Run just this package's tests:

```bash
uv run pytest -m "unit and api"
uv run pytest -m "integration and api"
```

## What Consumers Should Know

- **Every route follows Router -> Mapper -> Handler -> Presenter**, except
  `system`, which is intentionally flat. Don't copy `system`'s shape for a
  feature with a request body or a domain error to translate.
- **The `Container` is built once, eagerly, at process startup** — not
  lazily per request like the CLI's `CliContext`. A route depending on a
  service via `Depends(get_*_service)` always gets the same singleton
  instance for the life of the process.
- **Every response, success or error, shares one envelope shape**
  (`success`, `timestamp`, plus feature- or error-specific fields) — never
  parse a response by HTTP status code alone.
- **`error_code` is the stable, machine-readable field to branch on** —
  `message`/`hint` text may be reworded over time.
- **No route ever leaks a raw exception or traceback.** Anything outside
  the domain error contract (`AppError`, `ValidationAppError`,
  `pydantic.ValidationError`, FastAPI's `RequestValidationError`) is still
  caught by a catch-all handler and returned as a generic `500` with the
  standard envelope shape.
