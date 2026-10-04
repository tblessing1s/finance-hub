"""initial schema

Revision ID: 2eb6a5dcdb69
Revises:
Create Date: 2026-10-04 10:28:19.358068

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "2eb6a5dcdb69"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bucket",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("floor_cents", sa.BigInteger(), nullable=True),
        sa.Column("target_cents", sa.BigInteger(), nullable=True),
        sa.Column("balance_source", sa.String(length=32), server_default="manual", nullable=False),
        sa.Column("growth_rate_pct", sa.Numeric(precision=6, scale=3), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "balance_source IN ('manual', 'dashboard', 'derived')",
            name=op.f("ck_bucket_balance_source"),
        ),
        sa.CheckConstraint(
            "kind IN ('checking', 'hub', 'policy_cv', 'policy_loan', 'runway', 'lumpy_reserve', 'engine', 'roth', 'ira', 'k401')",
            name=op.f("ck_bucket_bucket_kind"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bucket")),
        sa.UniqueConstraint("name", name=op.f("uq_bucket_name")),
    )
    op.create_table(
        "category",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("monthly_target_cents", sa.BigInteger(), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "kind IN ('recurring', 'lumpy', 'transfer', 'ignore')",
            name=op.f("ck_category_category_kind"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_category")),
        sa.UniqueConstraint("name", name=op.f("uq_category_name")),
    )
    op.create_table(
        "engine_metric",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("deployed_cents", sa.BigInteger(), nullable=False),
        sa.Column("reserve_cents", sa.BigInteger(), nullable=False),
        sa.Column("extrinsic_week_cents", sa.BigInteger(), nullable=True),
        sa.Column("mtm_week_cents", sa.BigInteger(), nullable=True),
        sa.Column("return_26wk_pct", sa.Numeric(precision=7, scale=3), nullable=True),
        sa.Column("after_tax_26wk_pct", sa.Numeric(precision=7, scale=3), nullable=True),
        sa.Column("weeks_of_data", sa.Integer(), nullable=True),
        sa.Column("in_market", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("date", name=op.f("pk_engine_metric")),
    )
    op.create_table(
        "policy",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("base_premium_cents", sa.BigInteger(), nullable=False),
        sa.Column("fpur_schedule", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("seven_pay_limit_cents", sa.BigInteger(), nullable=False),
        sa.Column("cumulative_paid_cents", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("loan_rate_pct", sa.Numeric(precision=6, scale=3), nullable=False),
        sa.Column("loan_balance_cents", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("anniversary_date", sa.Date(), nullable=False),
        sa.Column("illustrated_cv", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("id = 1", name=op.f("ck_policy_singleton")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_policy")),
    )
    op.create_table(
        "scenario",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("levers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scenario")),
        sa.UniqueConstraint("name", name=op.f("uq_scenario_name")),
    )
    op.create_table(
        "sensor_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sensor", sa.String(length=40), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("thresholds", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sensor_config")),
        sa.UniqueConstraint("sensor", name=op.f("uq_sensor_config_sensor")),
    )
    op.create_table(
        "balance_snapshot",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bucket_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("balance_cents", sa.BigInteger(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "source IN ('manual', 'dashboard', 'derived')",
            name=op.f("ck_balance_snapshot_balance_source"),
        ),
        sa.ForeignKeyConstraint(
            ["bucket_id"],
            ["bucket.id"],
            name=op.f("fk_balance_snapshot_bucket_id_bucket"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_balance_snapshot")),
        sa.UniqueConstraint("bucket_id", "date", name="uq_balance_snapshot_bucket_date"),
    )
    op.create_index(
        op.f("ix_balance_snapshot_bucket_id"), "balance_snapshot", ["bucket_id"], unique=False
    )
    op.create_table(
        "category_rule",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("pattern", sa.String(length=200), nullable=False),
        sa.Column("match_kind", sa.String(length=32), server_default="contains", nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "match_kind IN ('contains', 'regex')", name=op.f("ck_category_rule_match_kind")
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["category.id"],
            name=op.f("fk_category_rule_category_id_category"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_category_rule")),
    )
    op.create_index(op.f("ix_category_rule_position"), "category_rule", ["position"], unique=False)
    op.create_table(
        "lumpy_item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("cadence_months", sa.Integer(), nullable=False),
        sa.Column("next_due", sa.Date(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("cadence_months > 0", name=op.f("ck_lumpy_item_positive_cadence")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["category.id"],
            name=op.f("fk_lumpy_item_category_id_category"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lumpy_item")),
    )
    op.create_table(
        "planned_flow",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("from_bucket_id", sa.Integer(), nullable=True),
        sa.Column("to_bucket_id", sa.Integer(), nullable=True),
        sa.Column("amount_cents", sa.BigInteger(), nullable=True),
        sa.Column("amount_rule", sa.String(length=32), nullable=True),
        sa.Column("cadence", sa.String(length=32), nullable=False),
        sa.Column("anchor_date", sa.Date(), nullable=False),
        sa.Column("stop_rule", sa.String(length=32), nullable=True),
        sa.Column("stop_date", sa.Date(), nullable=True),
        sa.Column("redirect_to_bucket_id", sa.Integer(), nullable=True),
        sa.Column("match_pattern", sa.String(length=200), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "amount_rule IN ('sweep_above_floor', 'remainder')",
            name=op.f("ck_planned_flow_amount_rule"),
        ),
        sa.CheckConstraint(
            "cadence IN ('per_paycheck', 'monthly_on_day', 'annual_on_date', 'weekly')",
            name=op.f("ck_planned_flow_cadence"),
        ),
        sa.CheckConstraint(
            "stop_rule IN ('bucket_reaches_target', 'headroom_zero', 'date')",
            name=op.f("ck_planned_flow_stop_rule"),
        ),
        sa.CheckConstraint(
            "stop_rule IS DISTINCT FROM 'date' OR stop_date IS NOT NULL",
            name=op.f("ck_planned_flow_stop_date_when_date_rule"),
        ),
        sa.CheckConstraint(
            "(amount_cents IS NULL) <> (amount_rule IS NULL)",
            name=op.f("ck_planned_flow_amount_xor_rule"),
        ),
        sa.CheckConstraint(
            "from_bucket_id IS NOT NULL OR to_bucket_id IS NOT NULL",
            name=op.f("ck_planned_flow_has_endpoint"),
        ),
        sa.CheckConstraint(
            "from_bucket_id IS NULL OR to_bucket_id IS NULL OR from_bucket_id <> to_bucket_id",
            name=op.f("ck_planned_flow_distinct_endpoints"),
        ),
        sa.ForeignKeyConstraint(
            ["from_bucket_id"],
            ["bucket.id"],
            name=op.f("fk_planned_flow_from_bucket_id_bucket"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["redirect_to_bucket_id"],
            ["bucket.id"],
            name=op.f("fk_planned_flow_redirect_to_bucket_id_bucket"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["to_bucket_id"],
            ["bucket.id"],
            name=op.f("fk_planned_flow_to_bucket_id_bucket"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_planned_flow")),
    )
    op.create_index(
        op.f("ix_planned_flow_from_bucket_id"), "planned_flow", ["from_bucket_id"], unique=False
    )
    op.create_index(
        op.f("ix_planned_flow_to_bucket_id"), "planned_flow", ["to_bucket_id"], unique=False
    )
    op.create_table(
        "transaction",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("account", sa.String(length=32), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("import_batch_id", sa.String(length=36), nullable=True),
        sa.Column("hash", sa.String(length=64), nullable=False),
        sa.Column("raw_row", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "account IN ('wf_checking', 'wf_card', 'capone_card')",
            name=op.f("ck_transaction_transaction_account"),
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["category.id"],
            name=op.f("fk_transaction_category_id_category"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transaction")),
        sa.UniqueConstraint("hash", name=op.f("uq_transaction_hash")),
    )
    op.create_index(
        op.f("ix_transaction_category_id"), "transaction", ["category_id"], unique=False
    )
    op.create_index(op.f("ix_transaction_date"), "transaction", ["date"], unique=False)
    op.create_index(
        op.f("ix_transaction_import_batch_id"), "transaction", ["import_batch_id"], unique=False
    )
    op.create_table(
        "ledger_entry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("iso_week", sa.String(length=8), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("from_bucket_id", sa.Integer(), nullable=True),
        sa.Column("to_bucket_id", sa.Integer(), nullable=True),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("planned_flow_id", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("scenario_id", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "kind IN ('forecast', 'actual')", name=op.f("ck_ledger_entry_ledger_kind")
        ),
        sa.CheckConstraint(
            "source IN ('sim', 'csv', 'manual', 'dashboard')",
            name=op.f("ck_ledger_entry_ledger_source"),
        ),
        sa.ForeignKeyConstraint(
            ["from_bucket_id"],
            ["bucket.id"],
            name=op.f("fk_ledger_entry_from_bucket_id_bucket"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["planned_flow_id"],
            ["planned_flow.id"],
            name=op.f("fk_ledger_entry_planned_flow_id_planned_flow"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["scenario_id"],
            ["scenario.id"],
            name=op.f("fk_ledger_entry_scenario_id_scenario"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["to_bucket_id"],
            ["bucket.id"],
            name=op.f("fk_ledger_entry_to_bucket_id_bucket"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ledger_entry")),
    )
    op.create_index(
        op.f("ix_ledger_entry_planned_flow_id"), "ledger_entry", ["planned_flow_id"], unique=False
    )
    op.create_index(
        "ix_ledger_entry_week_kind_scenario",
        "ledger_entry",
        ["iso_week", "kind", "scenario_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ledger_entry_week_kind_scenario", table_name="ledger_entry")
    op.drop_index(op.f("ix_ledger_entry_planned_flow_id"), table_name="ledger_entry")
    op.drop_table("ledger_entry")
    op.drop_index(op.f("ix_transaction_import_batch_id"), table_name="transaction")
    op.drop_index(op.f("ix_transaction_date"), table_name="transaction")
    op.drop_index(op.f("ix_transaction_category_id"), table_name="transaction")
    op.drop_table("transaction")
    op.drop_index(op.f("ix_planned_flow_to_bucket_id"), table_name="planned_flow")
    op.drop_index(op.f("ix_planned_flow_from_bucket_id"), table_name="planned_flow")
    op.drop_table("planned_flow")
    op.drop_table("lumpy_item")
    op.drop_index(op.f("ix_category_rule_position"), table_name="category_rule")
    op.drop_table("category_rule")
    op.drop_index(op.f("ix_balance_snapshot_bucket_id"), table_name="balance_snapshot")
    op.drop_table("balance_snapshot")
    op.drop_table("sensor_config")
    op.drop_table("scenario")
    op.drop_table("policy")
    op.drop_table("engine_metric")
    op.drop_table("category")
    op.drop_table("bucket")
