from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from starlette.middleware.sessions import SessionMiddleware

# import settings
import config
from fastapi import FastAPI, HTTPException
from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from api.admin_handlers import admin_router
from api.auth.auth_config import fastapi_users, auth_backend
from api.auth.http_exception import http_exception_handler
from api.auth.schemas import UserRead, UserCreate

from api.services.router import router as services_router

from api.config.router import router as config_router

from api.auth.router import router as auth_router
from config import SECRET
from scheduler import CronTrigger, scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    scheduler.add_job(print_scheduler_jobs, trigger=CronTrigger(second="*/10", day_of_week="0,1,2,3"), id="scheduler jobs logger")
    yield


async def print_scheduler_jobs():
    print(f"time = {datetime.now()} jobs = {scheduler.get_jobs()}")

app = FastAPI(
    title="Metrics urls",
    redoc_url=None,
    docs_url="/docs",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS

origins = [
    "http://192.168.1.79:8001",
]

app.add_exception_handler(HTTPException, http_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=SECRET)

main_api_router = APIRouter()
main_api_router.include_router(admin_router, prefix="/admin")

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(main_api_router)

app.include_router(auth_router)

app.include_router(services_router, prefix="/services")

app.include_router(config_router, prefix="/config")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(config.APP_PORT), reload=True)
