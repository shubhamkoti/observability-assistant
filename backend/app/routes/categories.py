from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Category
from app.schemas.dto import CategoryOut

router = APIRouter()


@router.get("/", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    stmt = select(Category).order_by(Category.name)
    return db.scalars(stmt).all()
