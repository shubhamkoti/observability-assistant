from datetime import datetime, timezone
from typing import Any

from pymongo.collection import Collection

from app.database.mongo import get_mongo_db


def _col(name: str) -> Collection:
    return get_mongo_db()[name]


def log_product_view(user_id: int | None, product_id: int, meta: dict[str, Any] | None = None) -> None:
    _col("product_view_logs").insert_one(
        {
            "user_id": user_id,
            "product_id": product_id,
            "ts": datetime.now(timezone.utc),
            "meta": meta or {},
        }
    )


def log_recommendation(user_id: int | None, payload: dict[str, Any]) -> None:
    _col("recommendation_logs").insert_one({"user_id": user_id, "ts": datetime.now(timezone.utc), **payload})


def log_user_activity(user_id: int | None, action: str, details: dict[str, Any]) -> None:
    _col("user_activity_logs").insert_one(
        {"user_id": user_id, "action": action, "details": details, "ts": datetime.now(timezone.utc)}
    )


def log_notification_event(notification_id: int, user_id: int, payload: dict[str, Any]) -> None:
    _col("notification_logs").insert_one(
        {"notification_id": notification_id, "user_id": user_id, "ts": datetime.now(timezone.utc), **payload}
    )


def log_chat_support(user_id: int, message: str, channel: str = "web") -> None:
    _col("chat_support_messages").insert_one(
        {"user_id": user_id, "message": message, "channel": channel, "ts": datetime.now(timezone.utc)}
    )


def log_audit(actor_id: int | None, topic: str, payload: dict[str, Any]) -> None:
    _col("audit_logs").insert_one(
        {"actor_id": actor_id, "topic": topic, "payload": payload, "ts": datetime.now(timezone.utc)}
    )
