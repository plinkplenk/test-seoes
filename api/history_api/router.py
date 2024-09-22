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

from api.actions.actions import get_last_load_date
from api.actions.indicators import _get_indicators_from_db, _get_top_query, _get_top_url
from api.actions.utils import get_day_of_week
from api.auth.models import User

from api.auth.auth_config import current_user

from sqlalchemy.ext.asyncio import AsyncSession

from api.config.utils import get_config_names, get_group_names
from db.session import connect_db, get_db_general

from const import date_format, date_format_2, date_format_out


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)

templates = Jinja2Templates(directory="static")


router = APIRouter()

@router.get("/")
async def get_history(
        request: Request,
        user: User = Depends(current_user),
        session: AsyncSession = Depends(get_db_general)
        ):
    group_name = request.session["group"].get("name", "")
    config_names = [elem[0] for elem in (await get_config_names(session, user, group_name))]

    group_names = await get_group_names(session, user)

    DATABASE_NAME = request.session['config'].get('database_name', "")

    if DATABASE_NAME:
        async_session = await connect_db(DATABASE_NAME)

    last_load_time = await get_last_load_date(async_session, "history")

    return templates.TemplateResponse("all-history.html",
                                      {"request": request,
                                       "user": user,
                                       "config_names": config_names,
                                       "group_names": group_names,
                                       "last_update_date": last_load_time,
                                       })


