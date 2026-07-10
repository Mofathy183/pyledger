"""FastAPI application factory for the PyLedger API.

app.py wires the lifespan (bootstrap.py) to a FastAPI instance and
registers routers. It performs no business logic, constructs no
services or repositories directly, and never imports Mongo-specific
infrastructure types — the same rule cli/app.py already follows for the
Typer app.
"""

from fastapi import FastAPI

from pyledger.api.features.system import router as system_router
from pyledger.config import Settings, get_settings

from .bootstrap import make_lifespan


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application.

    A factory rather than a bare module-level `app = FastAPI(...)`
    singleton, for two reasons:

    1. Tests need to construct independent app instances bound to
        TestSettings — required by the Beanie global-registration
        isolation test, which needs two app instances coexisting in one
        test session without corrupting each other's Document
        registration.
    2. `settings` is accepted explicitly, mirroring build_context(),
        so tests never have to monkeypatch get_settings().
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title=settings.api.title,
        version=settings.api.version,
        description=settings.api.description,
        lifespan=make_lifespan(settings),
    )

    app.include_router(router=system_router)

    return app


app = create_app()
