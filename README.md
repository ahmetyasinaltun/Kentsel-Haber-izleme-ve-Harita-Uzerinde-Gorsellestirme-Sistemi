# Kentsel Haber İzleme ve Harita Üzerinde Görselleştirme Sistemi

Bu proje, Kocaeli odaklı yerel haberleri otomatik olarak toplayıp işleyerek harita üzerinde görselleştiren bir sistemdir.

## Özellikler

- Çoklu haber kaynağından paralel scraping
- Haberlerin kategoriye göre sınıflandırılması
- Metinden konum/ilçe çıkarımı
- Google Geocoding API ile koordinat üretimi
- MongoDB üzerinde haber ve geocode cache yönetimi
- Filtrelenebilir harita arayüzü (haber türü, ilçe, tarih aralığı)

## Mimari

Proje iki ana parçadan oluşur:

- **Backend (FastAPI + MongoDB):**
  - Scraping işlemini tetikler
  - NLP/pipeline adımlarını çalıştırır
  - API endpoint’leri üzerinden haberleri sunar
- **Frontend (HTML/CSS/JS + Google Maps):**
  - Haberleri harita ve liste olarak gösterir
  - Filtreleme ve tema yönetimi sağlar

## Dizin Yapısı

```text
Kentsel_haber_gorsellestirme/
├── backend/
│   ├── api/
│   ├── db/
│   ├── pipeline/
│   ├── scraper/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── js/
│   └── index.html
└── docker-compose.yml
```

## Gereksinimler

- Python 3.11+
- MongoDB
- Google Maps API Key
- Google Geocoding API Key

## Ortam Değişkenleri (.env)

`Kentsel_haber_gorsellestirme` klasöründe `.env` dosyası oluşturun:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=kocaeli_haberler
GOOGLE_MAPS_API_KEY=your_maps_api_key
GOOGLE_GEOCODING_API_KEY=your_geocoding_api_key
```

## Kurulum ve Çalıştırma (Lokal)

### 1) Backend

```bash
cd Kentsel_haber_gorsellestirme/backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend varsayılan olarak: `http://localhost:8000`

### 2) Frontend

Basit bir statik sunucu ile `frontend` klasörünü çalıştırın (örnek):

```bash
cd Kentsel_haber_gorsellestirme/frontend
python -m http.server 5500
```

Ardından tarayıcıdan açın: `http://localhost:5500`

## API Özet

Temel endpoint’ler (`/api` prefix’i ile):

- `POST /scrape` → scraping işlemini arka planda başlatır
- `GET /scrape/status` → scraping durumunu döner
- `GET /news` → haberleri filtrelerle listeler
- `DELETE /news` → tüm haberleri siler
- `GET /news/{news_id}` → tek haber döner
- `GET /filter/options` → filtre seçeneklerini döner
- `GET /config/maps-key` → frontend için Maps API key döner

## Veri Akışı

1. Kaynak sitelerden haberler toplanır
2. Metinler temizlenir ve sınıflandırılır
3. Konum/ilçe çıkarımı yapılır
4. Geocoding ile koordinatlar üretilir
5. Tekrarlı kayıtlar ayıklanır
6. Sonuçlar MongoDB’ye kaydedilir
7. Frontend filtreleyip harita üzerinde gösterir

## Notlar

- Geocoding başarısı için API anahtarlarının geçerli olması gerekir.
- Konum bulunamayan haberler haritada gösterilmez.
- `GET /news` tarih filtrelerinde format: `YYYY-MM-DD`.
