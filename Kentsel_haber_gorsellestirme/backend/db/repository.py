# CRUD işlemleri
from db.connection import news_collection, geocache_collection
from datetime import datetime

# ── HABER İŞLEMLERİ ──────────────────────────────────────

def insert_news(news: dict) -> str:
    result = news_collection().insert_one(news)
    return str(result.inserted_id)

def get_all_news(filter_query=None, sort_by="published_at", sort_order=-1):
    collection = news_collection()
    cursor = collection.find(filter_query or {}, {"embedding": 0})
    cursor = cursor.sort(sort_by, sort_order)
    return list(cursor)

def get_news_by_type(news_type: str) -> list:
    return list(news_collection().find({"news_type": news_type}, {"embedding": 0}))

def get_news_by_date_range(start: datetime, end: datetime) -> list:
    return list(news_collection().find({
        "published_at": {"$gte": start, "$lte": end}
    }, {"embedding": 0}))

def news_url_exists(url: str) -> bool:
    return news_collection().count_documents({"sources.url": url}) > 0

def get_all_embeddings() -> list:
    return list(news_collection().find({}, {"_id": 1, "embedding": 1, "sources": 1}))

def add_source_to_news(news_id, source: dict):
    from bson import ObjectId
    news_collection().update_one(
        {"_id": ObjectId(news_id)},
        {"$push": {"sources": source}}
    )

# ── GEOCACHE İŞLEMLERİ ───────────────────────────────────

def get_cached_location(query: str) -> dict | None:
    return geocache_collection().find_one({"query": query})

def cache_location(query: str, lat: float, lng: float):
    geocache_collection().insert_one({
        "query": query,
        "lat": lat,
        "lng": lng,
        "cached_at": datetime.utcnow()
    })