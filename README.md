# -Kentsel-Haber-izleme-ve-Harita-Uzerinde-Gorsellestirme-Sistemi
# Kocaeli Haber Haritası

Web scraping tabanlı kentsel haber izleme ve Google Maps üzerinde görselleştirme sistemi.  
Kocaeli Üniversitesi — Bilgisayar Mühendisliği — Yazılım Laboratuvarı II — Proje I

---

## Özellikler

- 5 yerel Kocaeli haber sitesinden otomatik scraping
- Haber türü sınıflandırması (Trafik Kazası, Yangın, Elektrik Kesintisi, Hırsızlık, Kültürel Etkinlik)
- Embedding tabanlı duplicate kontrolü (≥ %90 benzerlik → aynı haber)
- NLP/regex ile konum çıkarımı ve Google Geocoding API entegrasyonu
- Google Maps üzerinde kategoriye göre renkli marker görselleştirmesi
- Haber türü / ilçe / tarih filtresi (sayfa yenilenmeden dinamik)
- MongoDB veri depolama

---

## Gereksinimler

- Python 3.11+
- Docker & Docker Compose (önerilen)
- Google Cloud hesabı (Maps JS API + Geocoding API key)

---

## Kurulum

### 1. Repoyu klonla

```bash
git clone https://github.com/KULLANICI_ADI/kocaeli-haber-harita.git
cd kocaeli-haber-harita
```

### 2. Ortam değişkenlerini ayarla

```bash
cp .env.example .env
```

`.env` dosyasını aç ve API anahtarlarını gir:

```
GOOGLE_MAPS_API_KEY=AIza...
GOOGLE_GEOCODING_API_KEY=AIza...
```

### 3a. Docker ile çalıştır (önerilen)

```bash
docker compose up --build
```

MongoDB ve backend otomatik olarak ayağa kalkar.

### 3b. Manuel kurulum

```bash
# MongoDB'nin yerel olarak çalıştığından emin ol (port 27017)

cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

---

## Kullanım

1. Tarayıcıda `frontend/index.html` dosyasını aç  
   (ya da backend'den statik dosya servisi yapılıyorsa `http://localhost:8000`)
2. **"Haberleri Güncelle"** butonuna tıklayarak scraping başlat
3. Sol paneldeki filtrelerle haber türü / ilçe / tarih seç
4. Haritadaki marker'lara tıklayarak haber detayına ulaş

---

## Proje Yapısı

```
kocaeli-haber-harita/
├── backend/
│   ├── api/
│   │   ├── routes.py          # /news /scrape /filter/options endpoint'leri
│   │   └── models.py          # Pydantic şemaları
│   ├── scraper/
│   │   ├── base_scraper.py
│   │   ├── cagdaskocaeli.py
│   │   ├── ozgurkocaeli.py
│   │   ├── seskocaeli.py
│   │   ├── yenikocaeli.py
│   │   └── bizimyaka.py
│   ├── pipeline/
│   │   ├── cleaner.py
│   │   ├── classifier.py
│   │   ├── location_extractor.py
│   │   ├── geocoder.py
│   │   └── deduplicator.py
│   ├── db/
│   │   ├── connection.py
│   │   └── repository.py
│   ├── main.py
│   ├── config.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   └── js/
│       ├── api.js
│       ├── filters.js
│       └── map.js
├── report/
│   ├── main.tex
│   ├── sections/
│   │   ├── introduction.tex
│   │   ├── methodology.tex
│   │   ├── results.tex
│   │   └── conclusion.tex
│   ├── figures/
│   └── main.pdf
├── .env                  # Git'e ekleme!
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

---

## API Endpoint'leri

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/news` | Haberleri listele (filtre parametreli) |
| GET | `/api/news/{id}` | Tek haber detayı |
| POST | `/api/scrape` | Scraping başlat |
| GET | `/api/filter/options` | Filtre seçeneklerini getir |
| GET | `/api/config/maps-key` | Maps API anahtarını güvenli sun |

---

## .gitignore

`.env` dosyasının git'e gitmediğinden emin ol:

```
.env
__pycache__/
*.pyc
.venv/
mongo_data/
report/main.pdf
```

---

## Lisans

Kocaeli Üniversitesi — Yazılım Laboratuvarı II — 2025–2026 Bahar Dönemi