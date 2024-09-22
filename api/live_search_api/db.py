from datetime import datetime
from sqlalchemy import and_, asc, desc, func, select

from api.config.models import LiveSearchListQuery, QueryLiveSearchGoogle, QueryLiveSearchYandex

from const import date_format

async def get_urls_with_pagination(
    page, 
    per_page, 
    date_start, 
    date_end, 
    state, 
    state_date, 
    metric_type, 
    state_type,
    list_id,
    lr_list_id,
    search_system,
    session,
):
    if search_system == "Yandex":
        database = QueryLiveSearchYandex
    elif search_system == "Google":
        database = QueryLiveSearchGoogle
    else:
        print("Поисковая система не указана")
    
    if metric_type == "P":
        pointer = database.position

    if not state:
        sub = select(LiveSearchListQuery).where(LiveSearchListQuery.list_id == list_id).offset(page).limit(per_page).subquery()

        all_queries = (await session.execute(select(LiveSearchListQuery.query).where(LiveSearchListQuery.list_id == list_id).offset(page).limit(per_page))).scalars().all()

        query = (
            select(
                database.date,
                database.url,
                database.position,
                sub.c.query,
            ).where(database.lr_list_id == lr_list_id)
            .join(sub, database.query_id == sub.c.id)
            .group_by(
                database.date,
                database.url,
                database.position,
                sub.c.id,
                sub.c.query,
                sub.c.list_id,
            )
            .having(and_(
                database.date <= date_end,
                database.date >= date_start
            ))
        )
    
    elif state == "decrease":
        sub_get_id = (
            select(
                database.id,  # Выбираем только нужные столбцы
                database.query_id,
                database.url,
                database.position,
                database.date
            ).where(database.lr_list_id == lr_list_id)
            .join(LiveSearchListQuery, database.query_id == LiveSearchListQuery.id)
            .where(
                and_(
                    database.date == state_date,
                    LiveSearchListQuery.list_id == list_id
                )
            )
            .order_by(desc(pointer))
            .offset(page)
            .limit(per_page)
            .subquery()  # Создаем подзапрос
        )

        # Алиас для подзапроса LiveSearchListQuery
        sub = select(
            LiveSearchListQuery.id,
            LiveSearchListQuery.query,
            LiveSearchListQuery.list_id
        ).join(sub_get_id, LiveSearchListQuery.id == sub_get_id.c.query_id).subquery()

        all_queries = (await session.execute(select(LiveSearchListQuery.query).where(LiveSearchListQuery.list_id == list_id).offset(page).limit(per_page))).scalars().all()

        # Основной запрос, используя алиасы
        query = (
            select(
                database.date,
                database.url,
                database.position,
                sub.c.query,
            ).where(database.lr_list_id == lr_list_id)
            .join(sub, database.query_id == sub.c.id)
            .group_by(
                database.date,
                database.url,
                database.position,
                sub.c.id,
                sub.c.query,
                sub.c.list_id,
            )
            .having(and_(
                database.date <= date_end,
                database.date >= date_start
            ))
        )
    
    elif state == "increase":
        sub_get_id = (
            select(
                database.id,  # Выбираем только нужные столбцы
                database.query_id,
                database.url,
                database.position,
                database.date
            )
            .join(LiveSearchListQuery, database.query_id == LiveSearchListQuery.id)
            .where(
                and_(
                    database.date == state_date,
                    LiveSearchListQuery.list_id == list_id
                )
            ).where(database.lr_list_id == lr_list_id)
            .order_by(asc(pointer))
            .offset(page)
            .limit(per_page)
            .subquery()  # Создаем подзапрос
        )

        # Алиас для подзапроса LiveSearchListQuery
        sub = select(
            LiveSearchListQuery.id,
            LiveSearchListQuery.query,
            LiveSearchListQuery.list_id
        ).join(sub_get_id, LiveSearchListQuery.id == sub_get_id.c.query_id).subquery()

        all_queries = (await session.execute(select(LiveSearchListQuery.query).where(LiveSearchListQuery.list_id == list_id).offset(page).limit(per_page))).scalars().all()

        # Основной запрос, используя алиасы
        query = (
            select(
                database.date,
                database.url,
                database.position,
                sub.c.query,
            ).where(database.lr_list_id == lr_list_id)
            .join(sub, database.query_id == sub.c.id)
            .group_by(
                database.date,
                database.url,
                database.position,
                sub.c.id,
                sub.c.query,
                sub.c.list_id,
            )
            .having(and_(
                database.date <= date_end,
                database.date >= date_start
            ))
        )
        
    res = await session.execute(query)
    product_row = res.fetchall()
    
    if product_row:
        return product_row, all_queries


