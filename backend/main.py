"""FastAPI application setup; business logic lives in backend.services."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm.exc import StaleDataError

from backend.api.routes import router
from backend.config import settings
from backend.database import engine
from backend.errors import ApplicationError
from backend.migrations import migrate_legacy_database
from backend.models import Base


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    migrate_legacy_database(engine)
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Adrobot · Campaign workspace", version="1.0.0", lifespan=lifespan)


@app.exception_handler(ApplicationError)
async def application_error_handler(_request: Request, error: ApplicationError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content={"detail": error.detail})


@app.exception_handler(StaleDataError)
async def stale_data_handler(_request: Request, _error: StaleDataError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "Поток изменён параллельно. Перезагрузите страницу."},
    )


@app.get("/api/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "auth_required": bool(settings().app_token),
        "campaign_name_prefix": settings().campaign_name_prefix,
    }


app.include_router(router)

frontend_directory = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_directory.exists():
    app.mount("/", StaticFiles(directory=frontend_directory, html=True), name="frontend")
