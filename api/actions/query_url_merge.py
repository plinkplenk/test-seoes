from typing import Callable

from db.dals import MetricQueryDAL, MergeDAL


async def _get_approach_query(session):
    async with session() as s:
        order_dal = MetricQueryDAL(s)
        queries = await order_dal.get_approach_query(session
        )
        return queries


async def _get_merge_with_pagination(date, page, per_page, session: Callable):
    async with session() as s:
        url_dal = MergeDAL(s)
        urls = await url_dal.get_merge_with_pagination(
            date, page, per_page
        )
        return urls


async def _get_merge_query(date_start, date_end, queries, session: Callable):
    async with session() as s:
        url_dal = MergeDAL(s)
        queries = await url_dal.get_merge_queries(date_start, date_end, queries)
        return queries


async def _get_merge_with_pagination_sort(date, search_text, page, per_page, session: Callable):
    async with session() as s:
        url_dal = MergeDAL(s)
        urls = await url_dal.get_merge_with_pagination_sort(
            date, search_text, page, per_page
        )
        return urls


async def _get_merge_with_pagination_and_like(date, search_text_url, search_text_query, page, per_page,
                                              session: Callable):
    async with session() as s:
        url_dal = MergeDAL(s)
        urls = await url_dal.get_merge_with_pagination_and_like(
            date, search_text_url, search_text_query, page, per_page
        )
        return urls


async def _get_merge_with_pagination_and_like_sort(date, search_text_url, search_text_query, sort_desc, page, per_page,
                                                   session: Callable):
    async with session() as s:
        url_dal = MergeDAL(s)
        urls = await url_dal.get_merge_with_pagination_and_like_sort(
            date, search_text_url, search_text_query, sort_desc, page, per_page
        )
        return urls
