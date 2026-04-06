from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.record import FinancialRecord


class RecordRepository:
    """Data access layer for FinancialRecord operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ──────────────────────────────────────
    # Create
    # ──────────────────────────────────────

    async def create(
        self,
        user_id: UUID,
        type: str,
        category: str,
        amount: int,
        record_date: date,
        description: str | None = None,
    ) -> FinancialRecord:
        """Insert a new financial record and return it"""
        record = FinancialRecord(
            user_id=user_id,
            type=type,
            category=category,
            amount=amount,
            date=record_date,
            description=description,
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    # ──────────────────────────────────────
    # Read
    # ──────────────────────────────────────

    async def get_by_id(self, record_id: UUID) -> FinancialRecord | None:
        """Fetch a non-deleted record by its ID"""
        result = await self.db.execute(
            select(FinancialRecord).where(
                and_(
                    FinancialRecord.id == record_id,
                    FinancialRecord.is_deleted.is_(False),
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_records(
        self,
        user_id: UUID | None = None,
        type: str | None = None,
        category: str | None = None,
        search: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[FinancialRecord], int]:
        """
        List records with optional filters.
        Returns (records, total_count) for pagination.
        """
        conditions: list = [FinancialRecord.is_deleted.is_(False)]

        if user_id is not None:
            conditions.append(FinancialRecord.user_id == user_id)
        if type is not None:
            conditions.append(FinancialRecord.type == type)
        if category is not None:
            conditions.append(FinancialRecord.category == category)
        if search is not None:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    FinancialRecord.category.ilike(search_term),
                    FinancialRecord.description.ilike(search_term),
                )
            )
        if date_from is not None:
            conditions.append(FinancialRecord.date >= date_from)
        if date_to is not None:
            conditions.append(FinancialRecord.date <= date_to)

        where_clause = and_(*conditions)

        # Total count for pagination
        count_query = (
            select(func.count()).select_from(FinancialRecord).where(where_clause)
        )
        total = (await self.db.execute(count_query)).scalar()

        # Paginated results ordered by date descending
        query = (
            select(FinancialRecord)
            .where(where_clause)
            .order_by(FinancialRecord.date.desc(), FinancialRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        records = list(result.scalars().all())

        return records, 0 if total is None else total

    # ──────────────────────────────────────
    # Update
    # ──────────────────────────────────────

    async def update(self, record_id: UUID, **fields) -> FinancialRecord | None:
        """Update specific fields of a record. Returns updated record or None."""
        update_data = {k: v for k, v in fields.items() if v is not None}
        if not update_data:
            return await self.get_by_id(record_id)

        await self.db.execute(
            update(FinancialRecord)
            .where(
                and_(
                    FinancialRecord.id == record_id,
                    FinancialRecord.is_deleted.is_(False),
                )
            )
            .values(**update_data)
        )
        await self.db.flush()
        return await self.get_by_id(record_id)

    # ──────────────────────────────────────
    # Delete (soft)
    # ──────────────────────────────────────

    async def soft_delete(self, record_id: UUID) -> FinancialRecord | None:
        """Mark a record as deleted without removing from the database."""
        await self.db.execute(
            update(FinancialRecord)
            .where(
                and_(
                    FinancialRecord.id == record_id,
                    FinancialRecord.is_deleted.is_(False),
                )
            )
            .values(is_deleted=True)
        )
        await self.db.flush()

        # Return the record even after soft-delete for the response
        result = await self.db.execute(
            select(FinancialRecord).where(FinancialRecord.id == record_id)
        )
        return result.scalar_one_or_none()
