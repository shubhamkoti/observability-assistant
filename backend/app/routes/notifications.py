from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import Session


from app.api.deps import get_current_user
from app.database.session import get_db
from app.models import Notification, User
from app.schemas.dto import NotificationOut

router = APIRouter()


@router.get("/", response_model=list[NotificationOut])
def list_notifications(limit: int = 50, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = (
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    return db.scalars(stmt).all()


@router.post("/mark-all-read")
def mark_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.execute(update(Notification).where(Notification.user_id == user.id).values(is_read=True))
    db.commit()
    return {"detail": "ok"}
