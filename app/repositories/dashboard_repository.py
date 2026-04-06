from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.record import FinancialRecord


class DashboardRepository:
    """Data access for dashboard aggregations and summaries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_totals_by_type(self, user_id: UUID | None = None) -> dict[str, int]:
        """Return total amount grouped by type (income vs expense)."""
        conditions: list = [FinancialRecord.is_deleted.is_(False)]
        if user_id is not None:
            conditions.append(FinancialRecord.user_id == user_id)

        query = (
            select(FinancialRecord.type, func.sum(FinancialRecord.amount))
            .where(and_(*conditions))
            .group_by(FinancialRecord.type)
        )
        result = await self.db.execute(query)
        rows = result.all()
        return {str(r[0]): int(r[1]) if r[1] else 0 for r in rows}

    async def get_category_breakdown(self, user_id: UUID | None = None) -> list[tuple[str, int]]:
        """Return total expense amounts grouped by category."""
        conditions: list = [
            FinancialRecord.is_deleted.is_(False),
            FinancialRecord.type == "expense",
        ]
        if user_id is not None:
            conditions.append(FinancialRecord.user_id == user_id)

        query = (
            select(FinancialRecord.category, func.sum(FinancialRecord.amount))
            .where(and_(*conditions))
            .group_by(FinancialRecord.category)
            .order_by(func.sum(FinancialRecord.amount).desc())
        )
        result = await self.db.execute(query)
        return [(str(r[0]), int(r[1]) if r[1] else 0) for r in result.all()]

    async def get_monthly_trends(self, user_id: UUID | None = None) -> list[tuple[str, str, int]]:
        """
        Return income and expense totals grouped by month.
        Format of returned tuples: (YYYY-MM, type, amount)
        """
        conditions: list = [FinancialRecord.is_deleted.is_(False)]
        if user_id is not None:
            conditions.append(FinancialRecord.user_id == user_id)

        # func.to_char converts the date to 'YYYY-MM' format in PostgreSQL
        month_label = func.to_char(FinancialRecord.date, "YYYY-MM").label("month")
        
        query = (
            select(month_label, FinancialRecord.type, func.sum(FinancialRecord.amount))
            .where(and_(*conditions))
            .group_by(month_label, FinancialRecord.type)
            .order_by(month_label)
        )
        result = await self.db.execute(query)
        return [(str(r[0]), str(r[1]), int(r[2]) if r[2] else 0) for r in result.all()]

    async def get_recent_activity(
        self, limit: int = 5, user_id: UUID | None = None
    ) -> list[FinancialRecord]:
        """Return the most recent records."""
        conditions: list = [FinancialRecord.is_deleted.is_(False)]
        if user_id is not None:
            conditions.append(FinancialRecord.user_id == user_id)

        query = (
            select(FinancialRecord)
            .where(and_(*conditions))
            .order_by(FinancialRecord.date.desc(), FinancialRecord.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
