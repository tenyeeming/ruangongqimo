from fastapi import APIRouter, Depends
from sqlmodel import Session

from .. import services
from ..auth import require_author
from ..database import get_session
from ..models import User
from ..schemas import ManuscriptIn, ManuscriptOut

router = APIRouter(prefix="/api/manuscripts", tags=["作者"])


@router.get("", response_model=list[ManuscriptOut])
def list_manuscripts(user: User = Depends(require_author), session: Session = Depends(get_session)):
    return [ManuscriptOut.of(m) for m in services.list_mine(session, user)]


@router.post("", response_model=ManuscriptOut, status_code=201)
def create_manuscript(data: ManuscriptIn, user: User = Depends(require_author),
                      session: Session = Depends(get_session)):
    m = services.create(session, user, data.category, data.title, data.content)
    return ManuscriptOut.of(m)


@router.get("/{manuscript_id}", response_model=ManuscriptOut)
def get_manuscript(manuscript_id: int, user: User = Depends(require_author),
                   session: Session = Depends(get_session)):
    return ManuscriptOut.of(services.get_mine(session, user, manuscript_id))


@router.put("/{manuscript_id}", response_model=ManuscriptOut)
def update_manuscript(manuscript_id: int, data: ManuscriptIn, user: User = Depends(require_author),
                      session: Session = Depends(get_session)):
    m = services.update(session, user, manuscript_id, data.category, data.title, data.content)
    return ManuscriptOut.of(m)


@router.delete("/{manuscript_id}", status_code=204)
def delete_manuscript(manuscript_id: int, user: User = Depends(require_author),
                      session: Session = Depends(get_session)):
    services.delete(session, user, manuscript_id)


@router.post("/{manuscript_id}/submit", response_model=ManuscriptOut)
def submit_manuscript(manuscript_id: int, user: User = Depends(require_author),
                      session: Session = Depends(get_session)):
    return ManuscriptOut.of(services.submit(session, user, manuscript_id))
