import datetime as dt
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.utils.money import cents_to_dollars


class RecordType(str, Enum):
    """Type of financial entry."""

    INCOME = "income"
    EXPENSE = "expense"


def _validate_decimal_places(v: Decimal) -> Decimal:
    """Ensure the amount has at most 2 decimal places."""
    if v.as_tuple().exponent < -2:
        raise ValueError("Amount must have at most 2 decimal places")
    return v


# -------------------------------------------------------
# Request schemas
# -------------------------------------------------------


class CreateRecordRequest(BaseModel):
    """Schema for creating a new financial record."""

    type: RecordType
    category: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Record category (e.g., Salary, Groceries)",
    )
    amount: Decimal = Field(
        ...,
        gt=0,
        description="Amount in currency units (e.g., 1500.50). Max 2 decimal places.",
    )
    description: str | None = Field(
        None,
        max_length=500,
        description="Optional note or description",
    )
    date: dt.date = Field(..., description="Date of the transaction")

    model_config = {"extra": "forbid"}

    @field_validator("amount")
    @classmethod
    def check_decimal_places(cls, v: Decimal) -> Decimal:
        return _validate_decimal_places(v)


class UpdateRecordRequest(BaseModel):
    """Schema for updating an existing financial record (partial update)."""

    type: RecordType | None = None
    category: str | None = Field(None, min_length=1, max_length=50)
    amount: Decimal | None = Field(None, gt=0)
    description: str | None = Field(None, max_length=500)
    date: dt.date | None = None

    model_config = {"extra": "forbid"}

    @field_validator("amount")
    @classmethod
    def check_decimal_places(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            return _validate_decimal_places(v)
        return v


# -------------------------------------------------------
# Response schemas
# -------------------------------------------------------


class RecordResponse(BaseModel):
    """Financial record returned in API responses."""

    id: UUID
    user_id: UUID
    type: RecordType
    category: str
    amount: Decimal
    description: str | None
    date: dt.date
    created_at: dt.datetime
    updated_at: dt.datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_record(cls, record) -> "RecordResponse":
        """
        Build a response from a FinancialRecord ORM object.

        Converts the stored amount (cents integer) back to currency
        units using exact Decimal arithmetic:
            150050 cents  ->  Decimal('1500.50')
        """
        return cls(
            id=record.id,
            user_id=record.user_id,
            type=record.type,
            category=record.category,
            amount=cents_to_dollars(record.amount),
            description=record.description,
            date=record.date,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


# -------------------------------------------------------
# Query / filter schemas
# -------------------------------------------------------


class RecordListParams(BaseModel):
    """Query parameters for listing records with filters."""

    type: RecordType | None = None
    category: str | None = None
    search: str | None = Field(
        None, description="Search term for description or category"
    )
    date_from: dt.date | None = None
    date_to: dt.date | None = None
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page
