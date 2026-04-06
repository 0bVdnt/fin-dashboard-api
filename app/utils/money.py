"""
Centralized monetary conversion utilities.

All monetary values are stored as integer cents in the database
to avoid floating-point precision errors. These helpers provide
exact conversion using Python's Decimal module.
"""

from decimal import Decimal


def dollars_to_cents(amount: Decimal) -> int:
    """
    Convert a currency amount to cents using exact Decimal arithmetic.

    Decimal('1500.50') * 100  ->  Decimal('150050')  ->  int 150050
    No floating-point involved at any step.
    """
    return int(amount * 100)


def cents_to_dollars(cents: int) -> Decimal:
    """
    Convert cents back to currency units using exact Decimal arithmetic.

    150050 cents  ->  Decimal('150050') / Decimal('100')  ->  Decimal('1500.50')
    """
    return Decimal(cents) / Decimal(100)
