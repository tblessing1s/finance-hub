from datetime import date

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._mixins import TimestampMixin


class LumpyItem(TimestampMixin, Base):
    """Irregular expense. Accrual per month = amount / cadence_months."""

    __tablename__ = "lumpy_item"
    __table_args__ = (CheckConstraint("cadence_months > 0", name="positive_cadence"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    cadence_months: Mapped[int] = mapped_column(Integer, nullable=False)
    next_due: Mapped[date] = mapped_column(Date, nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("category.id", ondelete="SET NULL"))