async def get_urls_with_pagination_and_like(
    page, 
    per_page, 
    date_start, 
    date_end,
    search_text, 
    state, 
    state_date, 
    metric_type, 
    state_type,
    list_id,
    lr_list_id,
    search_system,
    session,
):
    if search_system == "Yandex":
        database = QueryLiveSearchYandex
    elif search_system == "Google":
        database = QueryLiveSearchGoogle
    else:
        print("Поисковая система не указана")
    
    if metric_type == "P":
        pointer = database.position

    if not state:
        sub = select(LiveSearchListQuery).where(LiveSearchListQuery.list_id == list_id).filter(LiveSearchListQuery.query.like(f"%{search_text.strip()}%")).offset(page).limit(per_page).subquery()

        all_queries = (await session.execute(select(LiveSearchListQuery.query).where(LiveSearchListQuery.list_id == list_id).filter(LiveSearchListQuery.query.like(f"%{search_text.strip()}%")).offset(page).limit(per_page))).scalars().all()
        
        query = (
            select(
                database.date,
                database.url,
                database.position,
                sub.c.query,
            ).where(database.lr_list_id == lr_list_id)
            .join(sub, database.query_id == sub.c.id)
            .group_by(
                database.date,
                database.url,
                database.position,
                sub.c.id,
                sub.c.query,
                sub.c.list_id,
            )
            .having(and_(
                database.date <= date_end,
                database.date >= date_start
            ))
        )
    
    elif state == "decrease":
        sub_get_id = (
            select(
                database.id,  # Выбираем только нужные столбцы
                database.query_id,
                database.url,
                database.position,
                database.date
            ).where(database.lr_list_id == lr_list_id)
            .join(LiveSearchListQuery, database.query_id == LiveSearchListQuery.id)
            .where(
                and_(
                    database.date == state_date,
                    LiveSearchListQuery.list_id == list_id
                )
            )
            .order_by(desc(pointer))
            .offset(page)
            .limit(per_page)
            .subquery()  # Создаем подзапрос
        )

        # Алиас для подзапроса LiveSearchListQuery
        sub = select(
            LiveSearchListQuery.id,
            LiveSearchListQuery.query,
            LiveSearchListQuery.list_id
        ).join(sub_get_id, LiveSearchListQuery.id == sub_get_id.c.query_id).filter(LiveSearchListQuery.query.like(f"%{search_text.strip()}%")).subquery()

        all_queries = (await session.execute(select(LiveSearchListQuery.query).where(LiveSearchListQuery.list_id == list_id).filter(LiveSearchListQuery.query.like(f"%{search_text.strip()}%")).offset(page).limit(per_page))).scalars().all()
        # Основной запрос, используя алиасы
        query = (
            select(
                database.date,
                database.url,
                database.position,
                sub.c.query,
            ).where(database.lr_list_id == lr_list_id)
            .join(sub, database.query_id == sub.c.id)
            .group_by(
                database.date,
                database.url,
                database.position,
                sub.c.id,
                sub.c.query,
                sub.c.list_id,
            )
            .having(and_(
                database.date <= date_end,
                database.date >= date_start
            ))
        )
    
    elif state == "increase":
        sub_get_id = (
            select(
                database.id,  # Выбираем только нужные столбцы
                database.query_id,
                database.url,
                database.position,
                database.date
            ).where(database.lr_list_id == lr_list_id)
            .join(LiveSearchListQuery, database.query_id == LiveSearchListQuery.id)
            .where(
                and_(
                    database.date == state_date,
                    LiveSearchListQuery.list_id == list_id
                )
            )
            .order_by(asc(pointer))
            .offset(page)
            .limit(per_page)
            .subquery()  # Создаем подзапрос
        )

        # Алиас для подзапроса LiveSearchListQuery
        sub = select(
            LiveSearchListQuery.id,
            LiveSearchListQuery.query,
            LiveSearchListQuery.list_id
        ).join(sub_get_id, LiveSearchListQuery.id == sub_get_id.c.query_id).filter(LiveSearchListQuery.query.like(f"%{search_text.strip()}%")).subquery()

        all_queries = (await session.execute(select(LiveSearchListQuery.query).where(LiveSearchListQuery.list_id == list_id).filter(LiveSearchListQuery.query.like(f"%{search_text.strip()}%")).offset(page).limit(per_page))).scalars().all()
        # Основной запрос, используя алиасы
        query = (
            select(
                database.date,
                database.url,
                database.position,
                sub.c.query,
            ).where(database.lr_list_id == lr_list_id)
            .join(sub, database.query_id == sub.c.id)
            .group_by(
                database.date,
                database.url,
                database.position,
                sub.c.id,
                sub.c.query,
                sub.c.list_id,
            )
            .having(and_(
                database.date <= date_end,
                database.date >= date_start
            ))
        )

    res = await session.execute(query)
    product_row = res.fetchall()
    
    if product_row:
        return product_row, all_queries