@router.post("/")
async def get_history(
        request: Request, data_request: dict,
        user: User = Depends(current_user)
):
    DATABASE_NAME = request.session['config'].get('database_name', "")
    group = request.session['group'].get('name', '')
    async_session = await connect_db(DATABASE_NAME)
    start_date = datetime.strptime(data_request["start_date"], date_format_2)
    end_date = datetime.strptime(data_request["end_date"], date_format_2)
    indicators = await _get_indicators_from_db(start_date,
                                               end_date, async_session)

    if indicators:
        indicators.sort(key=lambda x: x[0])
    try:
        grouped_data = [(key, sorted(list(group), key=lambda x: x[2])) for key, group in
                        groupby(indicators, key=lambda x: x[0])]
    except TypeError as e:
        return JSONResponse({"data": []})

    if len(grouped_data) == 0:
        return JSONResponse({"data": []})

    data = []
    for count, el in enumerate(grouped_data):
        res = {"query":
                   f"<div style='width:355px; height: 55px; overflow: auto; white-space: nowrap;'><span>{el[0]}</span></div>"}
        prev_value = -inf
        value_sum, count = 0, 0
        for name, value, date in el[1]:
            if value >= prev_value:
                color = "#9DE8BD"  # green
            else:
                color = "#FDC4BD"  # red
            if value > 0:
                value_sum += value
                count += 1
                if el[0] != "TOTAL_CTR":
                    res[date.strftime(
                        date_format_2)] = f"""<div style='height: 55px; width: 100px; margin: 0px; padding: 0px; background-color: {color}; text-align: center; display: flex; align-items: center; justify-content: center;'>
                                            <span style='font-size: 18px'>{value}</span>
                                            </div>"""
                else:
                    res[date.strftime(
                        date_format_2)] = f"""<div style='height: 55px; width: 100px; margin: 0px; padding: 0px; background-color: {color}; text-align: center; display: flex; align-items: center; justify-content: center;'>
                                            <span style='font-size: 18px'>{value}%</span>
                                            </div>"""
                prev_value = value

        if el[0] in ("AVG_CLICK_POSITION", "TOTAL_CTR", "AVG_SHOW_POSITION"):
            if count > 0:
                value_sum = round(value_sum / count, 2)

        if el[0] != "TOTAL_CTR":
            res["result"] = f"""<div style='height: 55px; width: 100px; margin: 0px; padding: 0px; background-color: #9DE8BD; text-align: center; display: flex; align-items: center; justify-content: center;'>
                                    <span style='font-size: 18px'>{value_sum}</span>
                                    </div>"""
        else:
            res["result"] = f"""<div style='height: 55px; width: 100px; margin: 0px; padding: 0px; background-color: #9DE8BD; text-align: center; display: flex; align-items: center; justify-content: center;'>
                                    <span style='font-size: 18px'>{value_sum}%</span>
                                    </div>"""
        data.append(res)
    data[-1], data[-2] = data[-2], data[-1]

    TOP = 3, 5, 10, 20, 30
    query_front = []
    for top in TOP:
        grouped_data_sum = {
            "query":
                f"<div style='width:355px; height: 55px; overflow: auto; white-space: nowrap;'><span>TOP {top}</span></div>"
        }
        query_top = await _get_top_query(start_date, end_date, top, async_session)
        query_top.sort(key=lambda x: x[-1])
        total_position, total_clicks, total_impression, total_count, count_for_avg = 0, 0, 0, 0, 0
        for position, clicks, impression, count, date in query_top:
            grouped_data_sum[date.strftime(
                date_format_2)] = f"""<div style='height: 55px; width: 100px; margin: 0px; padding: 0px; background-color: #9DE8BD'>
              <span style='font-size: 18px'>{position}</span><br>
              <span style='font-size: 10px'>Клики</span><span style='font-size: 10px; margin-left: 10px'>Count: {count}</span><br>
              <span style='font-size: 10px'>{clicks}</span> <span style='font-size: 10px; margin-left: 10px'>R: {int(impression)}</span>
              </div>"""
            total_position += position
            total_clicks += clicks
            total_impression += impression
            total_count += count
            if position > 0:
                count_for_avg += 1

        if count_for_avg > 0:
            total_position = round(total_position / count_for_avg, 2)

        grouped_data_sum["result"] = f"""<div style='height: 55px; width: 100px; margin: 0px; padding: 0px; background-color: #9DE8BD'>
              <span style='font-size: 18px'>{total_position}</span><br>
              <span style='font-size: 10px'>Клики</span><span style='font-size: 10px; margin-left: 5px'>Count: {total_count}</span><br>
              <span style='font-size: 10px'>{total_clicks}</span> <span style='font-size: 10px; margin-left: 5px'>R: {int(total_impression)}</span>
              </div>"""

        query_front.append(grouped_data_sum)

    url_front = []
    for top in TOP:
        grouped_data_sum = {
            "query":
                f"<div style='width:355px; height: 55px; overflow: auto; white-space: nowrap;'><span>TOP {top}</span></div>"
        }
        query_top = await _get_top_url(start_date, end_date, top, async_session)
        query_top.sort(key=lambda x: x[-1])
        total_position, total_clicks, total_impression, total_count, count_for_avg = 0, 0, 0, 0, 0
        for position, clicks, impression, count, date in query_top:
            grouped_data_sum[date.strftime(
                date_format_2)] = f"""<div style='height: 55px; width: 100px; margin: 0px; padding: 0px; background-color: #9DE8BD'>
              <span style='font-size: 18px'>{position}</span><br>
              <span style='font-size: 10px'>Клики</span><span style='font-size: 10px; margin-left: 10px'>Count: {count}</span><br>
              <span style='font-size: 10px'>{clicks}</span> <span style='font-size: 10px; margin-left: 10px'>R: {int(impression)}</span>
              </div>"""
            total_position += position
            total_clicks += clicks
            total_impression += impression
            total_count += count
            if position > 0:
                count_for_avg += 1

        if count_for_avg > 0:
            total_position = round(total_position / count_for_avg, 2)

        grouped_data_sum["result"] = f"""<div style='height: 55px; width: 100px; margin: 0px; padding: 0px; background-color: #9DE8BD'>
              <span style='font-size: 18px'>{total_position}</span><br>
              <span style='font-size: 10px'>Клики</span><span style='font-size: 10px; margin-left: 10px'>Count: {total_count}</span><br>
              <span style='font-size: 10px'>{total_clicks}</span> <span style='font-size: 10px; margin-left: 7px'>R: {int(total_impression)}</span>
              </div>"""

        url_front.append(grouped_data_sum)

    json_data = jsonable_encoder(data)
    json_query_top = jsonable_encoder(query_front)
    json_url_top = jsonable_encoder(url_front)
    return JSONResponse({"data": json_data,
                         "query_top": json_query_top,
                         "url_top": json_url_top}
                        )


