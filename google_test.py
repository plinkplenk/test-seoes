import aiohttp
import aiofiles
import asyncio
import xml.etree.ElementTree as ET
import urllib.parse
from datetime import datetime
import sys

from config import xml_config

completed_task = 0


async def urlencode_string(string):
    return urllib.parse.quote(string)


async def process_query(query, MAIN_DOMAIN, lr, query_info):
    global completed_task
    encoded_query = await urlencode_string(query)
    API_URL = f"https://xmlstock.com/google/json/"
    request_url = f"""{API_URL}?
                    user={xml_config.USER_ID}&
                    key={xml_config.API_KEY}&
                    query={encoded_query}&
                    groupby={xml_config.GROUP_BY}&
                    domain={xml_config.DOMAIN}&
                    lr={lr}&
                    device={xml_config.DEVICE}"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(request_url) as response:
                response_text = await response.json()
                response_text_json = response_text["results"]
                for key, value in response_text_json.items():
                    if value["site_name"].lower() == MAIN_DOMAIN:
                        print(key, value["url"])
                        query_info[query] = [value["url"], key]
    except Exception as e:
        print(f"Error processing query '{query}': {e}", file=sys.stderr)


async def run_script_async(main_domain, lr, queries):
    tasks = []
    query_info = {}
    for query in queries:
        query = query.strip()
        task = asyncio.create_task(process_query(query, main_domain, lr, query_info))
        tasks.append(task)
        await asyncio.sleep(0.05)

        await asyncio.gather(*tasks)

    print(f"Processing completed.", file=sys.stderr)

    return query_info


# Запуск асинхронного процесса
if __name__ == "__main__":
    asyncio.run(run_script_async("dn.ru", 213, ["кран шаровый"]))