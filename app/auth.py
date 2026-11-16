import hashlib
import hmac
import os

from fastapi import Depends, HTTPException, Request
from sqlmodel import Session, select

from .database import get_session
from .models import Role, User


class LoginRequired(Exception):
    pass


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt.hex() + "$" + digest.hex()


def verify_password(password: str, stored: str) -> bool:
    salt_hex, digest_hex = stored.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 100_000)
    return hmac.compare_digest(digest.hex(), digest_hex)


def authenticate(session: Session, username: str, password: str):
    user = session.exec(select(User).where(User.username == username)).first()
    if user and verify_password(password, user.password_hash):
        return user
    return None


def get_current_user(request: Request, session: Session = Depends(get_session)) -> User:
    user_id = request.session.get("user_id")
    user = session.get(User, user_id) if user_id else None
    if user is None:
        raise LoginRequired()
    return user


def require_author(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.AUTHOR:
        raise HTTPException(403, "只有作者可以使用這個功能")
    return user


def require_editor(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.EDITOR:
        raise HTTPException(403, "只有編輯可以使用這個功能")
    return user
