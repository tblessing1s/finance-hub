from decimal import Decimal

from sqlalchemy import BigInteger, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._mixins import TimestampMixin
from app.models.enums import BalanceSource, BucketKind, enum_column


class Bucket(TimestampMixin, Base):
    """One row per place money sits. The policy loan is a negative bucket."""

    __tablename__ = "bucket"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    kind: Mapped[BucketKind] = mapped_column(enum_column(BucketKind, "bucket_kind"), nullable=False)
    floor_cents: Mapped[int | None] = mapped_column(BigInteger)
    target_cents: Mapped[int | None] = mapped_column(BigInteger)
    balance_source: Mapped[BalanceSource] = mapped_column(
        enum_column(BalanceSource, "balance_source"),
        nullable=False,
        default=BalanceSource.manual,
        server_default=BalanceSource.manual.value,
    )
    # Annual growth applied by the simulator (Roth, IRA, 401k, runway). Null = no growth.
    growth_rate_pct: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
