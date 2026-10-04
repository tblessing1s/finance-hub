from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._mixins import TimestampMixin
from app.models.enums import CategoryKind, MatchKind, enum_column


class Category(TimestampMixin, Base):
    """Transfers between own buckets are kind `transfer` so they never count as spend."""

    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    monthly_target_cents: Mapped[int | None] = mapped_column(BigInteger)
    kind: Mapped[CategoryKind] = mapped_column(
        enum_column(CategoryKind, "category_kind"), nullable=False
    )


class CategoryRule(Base):
    """Ordered matching rules for imported transactions. First match (lowest position) wins."""

    __tablename__ = "category_rule"

    id: Mapped[int] = mapped_column(primary_key=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    pattern: Mapped[str] = mapped_column(String(200), nullable=False)
    match_kind: Mapped[MatchKind] = mapped_column(
        enum_column(MatchKind, "match_kind"),
        nullable=False,
        default=MatchKind.contains,
        server_default=MatchKind.contains.value,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("category.id", ondelete="CASCADE"), nullable=False
    )
