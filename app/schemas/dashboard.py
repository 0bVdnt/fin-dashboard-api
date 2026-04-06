from decimal import Decimal
from pydantic import BaseModel

from app.schemas.record import RecordResponse


class DashboardSummary(BaseModel):
    """Aggregate totals for a user or the entire system."""
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal


class CategoryTotal(BaseModel):
    """Total expenses grouped by category."""
    category: str
    total: Decimal


class TrendData(BaseModel):
    """Monthly income vs expense trend."""
    period: str  # Format: YYYY-MM
    income: Decimal
    expense: Decimal


class DashboardResponse(BaseModel):
    """Comprehensive dashboard payload."""
    summary: DashboardSummary
    category_breakdown: list[CategoryTotal]
    recent_activity: list[RecordResponse]
    trends: list[TrendData]
