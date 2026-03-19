# api/routes.py
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId

from db.repository import (
    get_all_news,
    get_news_by_type,
    get_news_by_date_range,
)

router = APIRouter()

# ── YARDIMCI FONKSİYON ───────────────────────────────────────────────────────

def serialize_news(news_list: list) -> list:
    """ObjectId → str, datetime → ISO string dönüşümü"""
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

# Bu flag, aynı anda iki scraping işleminin çalışmasını önler
_scraping_in_progress = False

def run_scraping_pipeline():
    """Tüm scraper'ları çalıştırır, pipeline'dan geçirir, DB'ye yazar."""
    global _scraping_in_progress
    _scraping_in_progress = True
    try:
        from scraper.cagdaskocaeli   import CagdasKocaeliScraper
        from scraper.ozgurkocaeli    import OzgurKocaeliScraper
        from scraper.seskocaeli      import SesKocaeliScraper
        from scraper.yenikocaeli     import YeniKocaeliScraper
        from scraper.bizimyaka       import BizimYakaScraper

        from pipeline.cleaner            import clean_news
        from pipeline.classifier         import classify_news
        from pipeline.location_extractor import extract_location
        from pipeline.geocoder           import geocode_location
        from pipeline.deduplicator       import deduplicate_articles
        from db.repository               import insert_news
        from datetime                    import datetime

        scrapers = [
            CagdasKocaeliScraper(),
            OzgurKocaeliScraper(),
            SesKocaeliScraper(),
            YeniKocaeliScraper(),
            BizimYakaScraper(),
        ]

        # ── AŞAMA 1: Tüm scraper'lardan ham veri topla ───────────────── #
        candidates = []

        for scraper in scrapers:
            print(f"🕷️  {scraper.site_name} scraping başladı...")
            try:
                raw_news_list = scraper.get_news()
            except Exception as e:
                print(f"❌ {scraper.site_name} scraper hatası: {e}")
                continue

            for raw in raw_news_list:
                try:
                    # 1. Temizle
                    news = clean_news(raw)

                    # 2. Sınıflandır — kategori yoksa atla
                    news_type = classify_news(news["content"])
                    if not news_type:
                        continue
                    news["news_type"] = news_type

                    # 3. Konum çıkar
                    location_text = extract_location(news["content"])
                    if not location_text:
                        continue  # Konum yoksa haritada gösterilemez, kaydetme
                    news["location_text"] = location_text

                    # 4. Geocode et — başarısızsa atla
                    coords = geocode_location(location_text)
                    if not coords:
                        continue
                    news["location_coords"] = coords

                    news["scraped_at"] = datetime.utcnow()
                    candidates.append(news)

                except Exception as e:
                    print(f"⚠️  Haber işleme hatası: {e}")

        print(f"📋 Pipeline çıktısı: {len(candidates)} aday haber")

        # ── AŞAMA 2: Tüm adayları toplu duplicate kontrolünden geçir ─── #
        # deduplicate_articles hem link kontrolü hem embedding karşılaştırması yapar.
        # Duplicate olanlar için mevcut haberin sources listesini günceller (DB'ye yazar).
        # Geriye yalnızca gerçekten yeni haberler döner.
        unique_news = deduplicate_articles(candidates)

        # ── AŞAMA 3: Yeni haberleri DB'ye kaydet ─────────────────────── #
        saved = 0
        for news in unique_news:
            try:
                insert_news(news)
                saved += 1
            except Exception as e:
                print(f"⚠️  DB kayıt hatası: {e}")

        print(f"✅ Scraping tamamlandı. {saved} yeni haber kaydedildi.")

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
    news_type: Optional[str] = Query(None, description="Haber türü (ör: Yangın)"),
    district:  Optional[str] = Query(None, description="İlçe adı (ör: İzmit)"),
    start_date: Optional[str] = Query(None, description="Başlangıç tarihi (YYYY-MM-DD)"),
    end_date:   Optional[str] = Query(None, description="Bitiş tarihi (YYYY-MM-DD)"),
):
    mongo_filter = {}

    # Tür filtresi
    if news_type:
        mongo_filter["news_type"] = news_type

    # İlçe filtresi
    if district:
        mongo_filter["district"] = {"$regex": district, "$options": "i"}

    # Tarih filtresi
    if start_date or end_date:
        date_filter = {}
        try:
            if start_date:
                date_filter["$gte"] = datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                # Bitiş gününün sonuna kadar (23:59:59)
                date_filter["$lte"] = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
        except ValueError:
            raise HTTPException(status_code=400, detail="Tarih formatı yanlış. YYYY-MM-DD kullanın.")
        mongo_filter["published_at"] = date_filter

    news_list = get_all_news(mongo_filter)
    return {"count": len(news_list), "news": serialize_news(news_list)}


@router.get("/news/{news_id}", summary="Tek haber getir")
def get_single_news(news_id: str):
    from db.connection import news_collection
    try:
        oid = ObjectId(news_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz haber ID.")

    item = news_collection().find_one({"_id": oid}, {"embedding": 0})  # () eklendi
    if not item:
        raise HTTPException(status_code=404, detail="Haber bulunamadı.")

    return serialize_news([item])[0]


@router.get("/filter/options", summary="Filtre dropdown seçenekleri")
def filter_options():
    from db.connection import news_collection

    news_types = news_collection().distinct("news_type")  # () eklendi
    districts   = news_collection().distinct("district")   # () eklendi

    news_types = sorted([t for t in news_types if t])
    districts  = sorted([d for d in districts  if d])

    return {
        "news_types": news_types,
        "districts":  districts,
    }
# api/routes.py içine ekleyin
@router.get("/config/maps-key")
async def get_maps_key():
    from config import GOOGLE_MAPS_KEY   # ← direkt değişken
    return {"key": GOOGLE_MAPS_KEY}