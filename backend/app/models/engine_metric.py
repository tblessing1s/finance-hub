from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EngineMetric(Base):
    """One row per day, written by the pull from the Rotation Dashboard."""

    __tablename__ = "engine_metric"

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    deployed_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reserve_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    extrinsic_week_cents: Mapped[int | None] = mapped_column(BigInteger)
    mtm_week_cents: Mapped[int | None] = mapped_column(BigInteger)
    return_26wk_pct: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))
    after_tax_26wk_pct: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))
    weeks_of_data: Mapped[int | None] = mapped_column(Integer)
    in_market: Mapped[bool | None] = mapped_column(Boolean)
