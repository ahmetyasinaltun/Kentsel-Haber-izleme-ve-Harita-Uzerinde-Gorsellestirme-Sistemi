# Google Geocoding API + cache
# pipeline/geocoder.py — Google Geocoding API + MongoDB cache

import os
import requests
from datetime import datetime
from db.connection import get_db

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEOCODING_URL  = "https://maps.googleapis.com/maps/api/geocode/json"

# Kocaeli koordinat sınırları — yanlış eşleşmeleri filtreler
KOCAELI_BOUNDS = {
    "lat_min": 40.45, "lat_max": 41.10,
    "lng_min": 29.50, "lng_max": 30.80,
}


class Geocoder:
    def __init__(self):
        self.db         = get_db()
        self.cache_col  = self.db["geocache"]

    def geocode(self, article: dict) -> dict:
        """
        article["location_text"] → article["location_coords"] {"lat": ..., "lng": ...}
        Başarısız olursa location_coords None kalır → bu haber haritada gösterilmez.
        """
        location_text = article.get("location_text")

        # Konum yoksa atla
        if not location_text:
            return article

        coords = self._get_coords(location_text)
        article["location_coords"] = coords   # None veya {"lat": ..., "lng": ...}
        return article

    def _get_coords(self, location_text: str) -> dict | None:
        """
        Önce MongoDB cache'e bakar.
        Cache'de yoksa Google API'yi çağırır, sonucu cache'e yazar.
        """
        # 1) Cache'e bak
        cached = self.cache_col.find_one({"query": location_text})
        if cached:
            return {"lat": cached["lat"], "lng": cached["lng"]}

        # 2) Google Geocoding API çağrısı
        coords = self._call_google_api(location_text)

        # 3) Başarılıysa cache'e yaz
        if coords:
            self.cache_col.insert_one({
                "query":     location_text,
                "lat":       coords["lat"],
                "lng":       coords["lng"],
                "cached_at": datetime.utcnow()
            })

        return coords

    def _call_google_api(self, location_text: str) -> dict | None:
        """
        Google Geocoding API'yi çağırır.
        Kocaeli sınırları dışında bir koordinat gelirse None döner.
        """
        if not GOOGLE_API_KEY:
            print("❌ GOOGLE_API_KEY bulunamadı. .env dosyasını kontrol et.")
            return None

        # "Yahya Kaptan, İzmit" → "Yahya Kaptan, İzmit, Kocaeli, Türkiye"
        query = f"{location_text}, Kocaeli, Türkiye"

        try:
            response = requests.get(
                GEOCODING_URL,
                params={"address": query, "key": GOOGLE_API_KEY, "language": "tr"},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "OK" or not data.get("results"):
                print(f"⚠️  Geocoding başarısız: '{query}' → {data.get('status')}")
                return None

            loc = data["results"][0]["geometry"]["location"]
            lat, lng = loc["lat"], loc["lng"]

            # Kocaeli sınırları dışındaysa reddet
            if not self._is_in_kocaeli(lat, lng):
                print(f"⚠️  Koordinat Kocaeli dışında: '{query}' → ({lat}, {lng})")
                return None

            return {"lat": lat, "lng": lng}

        except Exception as e:
            print(f"❌ Google API hatası ('{location_text}'): {e}")
            return None

    def _is_in_kocaeli(self, lat: float, lng: float) -> bool:
        """Koordinatın Kocaeli sınırları içinde olup olmadığını kontrol eder."""
        b = KOCAELI_BOUNDS
        return (b["lat_min"] <= lat <= b["lat_max"] and
                b["lng_min"] <= lng <= b["lng_max"])


def geocode_articles(articles: list[dict]) -> list[dict]:
    """
    Tüm article listesi için koordinat dönüşümü yapar.
    Başarısız olanlar haritada gösterilmez (location_coords=None).

    Kullanım:
        from pipeline.geocoder import geocode_articles
        articles = geocode_articles(articles)
    """
    geocoder = Geocoder()
    success  = 0
    skipped  = 0
    failed   = 0

    for article in articles:
        if not article.get("location_text"):
            skipped += 1
            continue

        geocoder.geocode(article)

        if article.get("location_coords"):
            success += 1
        else:
            failed += 1

    print(f"✅ Geocoder: {success} koordinat bulundu | "
          f"{failed} başarısız | {skipped} konum yok")
    return articles