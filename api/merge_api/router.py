from cmath import inf
import csv
from datetime import datetime, timedelta
import io
from itertools import groupby
import logging
import sys

from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from openpyxl import Workbook

from api.actions.query_url_merge import _get_merge_query, _get_merge_with_pagination, _get_merge_with_pagination_and_like, _get_merge_with_pagination_and_like_sort, _get_merge_with_pagination_sort
from api.auth.models import User

from api.auth.auth_config import current_user
from api.config.utils import get_config_names, get_group_names
from db.models import QueryUrlsMergeLogs
from db.session import connect_db, get_db_general

from const import date_format_out, date_format_2

from sqlalchemy.ext.asyncio import AsyncSession

from db.utils import get_all_dates


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)

templates = Jinja2Templates(directory="static")


router = APIRouter()

@router.get("/menu/merge_database/")
async def show_menu_merge_page(request: Request,
                               user: User = Depends(current_user),
                               session: AsyncSession = Depends(get_db_general)):
    DATABASE_NAME = request.session['config'].get('database_name', "")
    group = request.session['group'].get('name', '')
    async_session = await connect_db(DATABASE_NAME)
    all_dates = await get_all_dates(async_session, QueryUrlsMergeLogs)
    group_name = request.session["group"].get("name", "")
    config_names = [elem[0] for elem in (await get_config_names(session, user, group_name))]

    group_names = await get_group_names(session, user)

    return templates.TemplateResponse("merge_database.html",
                                      {"request": request,
                                       "user": user,
                                       "config_names": config_names,
                                       "group_names": group_names,
                                       "all_dates": all_dates})


@router.get("/")
async def get_merge(request: Request,
                         user: User = Depends(current_user),
                         session: AsyncSession = Depends(get_db_general)
                         ):
    date = request.query_params.get("date")
    group_name = request.session["group"].get("name", "")
    config_names = [elem[0] for elem in (await get_config_names(session, user, group_name))]

    DATABASE_NAME = request.session['config'].get('database_name', "")
    async_session = await connect_db(DATABASE_NAME)
    all_dates = await get_all_dates(async_session, QueryUrlsMergeLogs)

    last_update_date = None
    
    if all_dates:
        last_update_date = all_dates[0][0].strftime(date_format_2)

    group_names = await get_group_names(session, user)

    return templates.TemplateResponse("query-url-merge.html",
                                      {"request": request,
                                       "user": user,
                                       "config_names": config_names,
                                       "group_names": group_names,
                                       "date": date,
                                       "last_update_date": last_update_date,
                                       })


