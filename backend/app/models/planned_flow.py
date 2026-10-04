from datetime import date

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models._mixins import TimestampMixin
from app.models.bucket import Bucket
from app.models.enums import AmountRule, Cadence, StopRule, enum_column


class PlannedFlow(TimestampMixin, Base):
    """A recurring movement of money. The Plan screen edits these rows.

    Either from_bucket or to_bucket may be null: a paycheck has no from-bucket, a bill has no
    to-bucket. Exactly one of amount_cents / amount_rule is set.
    """

    __tablename__ = "planned_flow"
    __table_args__ = (
        CheckConstraint(
            "(amount_cents IS NULL) <> (amount_rule IS NULL)",
            name="amount_xor_rule",
        ),
        CheckConstraint(
            "from_bucket_id IS NOT NULL OR to_bucket_id IS NOT NULL",
            name="has_endpoint",
        ),
        CheckConstraint(
            "from_bucket_id IS NULL OR to_bucket_id IS NULL OR from_bucket_id <> to_bucket_id",
            name="distinct_endpoints",
        ),
        CheckConstraint(
            "stop_rule IS DISTINCT FROM 'date' OR stop_date IS NOT NULL",
            name="stop_date_when_date_rule",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    from_bucket_id: Mapped[int | None] = mapped_column(
        ForeignKey("bucket.id", ondelete="RESTRICT"), index=True
    )
    to_bucket_id: Mapped[int | None] = mapped_column(
        ForeignKey("bucket.id", ondelete="RESTRICT"), index=True
    )
    amount_cents: Mapped[int | None] = mapped_column(BigInteger)
    amount_rule: Mapped[AmountRule | None] = mapped_column(enum_column(AmountRule, "amount_rule"))
    cadence: Mapped[Cadence] = mapped_column(enum_column(Cadence, "cadence"), nullable=False)
    anchor_date: Mapped[date] = mapped_column(Date, nullable=False)
    stop_rule: Mapped[StopRule | None] = mapped_column(enum_column(StopRule, "stop_rule"))
    stop_date: Mapped[date | None] = mapped_column(Date)
    redirect_to_bucket_id: Mapped[int | None] = mapped_column(
        ForeignKey("bucket.id", ondelete="SET NULL")
    )
    # Substring matched against imported transaction descriptions to write the actual row.
    match_pattern: Mapped[str | None] = mapped_column(String(200))
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    from_bucket: Mapped[Bucket | None] = relationship(foreign_keys=[from_bucket_id])
    to_bucket: Mapped[Bucket | None] = relationship(foreign_keys=[to_bucket_id])
    redirect_to_bucket: Mapped[Bucket | None] = relationship(foreign_keys=[redirect_to_bucket_id])