@router.post("/generate_excel_history")
async def generate_excel_history(request: Request, data_request: dict, user: User = Depends(current_user)):
    DATABASE_NAME = request.session['config'].get('database_name', "")
    group = request.session['group'].get('name', '')
    async_session = await connect_db(DATABASE_NAME)
    wb = Workbook()
    ws = wb.active
    start_date = datetime.strptime(data_request["start_date"], date_format_2)
    end_date = datetime.strptime(data_request["end_date"], date_format_2)
    main_header = []
    main_header_day_name = []
    for i in range(int(data_request["amount"])):
        date = (start_date + timedelta(days=i)).strftime(date_format_out)
        main_header_day_name.append(get_day_of_week(date))
        main_header.append(date)
    main_header = main_header[::-1]
    main_header.insert(0, "Indicators")
    main_header.insert(1, "result")
    main_header_day_name = main_header_day_name[::-1]
    main_header_day_name.insert(0, "День недели")
    main_header_day_name.insert(1, "result")
    ws.append(main_header)
    ws.append(main_header_day_name)
    main_header = []
    for i in range(int(data_request["amount"])):
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
    main_header = main_header[::-1]
    indicators = await _get_indicators_from_db(start_date, end_date, async_session)
    grouped_data = []
    if indicators:
        indicators.sort(key=lambda x: x[0])
    try:
        grouped_data = [(key, sorted(list(group), key=lambda x: x[2])) for key, group in
                        groupby(indicators, key=lambda x: x[0])]
    except TypeError as e:
        print("error")
    if len(grouped_data) == 0:
        print("empty data")
    for el in grouped_data:
        info = {}
        res = []
        value_sum, count = 0, 0
        for name, value, date in el[1]:
            if name != "TOTAL_CTR":
                info[date.strftime(date_format_out)] = [value]
            else:
                info[date.strftime(date_format_out)] = [f"{value}%"]
            value_sum += value
            count += 1

        if el[0] in ("AVG_CLICK_POSITION", "TOTAL_CTR", "AVG_SHOW_POSITION"):
            if count > 0:
                value_sum = round(value_sum / count, 2)
        res.append(el[0])
        if el[0] != "TOTAL_CTR":
            res.append(value_sum)
        else:
            res.append(f"{value_sum}%")
        for el in main_header:
            if el in info:
                res.extend(info[el])
            else:
                res.extend([0])
        ws.append(res)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(io.BytesIO(output.getvalue()),
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment;filename='data.xlsx'"})


@router.post("/generate_excel_top")
async def generate_excel_top(request: Request, data_request: dict, user: User = Depends(current_user)):
    DATABASE_NAME = request.session['config'].get('database_name', "")
    group = request.session['group'].get('name', '')
    async_session = await connect_db(DATABASE_NAME)
    wb = Workbook()
    ws = wb.active
    start_date = datetime.strptime(data_request["start_date"], date_format_2)
    end_date = datetime.strptime(data_request["end_date"], date_format_2)
    main_header = []
    for i in range(int(data_request["amount"])):
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
    main_header = main_header[::-1]
    main_header.insert(0, "TOP")
    for i in range(4):
        main_header.insert(1, "result")
    ws.append(main_header)
    header = ["Position", "Click", "Impression", "Count"] * (int(data_request["amount"]) + 1)
    header.insert(0, "")
    ws.append(header)
    ws.append(["query"])
    start = 0
    main_header = []
    for i in range(int(data_request["amount"])):
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
    main_header.append("result")
    main_header = main_header[::-1]

    TOP = 3, 5, 10, 20, 30
    for top in TOP:
        res = [f"TOP {top}"]
        info = {}
        query_top = await _get_top_query(start_date, end_date, top, async_session)
        query_top.sort(key=lambda x: x[-1])
        total_position, total_clicks, total_impression, total_count, count_for_avg = 0, 0, 0, 0, 0
        for position, clicks, impression, count, date in query_top:
            info[date.strftime(date_format_out)] = [position, clicks, impression, count]
            total_position += position
            total_clicks += clicks
            total_impression += impression
            total_count += count
            if position > 0:
                count_for_avg += 1

        if count_for_avg > 0:
            total_position = round(total_position / count_for_avg, 2)
        info["result"] = [total_position, total_clicks, total_impression, total_count]
        for el in main_header:
            if el in info:
                res.extend(info[el])
            else:
                res.extend([0, 0, 0, 0])
        ws.append(res)

    ws.append(["url"])

    TOP = 3, 5, 10, 20, 30
    for top in TOP:
        res = [f"TOP {top}"]
        info = {}
        url_top = await _get_top_url(start_date, end_date, top, async_session)
        url_top.sort(key=lambda x: x[-1])
        total_position, total_clicks, total_impression, total_count, count_for_avg = 0, 0, 0, 0, 0
        for position, clicks, impression, count, date in url_top:
            info[date.strftime(date_format_out)] = [position, clicks, impression, count]
            total_position += position
            total_clicks += clicks
            total_impression += impression
            total_count += count
            if position > 0:
                count_for_avg += 1

        if count_for_avg > 0:
            total_position = round(total_position / count_for_avg, 2)
        info["result"] = [total_position, total_clicks, total_impression, total_count]
        for el in main_header:
            if el in info:
                res.extend(info[el])
            else:
                res.extend([0, 0, 0, 0])
        ws.append(res)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(io.BytesIO(output.getvalue()),
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment;filename='data.xlsx'"})


@router.post("/generate_csv_history/")
async def generate_csv_history(request: Request, data_request: dict, user: User = Depends(current_user)):
    DATABASE_NAME = request.session['config'].get('database_name', "")
    group = request.session['group'].get('name', '')
    async_session = await connect_db(DATABASE_NAME)
    ws = []
    start_date = datetime.strptime(data_request["start_date"], date_format_2)
    end_date = datetime.strptime(data_request["end_date"], date_format_2)
    main_header = []
    main_header_day_name = []
    for i in range(int(data_request["amount"])):
        date = (start_date + timedelta(days=i)).strftime(date_format_out)
        main_header_day_name.append(get_day_of_week(date))
        main_header.append(date)
    main_header = main_header[::-1]
    main_header.insert(0, "Indicators")
    main_header_day_name = main_header_day_name[::-1]
    main_header_day_name.insert(0, "День недели")
    ws.append(main_header)
    ws.append(main_header_day_name)
    main_header = []
    for i in range(int(data_request["amount"])):
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
    main_header = main_header[::-1]
    indicators = await _get_indicators_from_db(start_date, end_date, async_session)
    grouped_data = []
    if indicators:
        indicators.sort(key=lambda x: x[0])
    try:
        grouped_data = [(key, sorted(list(group), key=lambda x: x[2])) for key, group in
                        groupby(indicators, key=lambda x: x[0])]
    except TypeError as e:
        print("error")
    if len(grouped_data) == 0:
        print("empty data")
    for el in grouped_data:
        info = {}
        res = []
        value_sum, count = 0, 0
        for name, value, date in el[1]:
            if name != "TOTAL_CTR":
                info[date.strftime(date_format_out)] = [value]
            else:
                info[date.strftime(date_format_out)] = [f"{value}%"]
            value_sum += value
            count += 1

        if el[0] in ("AVG_CLICK_POSITION", "TOTAL_CTR", "AVG_SHOW_POSITION"):
            if count > 0:
                value_sum = round(value_sum / count, 2)
        if el[0] != "TOTAL_CTR":
            res.append(value_sum)
        else:
            res.append(f"{value_sum}%")
        res.append(value_sum)
        for el in main_header:
            if el in info:
                res.extend(info[el])
            else:
                res.extend([0])
        ws.append(res)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(ws)
    output.seek(0)

    return StreamingResponse(content=output.getvalue(),
                             headers={"Content-Disposition": "attachment;filename='data.csv'"})


@router.post("/generate_csv_top")
async def generate_csv_top(request: Request, data_request: dict, user: User = Depends(current_user)):
    DATABASE_NAME = request.session['config'].get('database_name', "")
    group = request.session['group'].get('name', '')
    async_session = await connect_db(DATABASE_NAME)
    ws = []
    start_date = datetime.strptime(data_request["start_date"], date_format_2)
    end_date = datetime.strptime(data_request["end_date"], date_format_2)
    main_header = []
    for i in range(int(data_request["amount"])):
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
    main_header = main_header[::-1]
    main_header.insert(0, "TOP")
    for i in range(4):
        main_header.insert(1, "result")
    ws.append(main_header)
    header = ["Position", "Click", "Impression", "clicks"] * (int(data_request["amount"]) + 1)
    header.insert(0, "")
    ws.append(header)
    ws.append(["query"])
    start = 0
    main_header = []
    for i in range(int(data_request["amount"])):
        main_header.append((start_date + timedelta(days=i)).strftime(date_format_out))
    main_header.append("result")
    main_header = main_header[::-1]

    TOP = 3, 5, 10, 20, 30
    for top in TOP:
        res = [f"TOP {top}"]
        info = {}
        query_top = await _get_top_query(start_date, end_date, top, async_session)
        query_top.sort(key=lambda x: x[-1])
        total_position, total_clicks, total_impression, total_count, count_for_avg = 0, 0, 0, 0, 0
        for position, clicks, impression, count, date in query_top:
            info[date.strftime(date_format_out)] = [position, clicks, impression, count]
            total_position += position
            total_clicks += clicks
            total_impression += impression
            total_count += count
            if position > 0:
                count_for_avg += 1

        if count_for_avg > 0:
            total_position = round(total_position / count_for_avg, 2)
        info["result"] = [total_position, total_clicks, total_impression, total_count]
        for el in main_header:
            if el in info:
                res.extend(info[el])
            else:
                res.extend([0, 0, 0, 0])
        ws.append(res)

    ws.append(["url"])

    TOP = 3, 5, 10, 20, 30
    for top in TOP:
        res = [f"TOP {top}"]
        info = {}
        url_top = await _get_top_url(start_date, end_date, top, async_session)
        url_top.sort(key=lambda x: x[-1])
        total_position, total_clicks, total_impression, total_count, count_for_avg = 0, 0, 0, 0, 0
        for position, clicks, impression, count, date in url_top:
            info[date.strftime(date_format_out)] = [position, clicks, impression, count]
            total_position += position
            total_clicks += clicks
            total_impression += impression
            total_count += count
            if position > 0:
                count_for_avg += 1

        if count_for_avg > 0:
            total_position = round(total_position / count_for_avg, 2)
        info["result"] = [total_position, total_clicks, total_impression, total_count]
        for el in main_header:
            if el in info:
                res.extend(info[el])
            else:
                res.extend([0, 0, 0, 0])
        ws.append(res)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(ws)
    output.seek(0)

    return StreamingResponse(content=output.getvalue(),
                             headers={"Content-Disposition": "attachment;filename='data.csv'"})