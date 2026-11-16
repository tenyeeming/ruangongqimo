from datetime import datetime

from pydantic import BaseModel

from .models import Manuscript, User


class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    name: str
    role: str


class ManuscriptIn(BaseModel):
    category: str
    title: str
    content: str = ""


class ManuscriptOut(BaseModel):
    id: int
    category: str
    title: str
    content: str
    status: str
    updated_at: datetime

    @classmethod
    def of(cls, m: Manuscript):
        return cls(id=m.id, category=m.category, title=m.title, content=m.content,
                   status=m.status.label, updated_at=m.updated_at)


class ReviewItem(BaseModel):
    id: int
    author: str
    category: str
    title: str

    @classmethod
    def of(cls, m: Manuscript, author: User):
        return cls(id=m.id, author=author.name, category=m.category, title=m.title)


class ReviewDetail(ReviewItem):
    content: str
    updated_at: datetime

    @classmethod
    def of(cls, m: Manuscript, author: User):
        return cls(id=m.id, author=author.name, category=m.category, title=m.title,
                   content=m.content, updated_at=m.updated_at)
