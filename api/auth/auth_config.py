from fastapi import Depends, HTTPException
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, JWTStrategy, CookieTransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.auth.manager import get_user_manager
from api.auth.models import User
from api.config.models import Role
from config import SECRET
from db.session import get_db_general

cookie_transport = CookieTransport(cookie_name="bonds", cookie_secure=False, cookie_samesite="lax",
                                   cookie_max_age=31536000)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=31536000)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_superuser = fastapi_users.current_user(active=True, superuser=True)
current_user = fastapi_users.current_user(active=True, optional=True)


class RoleChecker:

    def __init__(self, required_permissions: set[str]) -> None:
        self.required_permissions = required_permissions

    async def __call__(
            self,
            user: User = Depends(current_user),
            session: AsyncSession = Depends(get_db_general),
    ) -> bool:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='not enough permissions'
            )
        user_role = ((await session.execute(select(Role.name).where(Role.id == user.role))).fetchone())[0]
        if user_role not in self.required_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='not enough permissions'
            )
        return True
