from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import buckets, planned_flows

app = FastAPI(
    title="Finance Hub",
    version="0.1.0",
    description="Planned flows vs actuals across buckets. Money is decimal dollars in this API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")


@api.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


api.include_router(buckets.router)
api.include_router(planned_flows.router)
app.include_router(api)
