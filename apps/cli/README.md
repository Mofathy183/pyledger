# Trutina CLI

`trutina-cli` is Trutina's terminal presentation package. It turns command-line arguments or interactive input into calls to the core services, then renders returned view models and application errors. Accounting rules and persistence behavior do not live here.

The installed command is:

```text
trutina-cli
```

This package requires Python 3.14+ and depends on the workspace packages `trutina-core`, `trutina-infrastructure`, and `trutina-config`, plus `typer`, `rich`, `anyio`, and `prompt-toolkit`.

## Commands

The current Typer application registers three command groups:

| Group | Commands |
| --- | --- |
| `account` | `create`, `get`, `list`, `update`, `delete` |
| `journal` | `create`, `get`, `list` |
| `posting` | `post`, `get-by-account`, `get-by-journal` |

Use the application's generated help for supported options and arguments:

```text
trutina-cli --help
trutina-cli account --help
trutina-cli journal create --help
```

`-h` is also a top-level help flag (the Typer app sets `help_option_names` to `["-h", "--help"]`). Commands that omit their relevant input enter their feature's interactive prompt flow where that command supports it.

## Interactive shell

Run the executable with no arguments to open the persistent shell:

```text
trutina-cli
```

The shell prints a Rich welcome panel (brand-styled, compact width) containing:

- the ASCII balance-scale mark
- the letter-spaced `T R U T I N A` wordmark
- the tagline `double-entry, in balance`
- the hint to type `help` to get started, or `exit` to leave

The prompt is `trutina> `.

```text
trutina> account list
trutina> /journal list
trutina> help journal create
trutina> journal create help
trutina> exit
```

- A leading `/` is optional for every shell line; `/account list` and `account list` dispatch the same command. The slash is stripped once in the loop before built-in checks and dispatch.
- `help` and `help <command path>` dispatch the application's own help via `app([*target, "--help"], ...)`. The trailing form, such as `journal create help`, does the same.
- `exit` (and `/exit`) leaves the shell. EOF and Ctrl+C also end the loop. `help` prints and continues. `quit` is not a shell built-in.
- Completion is active while typing (`complete_while_typing=True`). It is built from Typer's live Click command tree (`typer.main.get_command(app)`), so group and subcommand descriptions come from the same short help text as generated help output. The shell also offers its own `exit` and `help` entries from `SHELL_BUILTINS`. Trailing `help` is offered after a group or group+subcommand; after a leading `help `, completion offers real command names as the target, not built-ins.
- Tab accepts the highlighted (or first) completion rather than cycling the menu.
- The shell catches `typer.exceptions.TyperException` (Click usage errors from this Typer version), renders the message, and continues. Application validation and domain errors are handled by each command's `error_boundary()` before dispatch returns.

With arguments, a registered top-level group (`account`, `journal`, or `posting`) runs as a one-shot Typer invocation. A bare `-h` or `--help` also runs one-shot and exits after printing help. Any other first token enters the shell instead of being sent straight to Typer.

## Package layout

```text
apps/cli/
├── pyproject.toml
├── README.md
├── CONTEXT.md
└── src/trutina/cli/
    ├── main.py
    ├── composition/
    │   ├── app.py
    │   ├── bootstrap.py
    │   ├── context.py
    │   └── state.py
    ├── features/
    │   ├── account/
    │   ├── journal/
    │   └── posting/
    ├── shell/
    │   ├── loop.py
    │   ├── dispatch.py
    │   ├── completion.py
    │   ├── builtins.py
    │   └── keybindings.py
    └── shared/
        ├── boundary/
        ├── errors/
        ├── formatters/
        ├── interaction/
        └── ui/
            ├── console.py
            ├── logo.py
            ├── shell_banner.py
            ├── widgets.py
            └── theme/
                ├── styles.py
                ├── detection.py
                └── shell_style.py
```

Composition lives under `composition/`, the interactive shell under `shell/`, and the command error seam under `shared/boundary/`. `shared/ui/` owns the shared Rich console, theme support, widgets, ASCII logo, and shell welcome banner. Feature packages stay under `features/{account,journal,posting}/`.

Former top-level modules (`trutina.cli.app`, `trutina.cli.bootstrap`, `trutina.cli.context`, `trutina.cli.state`, `trutina.cli.shell` as a single module, `trutina.cli.shell_builtins`, `trutina.cli.shell_completion`, and `trutina.cli.shared.error_boundary`) are gone. There are no forwarding shims at those paths. Import current public composition objects from `trutina.cli.composition` (`app`, `main_callback`, `build_context`, `CliContext`, `CliState`); import the public shell entry as `trutina.cli.shell.run_shell`; import the error seam as `trutina.cli.shared.boundary.error_boundary`.

## Execution model

`main.py` is the process-level entry point. `main()` creates a `CliContext` via `build_context()` and calls `run(context)`.

`run()` opens one `anyio.from_thread.BlockingPortal`, creates a `CliState`, then selects shell (`run_shell(state)`) or one-shot Typer dispatch (`app(obj=state)`). Its `finally` block calls `CliContext.aclose()` through that portal. `CliState.call()` is the bridge from synchronous Typer command functions to async handlers and services.

`CliContext` performs no I/O when constructed. A `MongoExecutor` is created eagerly in `__init__`; it holds no connection state. On first repository use, async accessors establish the MongoDB connection, initialize Beanie, construct the Mongo repositories, and cache the services for that CLI invocation. It exposes `get_account_repo()`, `get_journal_repo()`, `get_posting_repo()`, `get_account_service()`, `get_journal_service()`, and `get_posting_service()`. Caller-provided repositories are retained across `aclose()`; repositories the context creates are cleared when it closes. Cached services are always cleared.

`composition/app.py`'s `main_callback()` fills `ctx.obj` with `build_context()` only when `ctx.obj` is `None` (a `CliRunner` path without `obj=`). Production `main.py` always passes a `CliState`, so that branch does not run for a real invocation. A context built only by the callback is not closed by `main.py`'s `finally`.

## Feature boundaries

Each feature follows the same presentation flow:

```text
command.py → parser.py / prompt.py → handler.py → core service
                                      ↓
                                 formatter.py
```

- `command.py` wires Typer to input selection, one or more handler calls, and rendering.
- `parser.py` turns flag values into the feature's input shape; `prompt.py` collects interactive values and delegates to the parser where applicable. Posting has no input DTO: its parser returns a cleaned journal number or account identifier.
- `handler.py` resolves a service through `CliContext` and invokes it.
- `formatter.py` converts service view models into Rich renderables and prints them.

Commands do not call repositories or services directly, construct domain models, or build Rich output inline. `shared/boundary/error_boundary.py` is the shared command error seam: it catches `AppError`, `ValidationAppError`, and Pydantic `ValidationError`, prints formatted panels, and raises `typer.Exit(code=1)`.

## Contributing

Keep terminal concerns in this package and preserve its one-way dependency on the core and infrastructure packages. The deeper rationale, layering rules, and constraints are in [CONTEXT.md](CONTEXT.md). For repository-wide guidance, see [the architecture documentation](../../docs/ARCHITECTURE.md) and [AGENTS.md](../../AGENTS.md).

When adding a command group, create its feature package, register its Typer app in `composition/app.py`, and add unit and integration coverage beside the feature. The shell completion tree reads the registered Click command tree, so registered groups and their help descriptions are discovered without a separate shell command list. Add a terminating keyword only by extending `SHELL_BUILTINS` in `shell/builtins.py`.
