from datetime import date, datetime
from typing import Any

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import TransactionAccount, enum_column


class Transaction(Base):
    """One imported bank or card row. `hash` of date+amount+description blocks duplicate imports."""

    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)  # outflows negative
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    account: Mapped[TransactionAccount] = mapped_column(
        enum_column(TransactionAccount, "transaction_account"), nullable=False
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("category.id", ondelete="SET NULL"), index=True
    )
    import_batch_id: Mapped[str | None] = mapped_column(String(36), index=True)
    hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    raw_row: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
