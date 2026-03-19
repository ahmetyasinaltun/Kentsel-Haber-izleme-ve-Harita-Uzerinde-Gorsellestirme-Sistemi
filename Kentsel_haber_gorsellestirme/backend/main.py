# main.py  — FastAPI uygulama giriş noktası
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.connection import test_connection
from api.routes import router

# ── UYGULAMA ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Kocaeli Haber Haritası API",
    description="Web scraping tabanlı Kocaeli yerel haber izleme sistemi",
    version="1.0.0",
)

# ── CORS — Frontend (HTML/JS) farklı port'tan istek atabilsin ────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Production'da frontend URL'si ile sınırla
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── BAŞLANGIÇTA MongoDB BAĞLANTISINI TEST ET ──────────────────────────────────
@app.on_event("startup")
def on_startup():
    test_connection()

# ── ROUTER ───────────────────────────────────────────────────────────────────
app.include_router(router, prefix="/api")

# ── SAĞLIK KONTROLÜ ──────────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": "Kocaeli Haber Haritası API"}


# ── ÇALIŞTIRMA ───────────────────────────────────────────────────────────────
# Terminal:  uvicorn main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)