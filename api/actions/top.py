from datetime import datetime
from typing import Callable
from sqlalchemy import func, select

from db.models import QueryUrlTop


async def get_last_date_update_for(session: Callable, metrics_type: str):
    async with session() as s:
        result = await s.execute(
            select(func.max(QueryUrlTop.date)).where(QueryUrlTop.type == metrics_type)
        )
        last_date = result.scalar()

        return last_date if last_date else datetime(1900, 1, 1)
