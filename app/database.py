import os
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select

from .models import Manuscript, Role, Status, User

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data.db'}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 預設帳號，密碼都是 123456
DEFAULT_USERS = [
    ("author1", "王小明", Role.AUTHOR),
    ("author2", "李小華", Role.AUTHOR),
    ("editor1", "陳編輯", Role.EDITOR),
]
DEFAULT_PASSWORD = "123456"


def get_session():
    with Session(engine) as session:
        yield session


def seed_users(session: Session) -> bool:
    from .auth import hash_password

    if session.exec(select(User)).first():
        return False
    for username, name, role in DEFAULT_USERS:
        session.add(User(username=username, name=name, role=role,
                         password_hash=hash_password(DEFAULT_PASSWORD)))
    session.commit()
    return True


# 範例稿件，方便展示
SAMPLE_MANUSCRIPTS = [
    ("author1", "論文", "校園二手書交易平台的需求分析",
     "本文訪談了 20 位同學，整理出二手書交易時最常遇到的問題，"
     "包括書況描述不清、面交時間難約、價格沒有參考依據。\n\n"
     "根據訪談結果，我們提出三項核心功能：書況分級、預約面交、歷史成交價查詢。",
     Status.REVIEWING),
    ("author2", "心得", "第一次參加黑客松",
     "兩天一夜的比賽比想像中累，但也學到很多。\n\n"
     "最大的收穫是學會在時間壓力下先做出能動的版本，再慢慢補功能。",
     Status.DRAFT),
]


def seed_samples(session: Session):
    if session.exec(select(Manuscript)).first():
        return
    users = {u.username: u for u in session.exec(select(User)).all()}
    for username, category, title, content, status in SAMPLE_MANUSCRIPTS:
        session.add(Manuscript(author_id=users[username].id, category=category,
                               title=title, content=content, status=status))
    session.commit()


def init_db():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # 只有第一次建立資料庫時才放範例稿件
        if seed_users(session):
            seed_samples(session)
