from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, joinedload

from app.database.session import get_db
from app.models import User
from app.utils.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)


def _sub_from_optional_creds(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str | None:
    if creds is None:
        return None
    try:
        payload = decode_access_token(creds.credentials)
        return str(payload["sub"])
    except (ValueError, KeyError):
        return None


def get_current_active_user_optional(
    db: Session = Depends(get_db),
    sub: str | None = Depends(_sub_from_optional_creds),
) -> User | None:
    if sub is None:
        return None
    user = (
        db.query(User)
        .options(joinedload(User.roles))
        .filter(User.id == int(sub))
        .first()
    )
    if not user or not user.is_active:
        return None
    return user


def _load_user(db: Session, sub: str) -> User:
    user = (
        db.query(User)
        .options(joinedload(User.roles))
        .filter(User.id == int(sub))
        .first()
    )
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")
    return user


def get_current_user(
    db: Session = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> User:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    try:
        payload = decode_access_token(creds.credentials)
        sub = str(payload["sub"])
    except (ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return _load_user(db, sub)


def require_roles(*role_names: str) -> Callable:
    normalized = set(role_names)

    def _dep(current: User = Depends(get_current_user)) -> User:
        names = {r.name for r in current.roles}
        if not normalized.intersection(names):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient privileges")
        return current

    return _dep
