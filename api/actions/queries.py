from db.dals import QueryDAL


async def _add_new_urls(urls, session):
    async with session() as s:
        order_dal = QueryDAL(s)
        order_id = await order_dal.add_new_urls(
            urls
        )
        return order_id


async def _get_urls_with_pagination_query(page, per_page, date_start, date_end, state, state_date, metric_type, state_type, session):
    async with session() as s:
        url_dal = QueryDAL(s)
        urls = await url_dal.get_urls_with_pagination(
            page, per_page, date_start, date_end, state, state_date, metric_type, state_type,
        )
        return urls


async def _get_urls_with_pagination_and_like_query(page, per_page, date_start, date_end, search_text, state, state_date, metric_type, state_type, session):
    async with session() as s:
        url_dal = QueryDAL(s)
        urls = await url_dal.get_urls_with_pagination_and_like(
            page, per_page, date_start, date_end, search_text, state, state_date, metric_type, state_type
        )
        return urls


async def _get_urls_with_pagination_sort_query(page, per_page, date_start, date_end, sort_desc, session):
    async with session() as s:
        url_dal = QueryDAL(s)
        urls = await url_dal.get_urls_with_pagination_sort(
            page, per_page, date_start, date_end, sort_desc
        )
        return urls


async def _get_urls_with_pagination_and_like_sort_query(page, per_page, date_start, date_end, search_text, sort_desc,
                                                  session):
    async with session() as s:
        url_dal = QueryDAL(s)
        urls = await url_dal.get_urls_with_pagination_and_like_sort(
            page, per_page, date_start, date_end, search_text, sort_desc
        )
        return urls
