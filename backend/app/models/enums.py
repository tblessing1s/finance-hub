"""Closed vocabularies from the brief. Stored as VARCHAR + CHECK constraint, not native enums,
so adding a value later is a one-line migration instead of an ALTER TYPE."""

from enum import StrEnum

import sqlalchemy as sa


class BucketKind(StrEnum):
    checking = "checking"
    hub = "hub"
    policy_cv = "policy_cv"
    policy_loan = "policy_loan"
    runway = "runway"
    lumpy_reserve = "lumpy_reserve"
    engine = "engine"
    roth = "roth"
    ira = "ira"
    k401 = "k401"


class BalanceSource(StrEnum):
    manual = "manual"
    dashboard = "dashboard"
    derived = "derived"


class AmountRule(StrEnum):
    sweep_above_floor = "sweep_above_floor"
    remainder = "remainder"


class Cadence(StrEnum):
    per_paycheck = "per_paycheck"
    monthly_on_day = "monthly_on_day"
    annual_on_date = "annual_on_date"
    weekly = "weekly"


class StopRule(StrEnum):
    bucket_reaches_target = "bucket_reaches_target"
    headroom_zero = "headroom_zero"
    date = "date"


class LedgerKind(StrEnum):
    forecast = "forecast"
    actual = "actual"


class LedgerSource(StrEnum):
    sim = "sim"
    csv = "csv"
    manual = "manual"
    dashboard = "dashboard"


class TransactionAccount(StrEnum):
    wf_checking = "wf_checking"
    wf_card = "wf_card"
    capone_card = "capone_card"


class CategoryKind(StrEnum):
    recurring = "recurring"
    lumpy = "lumpy"
    transfer = "transfer"
    ignore = "ignore"


class MatchKind(StrEnum):
    contains = "contains"
    regex = "regex"


def enum_column(enum_cls: type[StrEnum], name: str) -> sa.Enum:
    """VARCHAR-backed enum with a named CHECK constraint."""
    return sa.Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=32,
        values_callable=lambda e: [m.value for m in e],
    )
