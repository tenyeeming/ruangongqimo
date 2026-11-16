"""稿件相關的操作，狀態轉換的規則都集中在這裡。

編輯中 --送出--> 審查中 --通過--> 已通過
                  審查中 --退回--> 編輯中
"""
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from .models import CATEGORIES, Manuscript, Status, User


def _check_fields(category: str, title: str) -> str:
    if category not in CATEGORIES:
        raise HTTPException(400, "類別不正確")
    title = title.strip()
    if not title:
        raise HTTPException(400, "標題不能空白")
    if len(title) > 100:
        raise HTTPException(400, "標題最多 100 個字")
    return title


def _require_status(m: Manuscript, status: Status, message: str):
    if m.status != status:
        raise HTTPException(409, message)


def _get(session: Session, manuscript_id: int) -> Manuscript:
    m = session.get(Manuscript, manuscript_id)
    if m is None:
        raise HTTPException(404, "找不到這篇稿件")
    return m


def _save(session: Session, m: Manuscript) -> Manuscript:
    m.updated_at = datetime.now()
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


# ---------- 作者 ----------

def list_mine(session: Session, user: User):
    stmt = (select(Manuscript)
            .where(Manuscript.author_id == user.id)
            .order_by(Manuscript.updated_at.desc()))
    return session.exec(stmt).all()


def get_mine(session: Session, user: User, manuscript_id: int) -> Manuscript:
    m = _get(session, manuscript_id)
    if m.author_id != user.id:
        raise HTTPException(403, "這不是你的稿件")
    return m


def create(session: Session, user: User, category: str, title: str, content: str) -> Manuscript:
    title = _check_fields(category, title)
    m = Manuscript(author_id=user.id, category=category, title=title, content=content)
    return _save(session, m)


def update(session: Session, user: User, manuscript_id: int,
           category: str, title: str, content: str) -> Manuscript:
    m = get_mine(session, user, manuscript_id)
    _require_status(m, Status.DRAFT, "只有編輯中的稿件可以修改")
    m.title = _check_fields(category, title)
    m.category = category
    m.content = content
    return _save(session, m)


def delete(session: Session, user: User, manuscript_id: int):
    m = get_mine(session, user, manuscript_id)
    _require_status(m, Status.DRAFT, "只有編輯中的稿件可以刪除")
    session.delete(m)
    session.commit()


def submit(session: Session, user: User, manuscript_id: int) -> Manuscript:
    m = get_mine(session, user, manuscript_id)
    _require_status(m, Status.DRAFT, "這篇稿件已經送出過了")
    if not m.content.strip():
        raise HTTPException(400, "內容是空的，不能送出")
    m.status = Status.REVIEWING
    return _save(session, m)


# ---------- 編輯 ----------

def list_reviewing(session: Session):
    stmt = (select(Manuscript, User)
            .join(User, Manuscript.author_id == User.id)
            .where(Manuscript.status == Status.REVIEWING)
            .order_by(Manuscript.updated_at))
    return session.exec(stmt).all()


def get_reviewing(session: Session, manuscript_id: int):
    m = session.get(Manuscript, manuscript_id)
    # 編輯只看得到審查中的稿件
    if m is None or m.status != Status.REVIEWING:
        raise HTTPException(404, "找不到待審查的稿件")
    author = session.get(User, m.author_id)
    return m, author


def approve(session: Session, manuscript_id: int) -> Manuscript:
    m = _get(session, manuscript_id)
    _require_status(m, Status.REVIEWING, "只有審查中的稿件可以通過")
    m.status = Status.APPROVED
    return _save(session, m)


def reject(session: Session, manuscript_id: int) -> Manuscript:
    m = _get(session, manuscript_id)
    _require_status(m, Status.REVIEWING, "只有審查中的稿件可以退回")
    m.status = Status.DRAFT
    return _save(session, m)
