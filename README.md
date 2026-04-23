<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white" />
  <img src="https://img.shields.io/badge/Google%20Maps-4285F4?style=for-the-badge&logo=googlemaps&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/NLP-Sentence%20Transformers-FF6F00?style=for-the-badge" />
</p>

<h1 align="center">🗺️ Kentsel Haber İzleme ve Harita Üzerinde Görselleştirme Sistemi</h1>

<p align="center">
  <strong>Kocaeli ili yerel haber kaynaklarını otomatik olarak tarayıp, NLP pipeline'ı ile işleyerek Google Maps haritası üzerinde interaktif olarak görselleştiren full-stack web uygulaması.</strong>
</p>

<p align="center">
  <a href="#-özellikler">Özellikler</a> •
  <a href="#%EF%B8%8F-mimari">Mimari</a> •
  <a href="#-teknolojiler">Teknolojiler</a> •
  <a href="#-kurulum">Kurulum</a> •
  <a href="#-kullanım">Kullanım</a> •
  <a href="#-api-referansı">API</a> •
  <a href="#-proje-yapısı">Yapı</a>
</p>

---

## 📋 Proje Hakkında

Bu sistem, Kocaeli ilindeki **5 farklı yerel haber kaynağını** paralel olarak tarar, toplanan haberleri çok aşamalı bir NLP pipeline'ından geçirerek **otomatik sınıflandırma**, **konum çıkarımı**, **geocoding** ve **embedding tabanlı mükerrer tespit** işlemlerini gerçekleştirir. İşlenen haberler, kullanıcıya **interaktif bir harita arayüzü** üzerinden sunulur.

### 🎯 Hedef

- Kentsel olayların (trafik kazası, yangın, hırsızlık, elektrik kesintisi, kültürel etkinlik) coğrafi dağılımını görselleştirmek. 
- Farklı haber kaynaklarından gelen aynı olaya ait haberleri otomatik olarak birleştirmek.
- Kullanıcıya filtrelenebilir, responsive ve modern bir arayüz sunmak.

---

## ✨ Özellikler

### 🕷️ Web Scraping
- **5 yerel haber sitesi** paralel olarak taranır (ThreadPoolExecutor)
- Cloudflare korumasını aşabilen `cloudscraper` entegrasyonu
- Akıllı retry mekanizması ve rate limiting
- Son 3 günlük haberlerin otomatik filtrelenmesi

### 🧠 NLP Pipeline
| Aşama | Modül | Açıklama |
|:------|:------|:---------|
| 1️⃣ **Temizleme** | `cleaner.py` | HTML tag'leri, reklam metinleri, URL'ler ve gereksiz karakterlerin temizlenmesi |
| 2️⃣ **Sınıflandırma** | `classifier.py` | Anahtar kelime + negatif kelime tabanlı skor sistemiyle 5 kategoriye sınıflandırma |
| 3️⃣ **Konum Çıkarımı** | `location_extractor.py` | Regex + bağlam kalıpları ile ilçe, mahalle ve sokak düzeyinde konum tespiti |
| 4️⃣ **Geocoding** | `geocoder.py` | Google Geocoding API ile koordinat dönüşümü + MongoDB cache |
| 5️⃣ **Normalizer** | `normalizer.py` | Kategori bazlı metin maskeleme ve embedding için optimize metin üretimi |
| 6️⃣ **Deduplikasyon** | `deduplicator.py` | Sentence-BERT embedding + cosine similarity ile mükerrer haber tespiti (%90 eşik) |

### 🗺️ İnteraktif Harita
- Google Maps API entegrasyonu (Dark/Light tema desteği)
- Kategoriye göre renkli emoji marker'lar
- MarkerClusterer ile yoğun bölgelerin gruplandırılması
- Cluster tıklamada haber listesi popup'ı
- Harita ↔ Sidebar senkronizasyonu

### 🎨 Modern Arayüz
- Dark/Light tema geçişi (localStorage ile kalıcı)
- Gerçek zamanlı scraping ilerleme paneli
- Haber türü, ilçe ve tarih aralığı filtreleri
- Responsive tasarım (mobil uyumlu)
- Toast bildirim sistemi

