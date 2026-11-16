from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from .. import services
from ..auth import authenticate, require_author, require_editor
from ..database import get_session
from ..models import CATEGORIES, Role, Status, User

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter(include_in_schema=False)


def render(request: Request, name: str, status_code: int = 200, **context):
    context["flash"] = request.session.pop("flash", None)
    return templates.TemplateResponse(request, name, context, status_code=status_code)


def go(request: Request, url: str, message: str = None):
    if message:
        request.session["flash"] = message
    return RedirectResponse(url, status_code=303)


@router.get("/")
def index(request: Request, session: Session = Depends(get_session)):
    user_id = request.session.get("user_id")
    user = session.get(User, user_id) if user_id else None
    if user is None:
        return go(request, "/login")
    return go(request, "/author" if user.role == Role.AUTHOR else "/editor")


@router.get("/login")
def login_page(request: Request):
    return render(request, "login.html")


@router.post("/login")
def login(request: Request, username: str = Form(""), password: str = Form(""),
          session: Session = Depends(get_session)):
    user = authenticate(session, username, password)
    if user is None:
        return render(request, "login.html", 400, error="帳號或密碼錯誤", username=username)
    request.session["user_id"] = user.id
    return go(request, "/")


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return go(request, "/login")


# ---------- 作者 ----------

@router.get("/author")
def author_list(request: Request, user: User = Depends(require_author),
                session: Session = Depends(get_session)):
    items = services.list_mine(session, user)
    return render(request, "author_list.html", user=user, items=items, Status=Status)


@router.get("/author/new")
def author_new(request: Request, user: User = Depends(require_author)):
    return render(request, "author_form.html", user=user, m=None, categories=CATEGORIES,
                  form={"category": CATEGORIES[0], "title": "", "content": ""})


@router.post("/author/new")
def author_create(request: Request, category: str = Form(""), title: str = Form(""),
                  content: str = Form(""), action: str = Form("save"),
                  user: User = Depends(require_author), session: Session = Depends(get_session)):
    try:
        m = services.create(session, user, category, title, content)
    except HTTPException as e:
        return render(request, "author_form.html", 400, user=user, m=None, categories=CATEGORIES,
                      error=e.detail, form={"category": category, "title": title, "content": content})
    if action == "submit":
        return _submit(request, session, user, m.id)
    return go(request, "/author", "稿件已儲存")


@router.get("/author/{manuscript_id}")
def author_edit(request: Request, manuscript_id: int, user: User = Depends(require_author),
                session: Session = Depends(get_session)):
    m = services.get_mine(session, user, manuscript_id)
    return render(request, "author_form.html", user=user, m=m, categories=CATEGORIES, Status=Status,
                  form={"category": m.category, "title": m.title, "content": m.content})


@router.post("/author/{manuscript_id}")
def author_update(request: Request, manuscript_id: int, category: str = Form(""),
                  title: str = Form(""), content: str = Form(""), action: str = Form("save"),
                  user: User = Depends(require_author), session: Session = Depends(get_session)):
    try:
        m = services.update(session, user, manuscript_id, category, title, content)
    except HTTPException as e:
        if e.status_code != 400:
            raise
        m = services.get_mine(session, user, manuscript_id)
        return render(request, "author_form.html", 400, user=user, m=m, categories=CATEGORIES,
                      Status=Status, error=e.detail,
                      form={"category": category, "title": title, "content": content})
    if action == "submit":
        return _submit(request, session, user, m.id)
    return go(request, f"/author/{m.id}", "稿件已儲存")


@router.post("/author/{manuscript_id}/submit")
def author_submit(request: Request, manuscript_id: int, user: User = Depends(require_author),
                  session: Session = Depends(get_session)):
    return _submit(request, session, user, manuscript_id)


def _submit(request, session, user, manuscript_id):
    try:
        services.submit(session, user, manuscript_id)
    except HTTPException as e:
        if e.status_code not in (400, 409):
            raise
        return go(request, f"/author/{manuscript_id}", e.detail)
    return go(request, "/author", "已送出投稿，等待編輯審查")


@router.post("/author/{manuscript_id}/delete")
def author_delete(request: Request, manuscript_id: int, user: User = Depends(require_author),
                  session: Session = Depends(get_session)):
    services.delete(session, user, manuscript_id)
    return go(request, "/author", "稿件已刪除")


# ---------- 編輯 ----------

@router.get("/editor")
def editor_list(request: Request, user: User = Depends(require_editor),
                session: Session = Depends(get_session)):
    rows = services.list_reviewing(session)
    return render(request, "editor_list.html", user=user, rows=rows)


@router.get("/editor/{manuscript_id}")
def editor_detail(request: Request, manuscript_id: int, user: User = Depends(require_editor),
                  session: Session = Depends(get_session)):
    m, author = services.get_reviewing(session, manuscript_id)
    return render(request, "editor_detail.html", user=user, m=m, author=author)


@router.post("/editor/{manuscript_id}/approve")
def editor_approve(request: Request, manuscript_id: int, user: User = Depends(require_editor),
                   session: Session = Depends(get_session)):
    m = services.approve(session, manuscript_id)
    return go(request, "/editor", f"「{m.title}」已通過")


@router.post("/editor/{manuscript_id}/reject")
def editor_reject(request: Request, manuscript_id: int, user: User = Depends(require_editor),
                  session: Session = Depends(get_session)):
    m = services.reject(session, manuscript_id)
    return go(request, "/editor", f"「{m.title}」已退回給作者")