@router.post("/")
async def get_merge(
    request: Request, 
    data_request: dict, 
    user: User = Depends(current_user)
    ):
    DATABASE_NAME = request.session['config'].get('database_name', "")
    group = request.session['group'].get('name', '')
    async_session = await connect_db(DATABASE_NAME)
    start_date = datetime.strptime(data_request["start_date"], date_format_2)
    end_date = datetime.strptime(data_request["end_date"], date_format_2)
    if data_request["sort_result"]:
        if data_request["search_text_url"] == "" and data_request["search_text_query"] == "":
            urls = await _get_merge_with_pagination_sort(data_request["date"], data_request["sort_desc"],
                                                         data_request["start"], data_request["length"],
                                                         async_session)
        else:
            urls = await _get_merge_with_pagination_and_like_sort(data_request["date"], data_request["search_text_url"],
                                                                  data_request["search_text_query"],
                                                                  data_request["sort_desc"],
                                                                  data_request["start"], data_request["length"],
                                                                  async_session)
    else:
        if data_request["search_text_url"] == "" and data_request["search_text_query"] == "":
            urls = await _get_merge_with_pagination(data_request["date"], data_request["start"], data_request["length"],
                                                    async_session)
        else:
            urls = await _get_merge_with_pagination_and_like(data_request["date"], data_request["search_text_url"],
                                                             data_request["search_text_query"],
                                                             data_request["start"], data_request["length"],
                                                             async_session)
    if not urls or len(urls) == 0:
        return JSONResponse({"data": []})
    data = []
    all_queries = list()

    for el in urls:
        all_queries.extend(el[1])
    queries = await _get_merge_query(start_date, end_date, all_queries, async_session)
    if queries:
        queries.sort(key=lambda x: x[-1])
    grouped_data = dict([(key, sorted(list(group), key=lambda x: x[0])) for key, group in
                         groupby(queries, key=lambda x: x[-1])])
    for el in urls:
        parent_clicks, parent_position, parent_impression, parent_ctr, parent_count = 0, 0, 0, 0, 0
        url, queries = el[0], el[1]
        res = {"url":
                   f"<div style='width:355px; height: 55px; overflow: auto; white-space: nowrap;'><span>{el[0]}</span></div>",
               "queries": "", "count": 0}
        for query in queries:
            query = grouped_data.get(query, None)
            if query:
                res["count"] += 1
                res[
                    "queries"] += f"<div style='width:355px; height: 55px; overflow: auto; text-align: center; white-space: nowrap;'><span>{query[0][5]}</span></div>"

                data_dict = {}
                for el in query:
                    date = el[0]  # Преобразуем дату в строку
                    values = el  # Остальные значения кортежа
                    data_dict[date] = values

                total_clicks, position, impressions, ctr, count = 0, 0, 0, 0, 0
                current_date = start_date
                prev_stat = (-inf, -inf, -inf, -inf)
                while current_date <= end_date:
                    stat = data_dict.get(current_date, (-444, 0, 0, 0, 0, 0))
                    up = round(stat[1] - prev_stat[1], 2)
                    color = "#9DE8BD"
                    color_text = "green"
                    if up > 0:
                        color = "#FDC4BD"
                        color_text = "red"
                    if stat[1] <= 3:
                        color = "#B4D7ED"
                        color_text = "blue"
                    res[current_date.strftime(date_format_2)] = ''.join(
                        res.get(current_date.strftime(date_format_2), []))
                    if stat[0] != -444:
                        res[current_date.strftime(
                            date_format_2)] += f"""<div style='height: 55px; width: 100px; margin: 0px; padding: 0px; background-color: {color}'>
                                      <span style='font-size: 18px'>{stat[1]}</span><span style="margin-left: 5px; font-size: 10px; color: {color_text}">{abs(up)}</span><br>
                                      <span style='font-size: 10px'>Клики</span><span style='font-size: 10px; margin-left: 20px'>CTR {stat[4]}%</span><br>
                                      <span style='font-size: 10px'>{stat[2]}</span> <span style='font-size: 10px; margin-left: 20px'>R {stat[3]}%</span>
                                      </div>"""
                    else:
                        res[current_date.strftime(
                            date_format_2)] += f"""<div style='height: 55px; width: 100px; margin: 0px; padding: 0px; background-color: #B9BDBC'>
                                        <span style='font-size: 18px'><span style='color:red'>NAN</span></span><br>
                                        <span style='font-size: 10px'>Клики</span><span style='font-size: 10px; margin-left: 10px'>CTR <span style='color:red'>NAN%</span></span><br>
                                        <span style='font-size: 10px'><span style='color:red'>NAN</span></span> <span style='font-size: 10px; margin-left: 30px'>R <span style='color:red'>NAN%</span></span>
                                        </div>"""
                    total_clicks += stat[2]
                    position += stat[1]
                    impressions += stat[3]
                    ctr += stat[4]
                    if stat[1] > 0:
                        count += 1
                    prev_stat = (0, stat[1], stat[2], stat[3], stat[4])
                    if current_date == end_date:
                        res["result"] = res.get("result", "")
                        if impressions > 0:
                            total_position = round(position / count, 2)
                            total_ctr = round(ctr / count, 2)
                            res["result"] += f"""<div style='height: 55px; width: 100px; margin: 0px; padding: 0px; background-color: #9DE8BD'>
                                      <span style='font-size: 15px'>Позиция:{total_position}</span>
                                      <span style='font-size: 15px'>Клики:{total_clicks}</span>
                                      <span style='font-size: 9px'>Показы:{impressions}</span>
                                      <span style='font-size: 7px'>ctr:{round(total_clicks * 100 / impressions, 2)}%</span>
                                      </div>"""
                        else:
                            total_position = 0
                            total_ctr = 0
                            res["result"] += f"""<div style='height: 55px; width: 100px; margin: 0px; padding: 0px; background-color: #9DE8BD'>
                                      <span style='font-size: 15px'>Позиция:{0}</span>
                                      <span style='font-size: 15px'>Клики:{total_clicks}</span>
                                      <span style='font-size: 9px'>Показы:{impressions}</span>
                                      <span style='font-size: 9px'>ctr:{0}%</span>
                                      </div>"""
                        parent_clicks += total_clicks
                        parent_position += total_position
                        parent_impression += impressions
                        parent_ctr += total_ctr
                        if total_position > 0:
                            parent_count += 1
                    current_date += timedelta(days=1)

        if parent_clicks > 0:
            parent_position = round(parent_position / parent_count, 2)
            parent_ctr = round(parent_ctr / parent_count, 2)
            res["parent_result"] = f"""<div style='height: 55px; width: 100px; margin: 0px; padding: 0px; background-color: #9DE8BD'>
                                          <span style='font-size: 15px'>Позиция:{parent_position}</span>
                                          <span style='font-size: 15px'>Клики:{parent_clicks}</span>
                                          <span style='font-size: 9px'>Показы:{parent_impression}</span>
                                          <span style='font-size: 7px'>ctr:{round(parent_clicks * 100 / parent_impression, 2)}%</span>
                                          </div>"""

        data.append(res)
    json_data = jsonable_encoder(data)
    #
    # # return JSONResponse({"data": json_data, "recordsTotal": limit, "recordsFiltered": 50000})
    return JSONResponse({"data": json_data})