---

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ index.html│  │ map.js   │  │ filters.js / api.js  │  │
│  │ (UI/CSS) │  │ (Harita) │  │ (Filtreleme & API)   │  │
│  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘  │
│       └──────────────┼───────────────────┘              │
│                      │ HTTP (REST)                      │
└──────────────────────┼──────────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────────┐
│                  BACKEND (FastAPI)                       │
│                      │                                  │
│  ┌───────────────────▼───────────────────────────────┐  │
│  │              API Routes (routes.py)                │  │
│  │  POST /api/scrape  │  GET /api/news  │ Filters    │  │
│  └───────┬────────────┴────────┬────────────┬────────┘  │
│          │                     │            │           │
│  ┌───────▼─────────────┐  ┌───▼────┐  ┌────▼──────┐   │
│  │   SCRAPING LAYER    │  │   DB   │  │  CONFIG   │   │
│  │  ┌──────────────┐   │  │ Layer  │  │  (.env)   │   │
│  │  │ BaseScraper   │   │  └───┬────┘  └───────────┘   │
│  │  │ DaktiloScraper│   │      │                        │
│  │  │ YeniKocaeli   │   │      │                        │
│  │  └──────┬────────┘   │      │                        │
│  └─────────┼────────────┘      │                        │
│            │                   │                        │
│  ┌─────────▼──────────────────────────────────────────┐ │
│  │              NLP PIPELINE                          │ │
│  │  Cleaner → Classifier → LocationExtractor →        │ │
│  │  Geocoder → Normalizer → Deduplicator              │ │
│  └────────────────────────────┬───────────────────────┘ │
│                               │                         │
└───────────────────────────────┼─────────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │    MongoDB Atlas     │
                    │  ┌──────┐ ┌────────┐ │
                    │  │ news │ │geocache│ │
                    │  └──────┘ └────────┘ │
                    └──────────────────────┘
```

---

## 🛠️ Teknolojiler

### Backend
| Teknoloji | Kullanım Amacı |
|:----------|:---------------|
| **Python 3.11** | Ana programlama dili |
| **FastAPI** | REST API framework |
| **Uvicorn** | ASGI web sunucusu |
| **BeautifulSoup4** | HTML parsing (web scraping) |
| **cloudscraper** | Cloudflare bypass scraping |
| **Sentence-Transformers** | Multilingual embedding modeli (`paraphrase-multilingual-MiniLM-L12-v2`) |
| **scikit-learn** | Cosine similarity hesaplaması |
| **PyMongo** | MongoDB driver |
| **python-dotenv** | Ortam değişkenleri yönetimi |

### Frontend
| Teknoloji | Kullanım Amacı |
|:----------|:---------------|
| **Vanilla HTML/CSS/JS** | Tek sayfa uygulama (SPA) |
| **Google Maps JavaScript API** | İnteraktif harita |
| **Google Geocoding API** | Adres → Koordinat dönüşümü |
| **MarkerClusterer** | Marker kümeleme |
| **ES Modules** | JavaScript modül sistemi |

### Veritabanı & Altyapı
| Teknoloji | Kullanım Amacı |
|:----------|:---------------|
| **MongoDB Atlas** | Bulut veritabanı |
| **Docker & Docker Compose** | Konteynerizasyon |

---

## 🚀 Kurulum

### Ön Gereksinimler
- **Python 3.11+**
- **MongoDB** (Atlas veya lokal)
- **Google Maps API Key** (Maps JavaScript API + Geocoding API etkin)
- **Docker** (opsiyonel)

### 1. Repoyu Klonlayın

```bash
git clone https://github.com/ahmetyasinaltun/Kentsel-Haber-izleme-ve-Harita-Uzerinde-Gorsellestirme-Sistemi.git
cd Kentsel-Haber-izleme-ve-Harita-Uzerinde-Gorsellestirme-Sistemi/Kentsel_haber_gorsellestirme
```

### 2. Ortam Değişkenlerini Ayarlayın

`backend/` dizininde `.env` dosyası oluşturun:

```env
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
GOOGLE_GEOCODING_API_KEY=your_google_geocoding_api_key
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?appName=KentselHaberIzleme
MONGO_DB_NAME=kocaeli_haberler
```

### 3a. Manuel Kurulum

```bash
# Backend bağımlılıklarını yükleyin
cd backend
pip install -r requirements.txt

