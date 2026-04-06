from decimal import Decimal

import pytest

from app.schemas.record import _validate_decimal_places
from app.utils.money import cents_to_dollars, dollars_to_cents


def test_dollars_to_cents():
    assert dollars_to_cents(Decimal("1500.50")) == 150050
    assert dollars_to_cents(Decimal("0.01")) == 1
    assert dollars_to_cents(Decimal("10")) == 1000


def test_cents_to_dollars():
    assert cents_to_dollars(150050) == Decimal("1500.50")
    assert cents_to_dollars(1) == Decimal("0.01")
    assert cents_to_dollars(0) == Decimal("0")


def test_roundtrip_conversion():
    """Ensure converting dollars -> cents -> dollars is lossless."""
    original = Decimal("9999.99")
    assert cents_to_dollars(dollars_to_cents(original)) == original


def test_validate_decimal_places():
    assert _validate_decimal_places(Decimal("10.50")) == Decimal("10.50")
    assert _validate_decimal_places(Decimal("10")) == Decimal("10")
    with pytest.raises(ValueError):
        _validate_decimal_places(Decimal("10.555"))
