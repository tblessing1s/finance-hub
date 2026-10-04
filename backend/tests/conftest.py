"""Test plumbing. The test database is migrated up with Alembic at session start and back
down at the end, so the migrations themselves are exercised on every run. Each test runs
inside a transaction that is rolled back, so no test data ever persists.

Fixtures only: nothing here is ever loaded into the real database."""

from collections.abc import Generator
from datetime import date
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from alembic import command
from app.config import get_settings
from app.db import get_db
from app.main import app
from app.models import (
    AmountRule,
    Bucket,
    BucketKind,
    Cadence,
    LumpyItem,
    PlannedFlow,
    StopRule,
)

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _alembic_config(url: str) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.cmd_opts = type("Opts", (), {"x": [f"db_url={url}"]})()
    return cfg


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    url = get_settings().test_database_url
    cfg = _alembic_config(url)
    command.downgrade(cfg, "base")  # clean slate if a previous run was interrupted
    command.upgrade(cfg, "head")
    eng = create_engine(url)
    yield eng
    eng.dispose()
    command.downgrade(cfg, "base")


@pytest.fixture
def db(engine: Engine) -> Generator[Session, None, None]:
    with engine.connect() as conn:
        outer = conn.begin()
        session = Session(
            bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        try:
            yield session
        finally:
            session.close()
            outer.rollback()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def buckets(db: Session) -> dict[str, Bucket]:
    rows = {
        "checking": Bucket(name="WF Checking", kind=BucketKind.checking, floor_cents=750_000),
        "hub": Bucket(name="Schwab Hub", kind=BucketKind.hub),
        "runway": Bucket(name="Runway", kind=BucketKind.runway, target_cents=3_000_000),
        "engine": Bucket(name="Engine", kind=BucketKind.engine),
        "reserve": Bucket(name="Lumpy Reserve", kind=BucketKind.lumpy_reserve),
    }
    db.add_all(rows.values())
    db.commit()
    return rows


@pytest.fixture
def plan(db: Session, buckets: dict[str, Bucket]) -> dict[str, object]:
    """The brief's synthetic plan: two paycheck flows, one sweep, one stop rule, one lumpy item."""
    paycheck = PlannedFlow(
        name="Paycheck",
        to_bucket_id=buckets["checking"].id,
        amount_cents=320_000,
        cadence=Cadence.per_paycheck,
        anchor_date=date(2026, 10, 2),
    )
    k401 = PlannedFlow(
        name="Runway contribution",
        from_bucket_id=buckets["checking"].id,
        to_bucket_id=buckets["runway"].id,
        amount_cents=50_000,
        cadence=Cadence.per_paycheck,
        anchor_date=date(2026, 10, 2),
        stop_rule=StopRule.bucket_reaches_target,
        redirect_to_bucket_id=buckets["engine"].id,
    )
    sweep = PlannedFlow(
        name="Sweep to hub",
        from_bucket_id=buckets["checking"].id,
        to_bucket_id=buckets["hub"].id,
        amount_rule=AmountRule.sweep_above_floor,
        cadence=Cadence.monthly_on_day,
        anchor_date=date(2026, 10, 28),
    )
    lumpy = LumpyItem(
        name="Car insurance", amount_cents=120_000, cadence_months=6, next_due=date(2027, 1, 15)
    )
    db.add_all([paycheck, k401, sweep, lumpy])
    db.commit()
    return {"paycheck": paycheck, "runway_flow": k401, "sweep": sweep, "lumpy": lumpy, **buckets}
