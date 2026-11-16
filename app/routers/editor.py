from fastapi import APIRouter, Depends
from sqlmodel import Session

from .. import services
from ..auth import require_editor
from ..database import get_session
from ..schemas import ManuscriptOut, ReviewDetail, ReviewItem

router = APIRouter(prefix="/api/reviews", tags=["編輯"], dependencies=[Depends(require_editor)])


@router.get("", response_model=list[ReviewItem])
def list_reviews(session: Session = Depends(get_session)):
    return [ReviewItem.of(m, author) for m, author in services.list_reviewing(session)]


@router.get("/{manuscript_id}", response_model=ReviewDetail)
def get_review(manuscript_id: int, session: Session = Depends(get_session)):
    m, author = services.get_reviewing(session, manuscript_id)
    return ReviewDetail.of(m, author)


@router.post("/{manuscript_id}/approve", response_model=ManuscriptOut)
def approve(manuscript_id: int, session: Session = Depends(get_session)):
    return ManuscriptOut.of(services.approve(session, manuscript_id))


@router.post("/{manuscript_id}/reject", response_model=ManuscriptOut)
def reject(manuscript_id: int, session: Session = Depends(get_session)):
    return ManuscriptOut.of(services.reject(session, manuscript_id))
