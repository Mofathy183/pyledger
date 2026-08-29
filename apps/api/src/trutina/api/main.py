"""Console-script entry point for the PyLedger API.

Mirrors src/pyledger/main.py's role for the CLI: the one place a process
manager or a developer invokes to start this presentation layer. Unlike
the CLI, this does not construct a Container or open any connection
itself — that entire sequence lives in bootstrap.py and only runs once
uvicorn actually starts serving `app` (see app.py / bootstrap.py).

This module's only job is resolving Settings and handing uvicorn a
target. `uvicorn pyledger.api.app:app` works identically without this
file; this exists so there's one documented, discoverable way to start
the API, the same way `pyledger` is for the CLI, rather than requiring
every developer to remember the equivalent uvicorn invocation by hand.
"""

import uvicorn
from pyledger.config import get_settings


def main() -> None:
    settings = get_settings()

    uvicorn.run(
        "pyledger.api.composition.app:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.reload,
    )


if __name__ == "__main__":
    main()
