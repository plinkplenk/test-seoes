import re
import aiohttp
import aiofiles
import asyncio
import xml.etree.ElementTree as ET
import urllib.parse
from datetime import datetime
import sys

import idna

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
                    url = value["url"]
                    parsed_url = urllib.parse.urlparse(url)
                    # Проверяем и декодируем домен
                    try:
                        decoded_netloc = idna.decode(parsed_url.netloc)
                    except idna.IDNAError:
                        decoded_netloc = parsed_url.netloc  # Если ошибка, оставляем как есть

                    # Собираем обратно URL
                    decoded_url = urllib.parse.urlunparse((parsed_url.scheme, decoded_netloc, parsed_url.path, parsed_url.params, parsed_url.query, parsed_url.fragment))
                    pattern = fr'{re.escape(MAIN_DOMAIN)}'
                    if re.search(pattern, decoded_url):
                        if query not in query_info:
                            query_info[query] = [value["url"], int(key)]
    except Exception as e:
        print(f"Error processing query '{query}': {e}", file=sys.stderr)


async def run_script_async(main_domain, lr, queries):
    tasks = []
    query_info = {}
    for query in queries:
        query = query.strip()
        task = asyncio.create_task(process_query(query, main_domain, lr, query_info))
        tasks.append(task)

        await asyncio.gather(*tasks)

    print(f"Processing completed.", file=sys.stderr)

    return query_info


# Запуск асинхронного процесса
if __name__ == "__main__":
    asyncio.run(run_script_async())