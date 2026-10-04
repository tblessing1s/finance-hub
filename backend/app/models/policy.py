from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, Date, Integer, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._mixins import TimestampMixin


class Policy(TimestampMixin, Base):
    """Single config row for the Ameritas policy. id is pinned to 1 by a CHECK constraint.

    fpur_schedule and illustrated_cv are lists of {"policy_year": int, "amount_cents": int}
    so the sim can interpolate the illustration curve.
    """

    __tablename__ = "policy"
    __table_args__ = (CheckConstraint("id = 1", name="singleton"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    base_premium_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fpur_schedule: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    seven_pay_limit_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    cumulative_paid_cents: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    loan_rate_pct: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    loan_balance_cents: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    anniversary_date: Mapped[date] = mapped_column(Date, nullable=False)
    illustrated_cv: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
