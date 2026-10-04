"""Integer cents in the database, decimal dollars in the API, formatted only in the UI."""

from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated

from pydantic import BeforeValidator, Field

CENT = Decimal("0.01")

# Inbound: a dollar amount with at most two decimal places.
Money = Annotated[Decimal, Field(max_digits=14, decimal_places=2)]


def to_cents(value: Decimal | None) -> int | None:
    if value is None:
        return None
    return int((Decimal(value) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def from_cents(cents: int | None) -> Decimal | None:
    if cents is None:
        return None
    return (Decimal(cents) / 100).quantize(CENT)


# Outbound: reads a *_cents attribute and renders it as dollars.
MoneyOut = Annotated[Decimal, BeforeValidator(from_cents)]
