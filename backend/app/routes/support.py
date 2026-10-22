from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models import User
from app.schemas.dto import ChatIn
from app.services import mongo_logs

router = APIRouter()


@router.post("/", status_code=201)
def chat_message(body: ChatIn, current: User = Depends(get_current_user)):
    mongo_logs.log_chat_support(current.id, body.message)
    return {"detail": "stored", "echo": body.message[:140]}
