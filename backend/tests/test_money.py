from decimal import Decimal

import pytest

from app.schemas.money import from_cents, to_cents


@pytest.mark.parametrize(
    ("dollars", "cents"),
    [("0", 0), ("0.01", 1), ("7500", 750_000), ("1234.56", 123_456), ("0.005", 1), ("0.004", 0)],
)
def test_to_cents(dollars, cents):
    assert to_cents(Decimal(dollars)) == cents


def test_from_cents_two_places():
    assert from_cents(750_000) == Decimal("7500.00")
    assert str(from_cents(5)) == "0.05"
    assert from_cents(None) is None
    assert to_cents(None) is None
