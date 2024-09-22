from datetime import datetime
from itertools import groupby
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, select
from api.auth.models import User
from api.config.models import ListLrSearchSystem, UserQueryCount, YandexLr
from api.config.utils import get_config_names, get_group_names
from api.live_search_api.db import get_urls_with_pagination, get_urls_with_pagination_and_like, get_urls_with_pagination_sort, get_urls_with_pagination_sort_and_like
from db.session import get_db_general

from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.auth_config import current_user

from const import date_format_2, date_format, query_value


templates = Jinja2Templates(directory="static")


router = APIRouter()

@router.get("/")
async def get_live_search(
    request: Request,
    list_id: int = Query(None),
    search_system: str = Query(None),
    lr_id: int = Query(None),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_db_general)
):  
    if lr_id == -1:
        lr_id = (await session.execute(select(ListLrSearchSystem.id).where(and_(ListLrSearchSystem.list_id == list_id, ListLrSearchSystem.search_system == search_system)))).scalars().first()
        if lr_id is None:
            lr_id = -1
    print(lr_id)

    group_name = request.session["group"].get("name", "")
    
    config_names = [elem[0] for elem in (await get_config_names(session, user, group_name))]

    group_names = await get_group_names(session, user)

    query_count = (await session.execute(select(UserQueryCount.query_count).where(UserQueryCount.user_id == user.id))).scalars().first()

    region_list = (await session.execute(select(ListLrSearchSystem).where(and_(ListLrSearchSystem.list_id == list_id, ListLrSearchSystem.search_system == search_system)))).scalars().all()

    regions = (await session.execute(select(YandexLr))).scalars().all()
    region_dict = {region.Geoid: region.Geo for region in regions}

    current_region = (await session.execute(select(ListLrSearchSystem.lr).where(ListLrSearchSystem.id == lr_id))).scalars().first()

    print(current_region)

    return templates.TemplateResponse("live_search-info.html",
                                      {"request": request,
                                       "user": user,
                                       "config_names": config_names,
                                       "group_names": group_names,
                                       "list_id": list_id,
                                       "query_count": query_count,
                                       "search_system": search_system,
                                       "lr_id": lr_id,
                                       "region_list": region_list,
                                       "region_dict": region_dict,
                                       "current_region": current_region,
                                        }
                                       )


@router.post("/")
async def get_live_search(
    request: Request,
    data_request: dict,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_db_general)
    ):
    print(data_request)
    start_date = datetime.strptime(data_request["start_date"], date_format_2)
    end_date = datetime.strptime(data_request["end_date"], date_format_2)
    list_id = int(data_request["list_id"])
    lr_list_id = int(data_request["lr_id"])
    search_system = data_request["search_system"]
    state_date = None
    if data_request["button_date"]:
        state_date = datetime.strptime(data_request["button_date"], date_format_2)

    if data_request["sort_result"]:
        if data_request["search_text"] == "":
            urls, all_queries = await get_urls_with_pagination_sort(
                data_request["start"], 
                data_request["length"], 
                start_date,
                end_date,
                data_request["sort_desc"],
                list_id,
                lr_list_id,
                session,
                )
        else:
            urls, all_queries = await get_urls_with_pagination_sort_and_like(
                data_request["start"], 
                data_request["length"],
                start_date, 
                end_date,
                data_request["search_text"],
                data_request["sort_desc"],
                list_id,
                lr_list_id,
                session
                )
    else:
        if data_request["search_text"] == "":
            urls, all_queries = await get_urls_with_pagination(
                data_request["start"], 
                data_request["length"], 
                start_date,
                end_date, 
                data_request["button_state"], 
                state_date,
                data_request["metric_type"],
                data_request["state_type"],
                list_id,
                lr_list_id,
                search_system,
                session,
                )
        else:
            urls, all_queries = await get_urls_with_pagination_and_like(
                data_request["start"], 
                data_request["length"],
                start_date, 
                end_date, 
                data_request["search_text"],
                data_request["button_state"], 
                state_date,
                data_request["metric_type"],
                data_request["state_type"],
                list_id,
                lr_list_id,
                search_system,
                session,
                )
    try:
        if urls:
            urls.sort(key=lambda x: x[-1])
        
        grouped_data = [(key, sorted(list(group), key=lambda x: x[0])) for key, group in
                        groupby(urls, key=lambda x: x[-1])]

        if data_request["button_state"]:
            if data_request["metric_type"] == "P":
                grouped_data.sort(
                    key=lambda x: next(
                        (
                            sub_item[2] if sub_item[2] != 0 else 
                            (-float('inf') if data_request["button_state"] == "decrease" else float('inf'))
                            for sub_item in x[1]
                            if sub_item[0] == state_date
                        ),
                        -float('inf') if data_request["button_state"] == "decrease" else float('inf')
                    ),
                    reverse=data_request["button_state"] == "decrease"
                )
    except TypeError as e:
        return JSONResponse({"data": []})

    if len(grouped_data) == 0:
        return JSONResponse({"data": []})
    
    data = []
    current_query = set()
    for el in grouped_data:
        res = {"query":
                   f"<div style='width:355px; height: 55px; overflow: auto; white-space: nowrap;'><span>{el[0]}</span></div>"}
        current_query.add(el[0])
        url, pos = "", float("inf")
        for k, stat in enumerate(el[1]):
            if stat[2] < pos:
                color = "#9DE8BD"
                color_text = "green"
            elif stat[2] > pos:
                color = "#FDC4BD"
                color_text = "red"
            else:
                color = "#B4D7ED"
                color_text = "blue"
            pos = stat[2]
            if stat[2] > 0:
                res[stat[0].strftime(
                    date_format_2)] = f"""<div style='height: 55px; width: 100px; margin: 0px; padding: 0px; background-color: {color}; text-align: center; display: flex; align-items: center; justify-content: center;'>
                                        <a href='{stat[1]}' style='font-size: 18px; text-decoration: none; color: inherit;'>
                                            {stat[2]}
                                        </a>
                                    </div>"""
            else:   
                res[stat[0].strftime(
                date_format_2)] = f"""<div style='height: 55px; width: 100px; margin: 0px; padding: 0px; background-color: #FFFF99; text-align: center; display: flex; align-items: center; justify-content: center;'>
                                        <span style='font-size: 18px'>-</span></div>"""
        data.append(res)
    
    for query in all_queries:
        if query not in current_query:
            data.append(
                {"query":
                   f"<div style='width:355px; height: 55px; overflow: auto; white-space: nowrap;'><span>{query}</span></div>"}
                   )

    json_data = jsonable_encoder(data)

    return JSONResponse({"data": json_data})


@router.get("/update_query_count")
async def update_query_count(
    request: Request,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_db_general)
):
    res = (await session.execute(select(UserQueryCount).where(UserQueryCount.user_id == user.id))).scalars().first()

    if res.last_update_date == datetime.strptime(datetime.now().strftime(date_format), date_format):
        raise HTTPException(status_code=400, detail="Сегодня запросы уже были обновлены")
    
    res.query_count = query_value
    res.last_update_date = datetime.strptime(datetime.now().strftime(date_format), date_format)

    await session.commit()

    return {
        "status": 200,
        "message": f"query for {user.username} reset"
    }
