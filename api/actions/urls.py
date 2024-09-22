from db.dals import UrlDAL


async def _add_new_urls(urls, session):
    async with session() as s:
        order_dal = UrlDAL(s)
        order_id = await order_dal.add_new_urls(
            urls
        )
        return order_id


async def _get_urls_with_pagination(
        page, 
        per_page,
        date_start, 
        date_end, 
        state, 
        state_date, 
        metric_type, 
        state_type, 
        list_name, 
        session,
        general_session,
        ):
    async with session() as s:
        url_dal = UrlDAL(s)
        urls = await url_dal.get_urls_with_pagination(
            page, per_page, date_start, date_end, state, state_date, metric_type, state_type, list_name, general_session,
        )
        return urls


async def _get_urls_with_pagination_and_like(
        page, 
        per_page, 
        date_start, 
        date_end, 
        search_text, 
        state, 
        state_date, 
        metric_type, 
        state_type,
        list_name, 
        session,
        general_session,
        ):
    async with session() as s:
        url_dal = UrlDAL(s)
        urls = await url_dal.get_urls_with_pagination_and_like(
            page, per_page, date_start, date_end, search_text, state, state_date, metric_type, state_type, list_name, general_session,
        )
        return urls


async def _get_urls_with_pagination_sort(
        page, 
        per_page, 
        date_start, 
        date_end, 
        sort_desc,
        list_name, 
        session,
        general_session):
    async with session() as s:
        url_dal = UrlDAL(s)
        urls = await url_dal.get_urls_with_pagination_sort(
            page, per_page, date_start, date_end, sort_desc, list_name, general_session,
        )
        return urls


async def _get_urls_with_pagination_and_like_sort(
        page, 
        per_page, 
        date_start, 
        date_end, 
        search_text, 
        sort_desc,
        list_name,
        session,
        general_session,
        ):
    async with session() as s:
        url_dal = UrlDAL(s)
        urls = await url_dal.get_urls_with_pagination_and_like_sort(
            page, per_page, date_start, date_end, search_text, sort_desc, list_name, general_session
        )
        return urls
