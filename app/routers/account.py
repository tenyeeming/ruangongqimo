from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from ..auth import authenticate, get_current_user
from ..database import get_session
from ..models import User
from ..schemas import LoginIn, UserOut

router = APIRouter(prefix="/api", tags=["帳號"])


def _user_out(user: User) -> UserOut:
    return UserOut(id=user.id, username=user.username, name=user.name, role=user.role.value)


@router.post("/login", response_model=UserOut)
def login(data: LoginIn, request: Request, session: Session = Depends(get_session)):
    user = authenticate(session, data.username, data.password)
    if user is None:
        raise HTTPException(401, "帳號或密碼錯誤")
    request.session["user_id"] = user.id
    return _user_out(user)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return _user_out(user)
