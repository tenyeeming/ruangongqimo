from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


CATEGORIES = ["論文", "心得", "新聞", "其他"]


class Role(str, Enum):
    AUTHOR = "author"
    EDITOR = "editor"

    @property
    def label(self):
        return "作者" if self == Role.AUTHOR else "編輯"


class Status(str, Enum):
    DRAFT = "draft"
    REVIEWING = "reviewing"
    APPROVED = "approved"

    @property
    def label(self):
        return {"draft": "編輯中", "reviewing": "審查中", "approved": "已通過"}[self.value]


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    name: str
    password_hash: str
    role: Role


class Manuscript(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="user.id", index=True)
    category: str
    title: str
    content: str = ""
    status: Status = Field(default=Status.DRAFT)
    created_at: datetime = Field(default_factory=datetime.now, sa_type=DateTime)
    updated_at: datetime = Field(default_factory=datetime.now, sa_type=DateTime)
