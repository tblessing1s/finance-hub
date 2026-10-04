from datetime import date, datetime
from typing import Any

from pydantic import AliasPath, BaseModel, ConfigDict, Field, model_validator

from app.models.enums import AmountRule, Cadence, StopRule
from app.schemas.money import Money, MoneyOut


def check_flow_invariants(d: dict[str, Any]) -> None:
    """Shared by create and by the merged create+patch in the router.

    Mirrors the CHECK constraints on planned_flow so the client gets a 422 with a
    readable message rather than a 500 from the database.
    """
    amount, rule = d.get("amount"), d.get("amount_rule")
    if (amount is None) == (rule is None):
        raise ValueError("set exactly one of amount or amount_rule")
    if amount is not None and amount <= 0:
        raise ValueError("amount must be positive")
    src, dst = d.get("from_bucket_id"), d.get("to_bucket_id")
    if src is None and dst is None:
        raise ValueError("a flow needs a from_bucket or a to_bucket")
    if src is not None and src == dst:
        raise ValueError("from_bucket and to_bucket must differ")
    if rule is not None and src is None:
        raise ValueError(f"amount_rule {rule.value} needs a from_bucket to read the balance from")
    stop_rule, stop_date = d.get("stop_rule"), d.get("stop_date")
    if stop_rule == StopRule.date and stop_date is None:
        raise ValueError("stop_rule 'date' needs a stop_date")
    if stop_rule != StopRule.date and stop_date is not None:
        raise ValueError("stop_date only applies when stop_rule is 'date'")
    if stop_rule == StopRule.bucket_reaches_target and dst is None:
        raise ValueError("stop_rule 'bucket_reaches_target' needs a to_bucket with a target")
    redirect = d.get("redirect_to_bucket_id")
    if redirect is not None and stop_rule is None:
        raise ValueError("redirect_to_bucket only applies once a stop_rule fires")
    if redirect is not None and redirect == dst:
        raise ValueError("redirect_to_bucket must differ from to_bucket")


class PlannedFlowBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    from_bucket_id: int | None = None
    to_bucket_id: int | None = None
    amount: Money | None = None
    amount_rule: AmountRule | None = None
    cadence: Cadence
    anchor_date: date
    stop_rule: StopRule | None = None
    stop_date: date | None = None
    redirect_to_bucket_id: int | None = None
    match_pattern: str | None = Field(default=None, max_length=200)
    active: bool = True


class PlannedFlowCreate(PlannedFlowBase):
    @model_validator(mode="after")
    def _invariants(self) -> "PlannedFlowCreate":
        check_flow_invariants(self.model_dump())
        return self


class PlannedFlowUpdate(BaseModel):
    """Partial update. Fields left out are untouched; fields sent as null are cleared."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    from_bucket_id: int | None = None
    to_bucket_id: int | None = None
    amount: Money | None = None
    amount_rule: AmountRule | None = None
    cadence: Cadence | None = None
    anchor_date: date | None = None
    stop_rule: StopRule | None = None
    stop_date: date | None = None
    redirect_to_bucket_id: int | None = None
    match_pattern: str | None = Field(default=None, max_length=200)
    active: bool | None = None


class PlannedFlowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    from_bucket_id: int | None
    to_bucket_id: int | None
    from_bucket_name: str | None = Field(
        default=None, validation_alias=AliasPath("from_bucket", "name")
    )
    to_bucket_name: str | None = Field(
        default=None, validation_alias=AliasPath("to_bucket", "name")
    )
    amount: MoneyOut | None = Field(default=None, validation_alias="amount_cents")
    amount_rule: AmountRule | None
    cadence: Cadence
    anchor_date: date
    stop_rule: StopRule | None
    stop_date: date | None
    redirect_to_bucket_id: int | None
    redirect_to_bucket_name: str | None = Field(
        default=None, validation_alias=AliasPath("redirect_to_bucket", "name")
    )
    match_pattern: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
