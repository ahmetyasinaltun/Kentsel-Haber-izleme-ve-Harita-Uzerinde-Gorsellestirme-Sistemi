import logging
import certifi
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure
from config import MONGO_URI, MONGO_DB_NAME

logger = logging.getLogger(__name__)
_client: MongoClient | None = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            tls=True,
            tlsCAFile=certifi.where(),
            tlsAllowInvalidCertificates=True
        )
        try:
            _client.admin.command("ping")
            logger.info("MongoDB bağlantısı başarılı")
        except ConnectionFailure as e:
            logger.error("MongoDB bağlantısı kurulamadı: %s", e)
            raise
    return _client

def get_db() -> Database:
    return get_client()[MONGO_DB_NAME]

def news_collection() -> Collection:
    return get_db()["news"]

def geocache_collection() -> Collection:
    return get_db()["geocache"]

def test_connection() -> bool:
    try:
        get_client().admin.command("ping")
        logger.info("MongoDB Atlas bağlantısı başarılı!")
        return True
    except ConnectionFailure as e:
        logger.error("Bağlantı hatası: %s", e)
        return False

def close_connection() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
def get_news_collection() -> Collection:
    return get_db()["news"]

def get_geocache_collection() -> Collection:
    return get_db()["geocache"]        