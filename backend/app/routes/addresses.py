from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models import Address, User
from app.schemas.dto import AddressIn, AddressOut

router = APIRouter()


@router.get("/", response_model=list[AddressOut])
def list_addresses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Address).where(Address.user_id == user.id).order_by(Address.is_default.desc())
    return db.scalars(stmt).all()


@router.post("/", response_model=AddressOut)
def create_address(body: AddressIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.is_default:
        db.execute(update(Address).where(Address.user_id == user.id).values(is_default=False))
    addr = Address(user_id=user.id, **body.model_dump())
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr


@router.delete("/{address_id}", status_code=204)
def delete_address(address_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    res = db.execute(delete(Address).where(Address.id == address_id, Address.user_id == user.id))
    if res.rowcount == 0:
        raise HTTPException(404, "Address not found")
    db.commit()
    return
