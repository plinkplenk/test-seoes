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


async def process_query(query, result_file, MAIN_DOMAIN):
    global completed_task
    encoded_query = await urlencode_string(query)
    request_url = f"""{xml_config.API_URL}?
                    user={xml_config.USER_ID}&
                    key={xml_config.API_KEY}&
                    query={encoded_query}&
                    groupby={xml_config.GROUP_BY}&
                    domain={xml_config.DOMAIN}&
                    lr={xml_config.LR}&
                    device={xml_config.DEVICE}"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(request_url) as response:
                response_text = await response.text()
                root = ET.fromstring(response_text.encode("utf-8"))
                group_count = len(root.findall(".//group"))
                for i in range(1, group_count + 1):
                    domain = root.find(f".//group[{i}]/doc/domain").text
                    url = root.find(f".//group[{i}]/doc/url")
                    url = url.text if url is not None else "URL не найден"
                    if domain == MAIN_DOMAIN:
                        await result_file.write(f"{url}\t{query}\n")
                        completed_task += 1
                        if completed_task % 100 == 0:
                            print(f"{completed_task} queries complete")
    except Exception as e:
        print(f"Error processing query '{query}': {e}", file=sys.stderr)


async def run_bash_async(main_domain, group):
    RESULT_FILE = f"results_main_domain_async.txt"
    # Очистка файлов перед началом
    async with aiofiles.open(RESULT_FILE, 'w') as f:
        pass
    # Запись даты и сервиса съема в файл результатов
    async with aiofiles.open(RESULT_FILE, 'a', encoding="utf-8") as f:
        await f.write(f"Дата съема: {datetime.now()}\n")
        await f.write("Сервис съема: Yandex XML\n")
        await f.write("URL\tЗапрос\tПозиция\n")

    # Чтение запросов из файла
    async with aiofiles.open(f"queries.txt", "r", encoding="utf-8") as f:
        queries = await f.readlines()

    tasks = []
    async with aiofiles.open(RESULT_FILE, 'a', encoding="utf-8") as result_file:
        for query in queries:
            query = query.strip()
            task = asyncio.create_task(process_query(query, result_file, main_domain))
            tasks.append(task)
            await asyncio.sleep(0.2)  # Добавление тайм-аута между запросами

        await asyncio.gather(*tasks)

    print(f"Processing completed. Results are saved in {RESULT_FILE} and respective competitor files.", file=sys.stderr)


# Запуск асинхронного процесса
if __name__ == "__main__":
    asyncio.run(run_bash_async())