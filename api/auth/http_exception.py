# error_handlers.py
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

templates = Jinja2Templates(directory="static")


def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return RedirectResponse(url=request.url_for('login_page'))
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
