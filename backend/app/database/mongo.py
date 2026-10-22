from pymongo import MongoClient

from app.config import settings

_client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongo_uri)
    return _client


def get_mongo_db():
    return get_mongo_client()[settings.mongo_db]
