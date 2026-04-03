from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from datetime import datetime
from typing import Optional
from bson import ObjectId
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.responses import JSONResponse

from db.repository import get_all_news, get_news_by_type, get_news_by_date_range

router = APIRouter()

# ── YARDIMCI ─────────────────────────────────────────────────────────────────

def serialize_news(news_list: list) -> list:
    result = []
    for item in news_list:
        item["_id"] = str(item["_id"])
        if isinstance(item.get("published_at"), datetime):
            item["published_at"] = item["published_at"].isoformat()
        if isinstance(item.get("scraped_at"), datetime):
            item["scraped_at"] = item["scraped_at"].isoformat()
        result.append(item)
    return result

# ── SCRAPING ─────────────────────────────────────────────────────────────────

_scraping_in_progress = False

def _run_scraper(scraper) -> list:
    """Tek bir scraper'ı çalıştırır — thread içinde çağrılır."""
    print(f"🕷️  {scraper.site_name} scraping başladı...")
    t0 = time.time()
    try:
        news = scraper.get_news()
        elapsed = time.time() - t0
        print(f"⏱️  {scraper.site_name}: {len(news)} haber / {elapsed:.1f}s")
        return news
    except Exception as e:
        print(f"❌ {scraper.site_name} scraper hatası: {e}")
        return []


def run_scraping_pipeline():
    """Tüm scraper'ları paralel çalıştırır, pipeline'dan geçirir, DB'ye yazar."""
    global _scraping_in_progress
    _scraping_in_progress = True
    pipeline_start = time.time()

    try:
        from scraper.daktilo_scraper import (
            CagdasKocaeliScraper, OzgurKocaeliScraper,
            SesKocaeliScraper, BizimYakaScraper,
        )
        from scraper.yenikocaeli import YeniKocaeliScraper
        from pipeline.cleaner            import clean_articles
        from pipeline.classifier         import classify_articles
        from pipeline.location_extractor import extract_locations
        from pipeline.geocoder           import geocode_articles
        from pipeline.deduplicator       import deduplicate_articles
        from db.repository               import insert_news

        scrapers = [
            CagdasKocaeliScraper(),
            OzgurKocaeliScraper(),
            SesKocaeliScraper(),
            BizimYakaScraper(),
            YeniKocaeliScraper(),
        ]

        print("=" * 55)
        print(f"🚀 Scraping başladı — {len(scrapers)} site PARALEL çalışıyor")
        print("=" * 55)

        # ── 5 site aynı anda ────────────────────────────────────
        raw_all = []
        scrape_start = time.time()
        with ThreadPoolExecutor(max_workers=len(scrapers)) as executor:
            futures = {executor.submit(_run_scraper, s): s for s in scrapers}
            for future in as_completed(futures):
                raw_all.extend(future.result())

        scrape_elapsed = time.time() - scrape_start
        print(f"⏱️  Toplam scraping süresi: {scrape_elapsed:.1f}s")
        print(f"📥 Ham haber toplamı: {len(raw_all)}")

        # ── Pipeline ────────────────────────────────────────────
        cleaned    = clean_articles(raw_all)
        classified = classify_articles(cleaned)
        classified = [n for n in classified
                      if n.get("news_type") and n["news_type"] != "Diğer"]
        print(f"🏷️  Sınıflandırma sonrası: {len(classified)} haber")

        located = extract_locations(classified)
        located = [n for n in located if n.get("location_text")]
        print(f"📍 Konum bulunan: {len(located)} haber")

        geocoded = geocode_articles(located)
        geocoded = [n for n in geocoded if n.get("location_coords")]
        print(f"🌍 Geocode başarılı: {len(geocoded)} haber")

        unique_news = deduplicate_articles(geocoded)
        print(f"📋 Unique haber: {len(unique_news)}")

        saved = 0
        for news in unique_news:
            try:
                insert_news(news)
                saved += 1
            except Exception as e:
                print(f"⚠️  DB kayıt hatası: {e}")

        total_elapsed = time.time() - pipeline_start
        print("=" * 55)
        print(f"✅ Scraping tamamlandı — {saved} yeni haber kaydedildi")
        print(f"⏱️  Toplam süre: {total_elapsed:.1f}s")
        print("=" * 55)

    except Exception as e:
        print(f"❌ Pipeline genel hatası: {e}")
        import traceback
        traceback.print_exc()
    finally:
        _scraping_in_progress = False


