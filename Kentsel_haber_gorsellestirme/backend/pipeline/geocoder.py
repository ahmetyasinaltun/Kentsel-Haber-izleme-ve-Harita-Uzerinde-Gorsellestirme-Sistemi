# pipeline/geocoder.py — Google Geocoding API + MongoDB cache

import os
import requests
from datetime import datetime
from db.connection import get_db

from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_GEOCODING_API_KEY")
GEOCODING_URL  = "https://maps.googleapis.com/maps/api/geocode/json"

# ─── Kocaeli ili gerçek sınırları ────────────────────────────────────────────
# Batı: Gebze/Darıca ~29.25   Doğu: Kandıra/Karamürsel ~30.80
# Kuzey: Karadeniz kıyısı ~41.10   Güney: Gölcük/Karamürsel ~40.45
#
# Eski hatalı değer → lng_min: 29.50  (Gebze, Darıca, Çayırova dışarıda kalıyordu)
# Doğru değer       → lng_min: 29.20
#
# İlçe referans koordinatları (kontrol için):
#   Gebze:   40.8025, 29.4313
#   Darıca:  40.7647, 29.3733
#   Çayırova: 40.8383, 29.3947
#   İzmit:   40.7654, 29.9408
#   Kandıra: 41.0742, 30.1537
#   Karamürsel: 40.6957, 29.6075
KOCAELI_BOUNDS = {
    "lat_min": 40.45,
    "lat_max": 41.15,
    "lng_min": 29.20,   # ← DÜZELTİLDİ (eski: 29.50)
    "lng_max": 30.85,
}


class Geocoder:
    def __init__(self):
        self.db        = get_db()
        self.cache_col = self.db["geocache"]

    def geocode(self, article: dict) -> dict:
        location_text = article.get("location_text")
        if not location_text:
            return article
        coords = self._get_coords(location_text)
        article["location_coords"] = coords
        return article

    def _get_coords(self, location_text: str) -> dict | None:
        # 1) Cache'e bak
        cached = self.cache_col.find_one({"query": location_text})
        if cached:
            return {"lat": cached["lat"], "lng": cached["lng"]}

        # 2) Google API
        coords = self._call_google_api(location_text)

        # 3) Cache'e yaz
        if coords:
            self.cache_col.insert_one({
                "query":     location_text,
                "lat":       coords["lat"],
                "lng":       coords["lng"],
                "cached_at": datetime.utcnow()
            })

        return coords

    def _call_google_api(self, location_text: str) -> dict | None:
        if not GOOGLE_API_KEY:
            print("❌ GOOGLE_API_KEY bulunamadı. .env dosyasını kontrol et.")
            return None

        query = f"{location_text}, Kocaeli, Türkiye"

        try:
            response = requests.get(
                GEOCODING_URL,
                params={
                    "address":  query,
                    "key":      GOOGLE_API_KEY,
                    "language": "tr",
                    # bounds parametresi ile Google'a Kocaeli bölgesini ipucu ver
                    # → belirsiz mahalle/sokak adlarında daha isabetli sonuç verir
                    "bounds": f"{KOCAELI_BOUNDS['lat_min']},{KOCAELI_BOUNDS['lng_min']}"
                            f"|{KOCAELI_BOUNDS['lat_max']},{KOCAELI_BOUNDS['lng_max']}",
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            status = data.get("status")
            if status != "OK":
                error_msg = data.get("error_message", "Ek hata mesajı yok.")
                print(f"⚠️  Google API Reddi: '{query}'")
                print(f"   DURUM: {status} | MESAJ: {error_msg}")
                print(f"   Key: {GOOGLE_API_KEY[:4]}...{GOOGLE_API_KEY[-4:]}")
                return None

            if not data.get("results"):
                return None

            loc = data["results"][0]["geometry"]["location"]
            lat, lng = loc["lat"], loc["lng"]

            if not self._is_in_kocaeli(lat, lng):
                print(f"⚠️  Koordinat Kocaeli dışında: '{query}' → ({lat}, {lng})")
                return None

            return {"lat": lat, "lng": lng}

        except Exception as e:
            print(f"❌ Google API hatası ('{location_text}'): {e}")
            return None

    def _is_in_kocaeli(self, lat: float, lng: float) -> bool:
        b = KOCAELI_BOUNDS
        return (b["lat_min"] <= lat <= b["lat_max"] and
                b["lng_min"] <= lng <= b["lng_max"])


def geocode_articles(articles: list[dict]) -> list[dict]:
    geocoder = Geocoder()
    success = skipped = failed = 0

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