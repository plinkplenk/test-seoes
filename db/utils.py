from sqlalchemy import select, distinct, func

date_format = "%Y-%m-%d"


async def get_last_update_date(session, db_name):
    async with session() as s:
        result = await s.execute(func.max(db_name.date))

        return result.scalar()


async def add_last_update_date(session, db_name, date):
    async with session() as s:
        query = db_name(update_date=date)
        s.add(query)

        await s.commit()


async def get_all_dates(session, db_name):
    async with session() as s:
        query = select(distinct(db_name.update_date)).order_by(db_name.update_date.desc())
        res = await s.execute(query)
        res = res.fetchall()
        return res