@router.post("/scrape", summary="Scraping işlemini manuel tetikle")
def trigger_scrape(background_tasks: BackgroundTasks):
    global _scraping_in_progress
    if _scraping_in_progress:
        raise HTTPException(status_code=409, detail="Scraping zaten devam ediyor.")
    background_tasks.add_task(run_scraping_pipeline)
    return {"status": "started", "message": "Scraping arka planda başlatıldı."}


@router.get("/scrape/status", summary="Scraping durumu")
def scrape_status():
    return {"in_progress": _scraping_in_progress}


# ── HABERLER ─────────────────────────────────────────────────────────────────

@router.get("/news", summary="Tüm haberleri getir (isteğe bağlı filtre)")
def get_news(
    news_type:  Optional[str] = Query(None),
    district:   Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
):
    mongo_filter = {}
    if news_type:
        mongo_filter["news_type"] = news_type
    if district:
        mongo_filter["district"] = {"$regex": district, "$options": "i"}
    if start_date or end_date:
        date_filter = {}
        try:
            if start_date:
                date_filter["$gte"] = datetime.strptime(start_date, "%Y-%m-%d").replace(
                    hour=0, minute=0, second=0, microsecond=0)
            if end_date:
                date_filter["$lte"] = datetime.strptime(end_date, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            raise HTTPException(status_code=400, detail="Tarih formatı yanlış. YYYY-MM-DD kullanın.")
        mongo_filter["published_at"] = date_filter

    news_list = get_all_news(mongo_filter, sort_by="published_at", sort_order=-1)
    return {"count": len(news_list), "news": serialize_news(news_list)}


@router.delete("/news", summary="Tüm haberleri veritabanından sil")
def delete_all_news():
    from db.connection import news_collection
    result = news_collection().delete_many({})
    deleted = result.deleted_count
    print(f"🗑️  {deleted} haber veritabanından silindi.")
    return {"deleted": deleted, "message": f"{deleted} haber silindi."}


@router.get("/news/{news_id}", summary="Tek haber getir")
def get_single_news(news_id: str):
    from db.connection import news_collection
    try:
        oid = ObjectId(news_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz haber ID.")
    item = news_collection().find_one({"_id": oid}, {"embedding": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Haber bulunamadı.")
    return serialize_news([item])[0]


@router.get("/filter/options", summary="Filtre dropdown seçenekleri")
def filter_options():
    """
    Filtre seçeneklerini statik olarak döndürür.
    Böylece veritabanı boş olsa bile (Cold Start problemi) 
    arayüzde filtreler her zaman eksiksiz görünür.
    """
    news_types = [
        "Elektrik Kesintisi",
        "Hırsızlık",
        "Kültürel Etkinlikler",
        "Trafik Kazası",
        "Yangın"
    ]
    
    districts = [
        "Başiskele",
        "Çayırova",
        "Darıca",
        "Derince",
        "Dilovası",
        "Gebze",
        "Gölcük",
        "İzmit",
        "Kandıra",
        "Karamürsel",
        "Kartepe",
        "Körfez"
    ]
    
    return {"news_types": news_types, "districts": districts}


@router.get("/config/maps-key")
async def get_maps_key():
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not key:
        print("⚠️ HATA: GOOGLE_MAPS_API_KEY okunamadı!")
        return JSONResponse({"key": "", "error": "API Key not found"}, status_code=200)
    return {"key": key}