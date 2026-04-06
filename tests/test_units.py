from decimal import Decimal
import pytest

from app.services.record_service import RecordService
from app.schemas.record import _validate_decimal_places

def test_dollars_to_cents():
    assert RecordService._dollars_to_cents(Decimal('1500.50')) == 150050
    assert RecordService._dollars_to_cents(Decimal('0.01')) == 1
    assert RecordService._dollars_to_cents(Decimal('10')) == 1000

def test_validate_decimal_places():
    assert _validate_decimal_places(Decimal('10.50')) == Decimal('10.50')
    assert _validate_decimal_places(Decimal('10')) == Decimal('10')
    with pytest.raises(ValueError):
        _validate_decimal_places(Decimal('10.555'))
