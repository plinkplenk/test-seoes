from datetime import datetime
from typing import Callable

from psycopg2 import IntegrityError
from sqlalchemy import func, select

from const import date_format, date_format_2
from db.models import LastUpdateDate


async def add_last_load_date(async_session: Callable, metrics_type: str) -> None:
    async with async_session() as session:

        current_date = datetime.strptime(datetime.now().strftime(date_format), date_format)
        last_update_date = LastUpdateDate(date=current_date, metrics_type=metrics_type)
                
        result = await session.execute(
            select(LastUpdateDate).filter(LastUpdateDate.date == current_date, LastUpdateDate.metrics_type == metrics_type)
            )
        existing_record = result.scalars().first()
            
        if not existing_record:
            try:
                # Добавляем объект в сессию
                session.add(last_update_date)
                # Фиксируем изменения
                await session.commit()
                print(f"Date {current_date} added successfully.")
            except IntegrityError:
                # Если запись уже существует, выполняем откат
                await session.rollback()
                print(f"Date {current_date} already exists.")
        else:
            print(f"Date {current_date} already exists.")


async def get_last_load_date(async_session: Callable, metrics_type: str) -> str | None:
    async with async_session() as s:
        # Создаем запрос для получения записи с максимальным ID
        stmt = (
            select(LastUpdateDate).where(LastUpdateDate.metrics_type == metrics_type)
            .order_by(LastUpdateDate.id.desc())
            .limit(1)
        )
            
        result = await s.execute(stmt)
        record = result.scalars().first()

        if record:
            return record.date.strftime(date_format_2)
    
    return None


async def get_last_date(async_session: Callable, metric_type):
    async with async_session() as s:
        res = (await s.execute(select(func.max(metric_type.date)))).scalars().first()
    
    return res.strftime(date_format_2) if res else "1900-01-01"