@router.post("/generate_excel_merge/")
async def generate_excel_merge(request: Request, data_request: dict, user: User = Depends(current_user)):
    DATABASE_NAME = request.session['config'].get('database_name', "")
    group = request.session['group'].get('name', '')
    async_session = await connect_db(DATABASE_NAME)
    wb = Workbook()
    ws = wb.active
    start_date = datetime.strptime(data_request["start_date"], date_format_2)
    end_date = datetime.strptime(data_request["end_date"], date_format_2)
    main_header = []
    for i in range(int(data_request["amount"]) + 1):
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
    main_header = main_header[::-1]
    main_header.insert(0, "Url")
    main_header.insert(1, "Queries")
    for i in range(4):
        main_header.insert(2, "Result")
    for i in range(4):
        main_header.insert(1, "Parent Result")
    ws.append(main_header)
    header = ["Position", "Click", "R", "CTR"] * (int(data_request["amount"]) + 3)
    header.insert(0, "")
    header.insert(5, "")
    ws.append(header)
    start = 0
    main_header = []
    for i in range(int(data_request["amount"]) + 1):
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
    main_header.append("Result")
    main_header = main_header[::-1]
    while True:
        start_el = (start * 50)
        if data_request["sort_result"]:
            if data_request["search_text_url"] == "" and data_request["search_text_query"] == "":
                urls = await _get_merge_with_pagination_sort(data_request["date"], data_request["sort_desc"],
                                                             start_el, data_request["length"],
                                                             async_session)
            else:
                urls = await _get_merge_with_pagination_and_like_sort(data_request["date"],
                                                                      data_request["search_text_url"],
                                                                      data_request["search_text_query"],
                                                                      data_request["sort_desc"],
                                                                      start_el, data_request["length"],
                                                                      async_session)
        else:
            if data_request["search_text_url"] == "" and data_request["search_text_query"] == "":
                urls = await _get_merge_with_pagination(data_request["date"], start_el,
                                                        data_request["length"],
                                                        async_session)
            else:
                urls = await _get_merge_with_pagination_and_like(data_request["date"], data_request["search_text_url"],
                                                                 data_request["search_text_query"],
                                                                 start_el, data_request["length"],
                                                                 async_session)
        start += 1
        if not urls or len(urls) == 0:
            break
        all_queries = list()
        for el in urls:
            all_queries.extend(el[1])
        queries = await _get_merge_query(start_date, end_date, all_queries, async_session)
        if queries:
            queries.sort(key=lambda x: x[-1])
        grouped_data = dict([(key, sorted(list(group), key=lambda x: x[0])) for key, group in
                             groupby(queries, key=lambda x: x[-1])])
        for url, queries in urls:
            parent_res = []
            parent_clicks, parent_position, parent_impression, parent_ctr, parent_count = 0, 0, 0, 0, 0
            for query in queries:
                res = []
                res.append(url)
                res.append(query)
                el = grouped_data.get(query, None)
                info = {}
                if el:
                    total_clicks, position, impressions, ctr, count = 0, 0, 0, 0, 0
                    for k, stat in enumerate(el):
                        info[stat[0].strftime(date_format_out)] = [stat[1], stat[2], stat[3], stat[4]]
                        total_clicks += stat[2]
                        position += stat[1]
                        impressions += stat[3]
                        ctr += stat[4]
                        if stat[1] > 0:
                            count += 1
                    if impressions > 0:
                        total_position = round(position / count, 2)
                        total_ctr = round(ctr / count, 2)
                        info["Result"] = [total_position, total_clicks, impressions, round(total_clicks * 100 / impressions, 2)]
                    else:
                        total_position = 0
                        total_ctr = 0
                        info["Result"] = [total_position, total_clicks, impressions, 0]
                    parent_impression += impressions
                    parent_position += total_position
                    parent_clicks += total_clicks
                    parent_ctr += total_ctr
                    for el in main_header:
                        if el in info:
                            res.extend(info[el])
                        else:
                            res.extend([0, 0, 0, 0])
                parent_res.append(res)

            for parent in parent_res:
                parent_true = [parent_position, parent_clicks, parent_impression, parent_ctr]
                parent_true.extend(parent)
                parent_true[0], parent_true[4] = parent_true[4], parent_true[0]
                ws.append(parent_true)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(io.BytesIO(output.getvalue()),
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment;filename='data.xlsx'"})


@router.post("/generate_csv_merge/")
async def generate_csv_merge(request: Request, data_request: dict, user: User = Depends(current_user)):
    DATABASE_NAME = request.session['config'].get('database_name', "")
    group = request.session['group'].get('name', '')
    async_session = await connect_db(DATABASE_NAME)
    ws = []
    start_date = datetime.strptime(data_request["start_date"], date_format_2)
    end_date = datetime.strptime(data_request["end_date"], date_format_2)
    main_header = []
    for i in range(int(data_request["amount"]) + 1):
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
    main_header = main_header[::-1]
    main_header.insert(0, "Url")
    main_header.insert(1, "Queries")
    for i in range(4):
        main_header.insert(2, "Result")
    for i in range(4):
        main_header.insert(1, "Parent Result")
    ws.append(main_header)
    header = ["Position", "Click", "R", "CTR"] * (int(data_request["amount"]) + 3)
    header.insert(0, "")
    header.insert(5, "")
    ws.append(header)
    start = 0
    main_header = []
    for i in range(int(data_request["amount"]) + 1):
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
    main_header.append("Result")
    main_header = main_header[::-1]
    while True:
        start_el = (start * 50)
        if data_request["sort_result"]:
            if data_request["search_text_url"] == "" and data_request["search_text_query"] == "":
                urls = await _get_merge_with_pagination_sort(data_request["date"], data_request["sort_desc"],
                                                             start_el, data_request["length"],
                                                             async_session)
            else:
                urls = await _get_merge_with_pagination_and_like_sort(data_request["date"],
                                                                      data_request["search_text_url"],
                                                                      data_request["search_text_query"],
                                                                      data_request["sort_desc"],
                                                                      start_el, data_request["length"],
                                                                      async_session)
        else:
            if data_request["search_text_url"] == "" and data_request["search_text_query"] == "":
                urls = await _get_merge_with_pagination(data_request["date"], start_el,
                                                        data_request["length"],
                                                        async_session)
            else:
                urls = await _get_merge_with_pagination_and_like(data_request["date"], data_request["search_text_url"],
                                                                 data_request["search_text_query"],
                                                                 start_el, data_request["length"],
                                                                 async_session)
        start += 1
        if not urls or len(urls) == 0:
            break
        all_queries = list()
        for el in urls:
            all_queries.extend(el[1])
        queries = await _get_merge_query(start_date, end_date, all_queries, async_session)
        if queries:
            queries.sort(key=lambda x: x[-1])
        grouped_data = dict([(key, sorted(list(group), key=lambda x: x[0])) for key, group in
                             groupby(queries, key=lambda x: x[-1])])
        for url, queries in urls:
            parent_res = []
            parent_clicks, parent_position, parent_impression, parent_ctr, parent_count = 0, 0, 0, 0, 0
            for query in queries:
                res = []
                res.append(url)
                res.append(query)
                el = grouped_data.get(query, None)
                info = {}
                if el:
                    total_clicks, position, impressions, ctr, count = 0, 0, 0, 0, 0
                    for k, stat in enumerate(el):
                        info[stat[0].strftime(date_format_out)] = [stat[1], stat[2], stat[3], stat[4]]
                        total_clicks += stat[2]
                        position += stat[1]
                        impressions += stat[3]
                        ctr += stat[4]
                        if stat[1] > 0:
                            count += 1
                    if impressions > 0:
                        total_position = round(position / count, 2)
                        total_ctr = round(ctr / count, 2)
                        info["Result"] = [total_position, total_clicks, impressions, round(total_clicks * 100 / impressions, 2)]
                    else:
                        total_position = 0
                        total_ctr = 0
                        info["Result"] = [total_position, total_clicks, impressions, 0]
                    parent_impression += impressions
                    parent_position += total_position
                    parent_clicks += total_clicks
                    parent_ctr += total_ctr
                    for el in main_header:
                        if el in info:
                            res.extend(info[el])
                        else:
                            res.extend([0, 0, 0, 0])
                parent_res.append(res)

            for parent in parent_res:
                parent_true = [parent_position, parent_clicks, parent_impression, parent_ctr]
                parent_true.extend(parent)
                parent_true[0], parent_true[4] = parent_true[4], parent_true[0]
                ws.append(parent_true)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(ws)
    output.seek(0)

    return StreamingResponse(content=output.getvalue(),
                             headers={"Content-Disposition": "attachment;filename='data.csv'"})