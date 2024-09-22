from typing import Callable

from db.dals import IndicatorDAL


async def _add_new_indicators(indicators, session):
    async with session() as s:
        order_dal = IndicatorDAL(s)
        await order_dal.add_new_indicator(indicators)


async def _get_indicators_from_db(start_date, end_date, session):
    async with session() as s:
        order_dal = IndicatorDAL(s)
        indicators = await order_dal.get_indicators_from_db(start_date, end_date)
    return indicators


async def _add_top(tops, session):
    async with session() as s:
        order_dal = IndicatorDAL(s)
        await order_dal.add_top(tops)


async def _get_top_query(start_date, end_date, top, session: Callable):
    async with session() as s:
        order_dal = IndicatorDAL(s)
        result = await order_dal.get_top_query(start_date, end_date, top)
        return result


async def _get_top_url(start_date, end_date, top, session: Callable):
    async with session() as s:
        order_dal = IndicatorDAL(s)
        result = await order_dal.get_top_url(start_date, end_date, top)
        return result

