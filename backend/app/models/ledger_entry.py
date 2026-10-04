from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import LedgerKind, LedgerSource, enum_column


class LedgerEntry(Base):
    """The spine. Forecast rows are rewritten per sim run; actual rows are never touched by it."""

    __tablename__ = "ledger_entry"
    __table_args__ = (
        Index("ix_ledger_entry_week_kind_scenario", "iso_week", "kind", "scenario_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    iso_week: Mapped[str] = mapped_column(String(8), nullable=False)  # e.g. 2026-W41
    date: Mapped[date] = mapped_column(Date, nullable=False)
    from_bucket_id: Mapped[int | None] = mapped_column(ForeignKey("bucket.id", ondelete="RESTRICT"))
    to_bucket_id: Mapped[int | None] = mapped_column(ForeignKey("bucket.id", ondelete="RESTRICT"))
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    planned_flow_id: Mapped[int | None] = mapped_column(
        ForeignKey("planned_flow.id", ondelete="SET NULL"), index=True
    )
    kind: Mapped[LedgerKind] = mapped_column(enum_column(LedgerKind, "ledger_kind"), nullable=False)
    scenario_id: Mapped[int | None] = mapped_column(
        ForeignKey("scenario.id", ondelete="CASCADE")
    )  # null = base plan
    source: Mapped[LedgerSource] = mapped_column(
        enum_column(LedgerSource, "ledger_source"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
