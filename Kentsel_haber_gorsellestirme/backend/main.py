# main.py — FastAPI uygulama giriş noktası
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
    print("✅ Backend hazır — scraping index.html açılışında başlayacak.")


app.include_router(router, prefix="/api")


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": "Kocaeli Haber Haritası API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)