import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from .auth import LoginRequired
from .database import init_db
from .routers import account, author, editor, pages

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="投稿審查系統", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent / "static"), name="static")

app.include_router(account.router)
app.include_router(author.router)
app.include_router(editor.router)
app.include_router(pages.router)


def _is_api(request: Request):
    return request.url.path.startswith("/api")


@app.exception_handler(LoginRequired)
async def handle_login_required(request: Request, exc: LoginRequired):
    if _is_api(request):
        return JSONResponse({"detail": "請先登入"}, status_code=401)
    return RedirectResponse("/login", status_code=303)


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(request: Request, exc: StarletteHTTPException):
    if _is_api(request):
        return await http_exception_handler(request, exc)
    return pages.templates.TemplateResponse(
        request, "error.html", {"code": exc.status_code, "message": exc.detail},
        status_code=exc.status_code)
