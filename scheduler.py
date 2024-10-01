import asyncio
from time import sleep
from pytz import utc, all_timezones

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger

import config

_db_url = f"postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DATABASE_GENERAL_NAME}"

jobstores = {
    "sqlalchemy": SQLAlchemyJobStore(url=_db_url)
}

scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="Europe/Moscow")