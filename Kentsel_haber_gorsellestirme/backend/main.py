# main.py — FastAPI uygulama giriş noktası
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.connection import test_connection
from api.routes import router

app = FastAPI(
    title="Kocaeli Haber Haritası API",
    description="Web scraping tabanlı Kocaeli yerel haber izleme sistemi",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    test_connection()

    # DB'de son 3 günde haber var mı kontrol et
    # Varsa scraping yapmadan devam et (--reload ile gereksiz tetiklenmeyi önler)
    from datetime import datetime, timedelta
    from db.connection import news_collection

    try:
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        recent_count = news_collection().count_documents(
            {"scraped_at": {"$gte": three_days_ago}}
        )
    except Exception:
        recent_count = 0

    if recent_count > 0:
        print(f"ℹ️  DB'de {recent_count} güncel haber mevcut — otomatik scraping atlandı.")
        print("    Manuel scraping için arayüzdeki 'Haberleri Güncelle' butonunu kullanın.")
    else:
        print("🔄 DB'de güncel haber bulunamadı — otomatik scraping başlatılıyor...")
        from api.routes import run_scraping_pipeline
        # Startup'ı bloklamadan arka planda başlat
        thread = threading.Thread(target=run_scraping_pipeline, daemon=True)
        thread.start()


app.include_router(router, prefix="/api")


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": "Kocaeli Haber Haritası API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)