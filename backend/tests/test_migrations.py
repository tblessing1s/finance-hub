from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from app.db import Base

EXPECTED_TABLES = {
    "bucket",
    "planned_flow",
    "ledger_entry",
    "balance_snapshot",
    "transaction",
    "category",
    "lumpy_item",
    "scenario",
    "engine_metric",
    "policy",
    "category_rule",
    "sensor_config",
}


def test_every_table_in_the_brief_exists(engine):
    tables = set(inspect(engine).get_table_names()) - {"alembic_version"}
    assert tables == EXPECTED_TABLES


def test_migrations_match_models(engine):
    """The head migration and Base.metadata agree, so autogenerate would be a no-op."""
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn, opts={"compare_type": True})
        diff = compare_metadata(ctx, Base.metadata)
    assert diff == [], diff
