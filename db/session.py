from typing import Generator

from fastapi import Depends

import config

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from api.auth.models import User

##############################################
# BLOCK FOR COMMON INTERACTION WITH DATABASE #
##############################################

# REAL_DATABASE_URL = f"postgresql+asyncpg://mainuser:Kirill123456@5.35.81.91:5432/products"

GENERAL_DATABASE_URL = f"postgresql+asyncpg://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DATABASE_GENERAL_NAME}"

engine_general = create_async_engine(
    GENERAL_DATABASE_URL,
    future=True,
    pool_size=20,
    max_overflow=10,
    execution_options={"isolation_level": "AUTOCOMMIT"},
)

async_session_general = sessionmaker(engine_general, expire_on_commit=False, class_=AsyncSession)


async def connect_db(db_name: str):
    db_name_bound = f"{db_name}"
    try:
        REAL_DATABASE_URL = f"postgresql+asyncpg://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{db_name_bound}"
        engine = create_async_engine(
            REAL_DATABASE_URL,
            future=True,
            execution_options={"isolation_level": "AUTOCOMMIT"},
        )
        async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    except Exception as e:
        print("Ошибка при подключении к БД:", e)
        return -1
    return async_session


async def get_db(db_name) -> Generator:
    """Dependency for getting async session"""
    try:
        session: AsyncSession = await create_db(db_name)
        yield session
    finally:
        await session.close()


async def get_db_general() -> Generator:
    """Dependency for getting async session"""
    try:
        session: AsyncSession = async_session_general()
        yield session
    finally:
        await session.close()
