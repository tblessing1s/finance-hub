from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import BalanceSource, enum_column


class BalanceSnapshot(Base):
    """Latest snapshot plus later actuals gives the live balance."""

    __tablename__ = "balance_snapshot"
    __table_args__ = (
        UniqueConstraint("bucket_id", "date", name="uq_balance_snapshot_bucket_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    bucket_id: Mapped[int] = mapped_column(
        ForeignKey("bucket.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    balance_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source: Mapped[BalanceSource] = mapped_column(
        enum_column(BalanceSource, "balance_source"), nullable=False
    )
