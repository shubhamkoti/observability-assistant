from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user_optional
from app.database.session import get_db
from app.models import User
from app.services import mongo_logs

router = APIRouter()


@router.get("/")
def recommend_top(
    db: Session = Depends(get_db),
    current: User | None = Depends(get_current_active_user_optional),
):
    rows = db.execute(text("SELECT product_id, name FROM v_top_selling_products LIMIT 6")).mappings().all()
    payload = {"strategy": "view_top_selling", "items": [dict(r) for r in rows]}
    mongo_logs.log_recommendation(current.id if current else None, payload)
    return payload
