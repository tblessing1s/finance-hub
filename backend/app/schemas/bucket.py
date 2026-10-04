from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BalanceSource, BucketKind
from app.schemas.money import Money, MoneyOut

Pct = Decimal


class BucketBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    kind: BucketKind
    floor: Money | None = Field(
        default=None, ge=0, description="Balance the sim will not sweep below"
    )
    target: Money | None = Field(
        default=None, ge=0, description="Balance at which a stop rule fires"
    )
    balance_source: BalanceSource = BalanceSource.manual
    growth_rate_pct: Pct | None = Field(
        default=None, ge=-100, le=100, max_digits=6, decimal_places=3
    )


class BucketCreate(BucketBase):
    pass


class BucketUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    kind: BucketKind | None = None
    floor: Money | None = Field(default=None, ge=0)
    target: Money | None = Field(default=None, ge=0)
    balance_source: BalanceSource | None = None
    growth_rate_pct: Pct | None = Field(
        default=None, ge=-100, le=100, max_digits=6, decimal_places=3
    )


class BucketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    kind: BucketKind
    floor: MoneyOut | None = Field(default=None, validation_alias="floor_cents")
    target: MoneyOut | None = Field(default=None, validation_alias="target_cents")
    balance_source: BalanceSource
    growth_rate_pct: Decimal | None = None
    created_at: datetime
    updated_at: datetime