# spaCy Türkçe modelini indirin (opsiyonel)
# python -m spacy download xx_ent_wiki_sm

# Backend'i başlatın
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend için `frontend/index.html` dosyasını tarayıcıda açın veya bir HTTP sunucusu ile sunun:

```bash
cd ../frontend
python -m http.server 5500
```

### 3b. Docker ile Kurulum

```bash
docker-compose up --build
```

> Docker Compose, MongoDB + Backend servislerini otomatik olarak başlatır.

---

## 📖 Kullanım

1. **Backend'i başlatın** (`uvicorn` veya `docker-compose`)
2. **Frontend'i açın** (`http://localhost:5500` veya `index.html`)
3. Sayfa açıldığında otomatik olarak:
   - 5 haber sitesi paralel olarak taranır
   - NLP pipeline haberleri işler
   - Harita üzerinde marker'lar gösterilir
4. **Filtreleme seçenekleri:**
   - 📰 Haber Türü (Trafik Kazası, Yangın, Hırsızlık, Elektrik Kesintisi, Kültürel Etkinlikler)
   - 📍 İlçe (Kocaeli'nin 12 ilçesi)
   - 📅 Tarih Aralığı
5. **«Haberleri Yükle»** butonuyla yeni scraping tetikleyebilirsiniz
6. **«Sıfırla»** butonu veritabanını temizler

---

## 📡 API Referansı

Tüm endpoint'ler `/api` prefix'i altındadır. Backend varsayılan olarak `http://localhost:8000` üzerinde çalışır.

| Method | Endpoint | Açıklama |
|:-------|:---------|:---------|
| `GET` | `/` | Health check |
| `POST` | `/api/scrape` | Scraping pipeline'ını arka planda tetikler |
| `GET` | `/api/scrape/status` | Scraping durumunu sorgular |
| `GET` | `/api/news` | Haberleri getirir (filtreleme destekli) |
| `GET` | `/api/news/{id}` | Tek haber detayı |
| `DELETE` | `/api/news` | Tüm haberleri siler |
| `GET` | `/api/filter/options` | Filtre dropdown seçenekleri |
| `GET` | `/api/config/maps-key` | Google Maps API anahtarını döner |

### Filtre Parametreleri (`GET /api/news`)

| Parametre | Tip | Açıklama |
|:----------|:----|:---------|
| `news_type` | string | Haber türü filtresi |
| `district` | string | İlçe filtresi (regex destekli) |
| `start_date` | string | Başlangıç tarihi (`YYYY-MM-DD`) |
| `end_date` | string | Bitiş tarihi (`YYYY-MM-DD`) |

---

## 📂 Proje Yapısı

```
Kentsel_haber_gorsellestirme/
│
├── docker-compose.yml          # MongoDB + Backend orkestrasyon
├── .gitignore
│
├── backend/
│   ├── main.py                 # FastAPI uygulama giriş noktası
│   ├── config.py               # Ortam değişkenleri yönetimi
│   ├── requirements.txt        # Python bağımlılıkları
│   ├── .env                    # API anahtarları ve DB bağlantısı (git'e eklenmez)
│   │
│   ├── api/
│   │   ├── models.py           # Pydantic modelleri
│   │   └── routes.py           # API endpoint tanımları + scraping orkestrasyon
│   │
│   ├── db/
│   │   ├── connection.py       # MongoDB bağlantı yönetimi (singleton)
│   │   └── repository.py       # CRUD işlemleri (news + geocache)
│   │
│   ├── scraper/
│   │   ├── base_scraper.py     # Ortak scraper sınıfı (retry, rate-limit)
│   │   ├── daktilo_scraper.py  # 4 site: Çağdaş, Özgür, Ses, BizimYaka
│   │   └── yenikocaeli.py      # Yeni Kocaeli scraper (farklı DOM yapısı)
│   │
│   ├── pipeline/
│   │   ├── cleaner.py          # HTML temizleme, reklam/gürültü filtreleme
│   │   ├── classifier.py       # Anahtar kelime tabanlı 5-sınıf kategorizasyon
│   │   ├── location_extractor.py  # NER + regex ile konum çıkarımı
│   │   ├── geocoder.py         # Google Geocoding API + MongoDB cache
│   │   ├── normalizer.py       # Embedding için kategori bazlı metin maskeleme
│   │   └── deduplicator.py     # Sentence-BERT + cosine similarity deduplikasyon
│   │
│   ├── similarity_tester.py    # Embedding benzerlik test aracı
│   ├── site_tester.py          # Scraper çıktı test aracı
│   └── debug_fetch.py          # HTTP istek debug aracı
│
└── frontend/
    ├── index.html              # Tek sayfa uygulama (HTML + CSS + JS)
    ├── css/
    │   └── style.css           # Ek stil dosyası
    └── js/
        ├── api.js              # Backend API iletişim modülü
        ├── filters.js          # Filtre yönetimi ve state kontrolü
        └── map.js              # Google Maps entegrasyonu + marker yönetimi
```

---

## 🔍 Haber Kaynakları

| # | Site | URL | Scraper |
|:--|:-----|:----|:--------|
| 1 | Çağdaş Kocaeli | `cagdaskocaeli.com.tr` | DaktiloScraper |
| 2 | Özgür Kocaeli | `ozgurkocaeli.com.tr` | DaktiloScraper |
| 3 | Ses Kocaeli | `seskocaeli.com` | DaktiloScraper |
| 4 | Bizim Yaka | `bizimyaka.com` | DaktiloScraper |
| 5 | Yeni Kocaeli | `yenikocaeli.com` | YeniKocaeliScraper |

---

## 🏷️ Haber Kategorileri

| Kategori | Emoji | Renk | Örnek Anahtar Kelimeler |
|:---------|:-----:|:----:|:------------------------|
| **Trafik Kazası** | 💥 | 🔴 | trafik kazası, çarpıştı, takla attı, zincirleme kaza |
| **Yangın** | 🔥 | 🟠 | yangın çıktı, alev aldı, itfaiye, söndürme çalışması |
| **Hırsızlık** | 🦹 | 🟣 | hırsız, soygun, gasp, kapkaç, çalındı |
| **Elektrik Kesintisi** | ⚡ | 🟡 | elektrik kesintisi, trafo arızası, SEDAŞ |
| **Kültürel Etkinlikler** | 🎭 | 🔵 | konser, festival, sergi, tiyatro, şenlik |

---

## 🧪 Test Araçları

Proje, geliştirme sürecini destekleyen test scriptleri içerir:

- **`similarity_tester.py`** — Farklı kaynaklardan gelen aynı olaya ait haberlerin cosine similarity skorlarını hesaplar
- **`site_tester.py`** — Scraper + Cleaner çıktılarını görsel olarak test eder
- **`debug_fetch.py`** — HTTP istek ve DOM yapısı debug aracı

```bash
# Benzerlik testi çalıştır
cd backend
python similarity_tester.py
```

---

## ⚠️ Önemli Notlar

- `.env` dosyasını **asla** GitHub'a pushlamayın. `.gitignore` dosyasında hali hazırda tanımlıdır.
- Google Maps API Key'in **Maps JavaScript API** ve **Geocoding API** hizmetleri için aktif olması gerekir.
- Scraping işlemi arka planda çalışır ve ~1-3 dakika sürebilir.
- Embedding modeli (`paraphrase-multilingual-MiniLM-L12-v2`) ilk çalıştırmada indirilir (~420 MB).
- Geocoding sonuçları MongoDB'de `geocache` koleksiyonunda önbelleklenir, tekrar eden sorgular API kotasını tüketmez.

---

## 📄 Lisans

Bu proje akademik amaçla geliştirilmiştir.

---

<p align="center">
  <sub>Kocaeli Üniversitesi — Bilgisayar Mühendisliği Bölümü</sub>
</p>
