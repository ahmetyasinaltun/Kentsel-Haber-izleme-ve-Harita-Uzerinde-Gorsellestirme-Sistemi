# Kentsel Haber İzleme ve Harita Üzerinde Görselleştirme Sistemi

Kocaeli yerel haber sitelerinden haber toplayan, sınıflandıran ve harita üzerinde görselleştiren sistem.

## Kurulum

```bash
cp .env.example .env
# .env dosyasını düzenleyerek API anahtarlarını girin
docker-compose up -d
```

## Çalıştırma

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
