from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.auth import BasicAuthMiddleware
from app.config import get_settings
from app.routers import buckets, planned_flows

settings = get_settings()

app = FastAPI(
    title="Finance Hub",
    version="0.1.0",
    description="Planned flows vs actuals across buckets. Money is decimal dollars in this API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
if settings.basic_auth:
    # Health stays open so the platform check can run without credentials.
    app.add_middleware(
        BasicAuthMiddleware, credentials=settings.basic_auth, exempt_paths=("/api/health",)
    )

api = APIRouter(prefix="/api")


@api.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


api.include_router(buckets.router)
api.include_router(planned_flows.router)
app.include_router(api)


def mount_static(static_dir: str | None) -> None:
    """Serve the built Angular app with an SPA fallback. No-op when the directory is missing."""
    if not static_dir:
        return
    root = Path(static_dir)
    index = root / "index.html"
    if not index.is_file():
        return

    app.mount("/assets", StaticFiles(directory=root / "assets", check_dir=False), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        if path.startswith("api/"):
            raise HTTPException(404)
        candidate = root / path
        if path and candidate.is_file() and candidate.resolve().is_relative_to(root.resolve()):
            return FileResponse(candidate)
        return FileResponse(index)


mount_static(settings.static_dir)
