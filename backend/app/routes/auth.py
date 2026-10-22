from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models import Role, SellerProfile, User
from app.schemas.dto import TokenOut, UserLoginIn, UserOut, UserRegisterIn
from app.services import mongo_logs
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter()


@router.post("/register", response_model=TokenOut)
def register(body: UserRegisterIn, db: Session = Depends(get_db)):
    exists = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    db.flush()

    customer = db.execute(select(Role).where(Role.name == "customer")).scalar_one()
    user.roles.append(customer)

    if body.seller_shop_name:
        seller_role = db.execute(select(Role).where(Role.name == "seller")).scalar_one()
        user.roles.append(seller_role)
        db.add(SellerProfile(user_id=user.id, shop_name=body.seller_shop_name))

    db.commit()
    full = db.execute(select(User).options(joinedload(User.roles)).where(User.id == user.id)).unique().scalar_one()
    mongo_logs.log_user_activity(full.id, "REGISTER", {"email": full.email})
    token = create_access_token(str(full.id), extra={"roles": [r.name for r in full.roles]})
    return TokenOut(access_token=token)


@router.post("/login", response_model=TokenOut)
def login(body: UserLoginIn, db: Session = Depends(get_db)):
    stmt = select(User).options(joinedload(User.roles)).where(User.email == body.email)
    user = db.execute(stmt).unique().scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")
    token = create_access_token(str(user.id), extra={"roles": [r.name for r in user.roles]})
    mongo_logs.log_user_activity(user.id, "LOGIN", {"email": user.email})
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current
