from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Scenario(Base):
    """A saved lever set. Levers: engine_return_pct, fpur_annual_cents, monthly_burn_cents,
    new_income_cents, new_income_start, retirement_age, inflation_pct, surplus_override_cents."""

    __tablename__ = "scenario"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    levers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
