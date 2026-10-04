from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._mixins import TimestampMixin


class SensorConfig(TimestampMixin, Base):
    """Tunable thresholds per sensor, e.g. {"green_min_cents": 750000, "amber_band_cents": 50000}.
    Keyed by sensor name so a threshold change is a row update, not a deploy."""

    __tablename__ = "sensor_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    sensor: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    thresholds: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