async def get_urls_with_pagination_sort(
    page, 
    per_page, 
    date_start, 
    date_end, 
    sort_desc, 
    list_id,
    lr_list_id,
    search_system,
    session,
):
    if search_system == "Yandex":
        database = QueryLiveSearchYandex
    elif search_system == "Google":
        database = QueryLiveSearchGoogle
    else:
        print("Поисковая система не указана")

    if sort_desc:
        sub = select(LiveSearchListQuery).order_by(desc(LiveSearchListQuery.query)).where(LiveSearchListQuery.list_id == list_id).offset(page).limit(per_page).subquery()
        all_queries = (await session.execute(select(LiveSearchListQuery.query).order_by(desc(LiveSearchListQuery.query)).where(LiveSearchListQuery.list_id == list_id).offset(page).limit(per_page))).scalars().all()
    else:
        sub = select(LiveSearchListQuery).order_by(asc(LiveSearchListQuery.query)).where(LiveSearchListQuery.list_id == list_id).offset(page).limit(per_page).subquery()
        all_queries = (await session.execute(select(LiveSearchListQuery).order_by(asc(LiveSearchListQuery.query)).where(LiveSearchListQuery.list_id == list_id).offset(page).limit(per_page))).scalars().all()

    
    query = (
        select(
            database.date,
            database.url,
            database.position,
            sub.c.query,
        ).where(database.lr_list_id == lr_list_id)
        .join(sub, database.query_id == sub.c.id)
        .group_by(
            database.date,
            database.url,
            database.position,
            sub.c.id,
            sub.c.query,
            sub.c.list_id,
        )
        .having(and_(
            database.date <= date_end,
            database.date >= date_start
        ))
    )

    res = await session.execute(query)
    product_row = res.fetchall()
    
    if product_row:
        return product_row, all_queries


async def get_urls_with_pagination_sort_and_like(
    page, 
    per_page, 
    date_start, 
    date_end,
    search_text, 
    sort_desc, 
    list_id,
    lr_list_id,
    search_system,
    session,
):
    if search_system == "Yandex":
        database = QueryLiveSearchYandex
    elif search_system == "Google":
        database = QueryLiveSearchGoogle
    else:
        print("Поисковая система не указана")

    if sort_desc:
        sub = select(LiveSearchListQuery).order_by(desc(LiveSearchListQuery.query)).filter(LiveSearchListQuery.query.like(f"%{search_text.strip()}%")).where(LiveSearchListQuery.list_id == list_id).offset(page).limit(per_page).subquery()
        all_queries = (await session.execute(select(LiveSearchListQuery).order_by(desc(LiveSearchListQuery.query)).filter(LiveSearchListQuery.query.like(f"%{search_text.strip()}%")).where(LiveSearchListQuery.list_id == list_id).offset(page).limit(per_page))).scalars().all()

    else:
        sub = select(LiveSearchListQuery).order_by((LiveSearchListQuery.query)).filter(LiveSearchListQuery.query.like(f"%{search_text.strip()}%")).where(LiveSearchListQuery.list_id == list_id).offset(page).limit(per_page).subquery()
        all_queries = (await session.execute(select(LiveSearchListQuery).order_by((LiveSearchListQuery.query)).filter(LiveSearchListQuery.query.like(f"%{search_text.strip()}%")).where(LiveSearchListQuery.list_id == list_id).offset(page).limit(per_page))).scalars().all()

    query = (
        select(
            database.date,
            database.url,
            database.position,
            sub.c.query,
        ).where(database.lr_list_id == lr_list_id)
        .join(sub, database.query_id == sub.c.id)
        .group_by(
            database.date,
            database.url,
            database.position,
            sub.c.id,
            sub.c.query,
            sub.c.list_id,
        )
        .having(and_(
            database.date <= date_end,
            database.date >= date_start
        ))
    )

    res = await session.execute(query)
    product_row = res.fetchall()
    
    if product_row:
        return product_row, all_queries