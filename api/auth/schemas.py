import uuid
from typing import Optional

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    id: int
    username: Optional[str] = None
    email: str


class UserCreate(schemas.BaseUserCreate):
    id: int
    username: Optional[str] = None
    email: str


class UserUpdate(schemas.BaseUserUpdate):
    id: int
    username: Optional[str] = None
    email: str
