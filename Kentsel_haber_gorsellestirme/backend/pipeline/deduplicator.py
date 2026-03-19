# Embedding benzerlik kontrolü
# pipeline/deduplicator.py — Embedding tabanlı duplicate haber kontrolü
# Gerekli kurulum: pip install sentence-transformers

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from db.connection import get_db

# Türkçe metinlerde iyi çalışan çok dilli model (384 boyutlu vektör)
MODEL_NAME       = "paraphrase-multilingual-MiniLM-L12-v2"
SIMILARITY_THRESHOLD = 0.90   # %90 ve üzeri → aynı haber

# Model bir kez yüklenir, her çağrıda tekrar yüklenmez
_model = None

def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print("🔄 Embedding modeli yükleniyor (ilk seferinde biraz sürebilir)...")
        _model = SentenceTransformer(MODEL_NAME)
        print("✅ Model hazır")
    return _model


def _make_text(article: dict) -> str:
    """Başlık + içeriği birleştirip embedding için hazırlar."""
    title   = article.get("title", "")
    content = article.get("content", "")[:500]   # İlk 500 karakter yeterli
    return f"{title} {content}".strip()


class Deduplicator:
    def __init__(self):
        self.model = _get_model()
        self.db    = get_db()
        self.col   = self.db["news"]

    def deduplicate(self, articles: list[dict]) -> list[dict]:
        """
        Gelen article listesini işler:
          1. Önce link duplicate kontrolü (aynı URL → direkt atla)
          2. Sonra embedding benzerlik kontrolü (≥%90 → aynı haber)
             - Yeni haber ise: embedding hesapla, kaydet
             - Duplicate ise: mevcut haberin sources listesine ekle, haberi atla

        Dönen liste: MongoDB'ye kaydedilecek benzersiz haberler
        """
        unique    = []
        duplicate = 0
        link_dup  = 0

        # Yeni haberler için embedding'leri toplu hesapla (daha hızlı)
        texts = [_make_text(a) for a in articles]
        embeddings = self.model.encode(texts, show_progress_bar=False)

        for i, article in enumerate(articles):
            url = article["sources"][0]["url"]

            # ── 1) Link duplicate kontrolü ──────────────────────────────── #
            if self._url_exists(url):
                link_dup += 1
                continue

            # ── 2) Embedding benzerlik kontrolü ─────────────────────────── #
            article["embedding"] = embeddings[i].tolist()

            existing_match = self._find_similar(embeddings[i])

            if existing_match:
                # Aynı haber farklı kaynakta → sources listesine ekle
                self._add_source(existing_match["_id"], article["sources"][0])
                duplicate += 1
                continue

            # ── 3) Yeni haber → listeye ekle ────────────────────────────── #
            unique.append(article)

        print(f"✅ Deduplicator: {len(unique)} yeni | "
              f"{duplicate} embedding duplicate | {link_dup} link duplicate")
        return unique

    def _url_exists(self, url: str) -> bool:
        """Bu URL daha önce kaydedilmiş mi?"""
        return self.col.find_one({"sources.url": url}) is not None

    def _find_similar(self, embedding: np.ndarray) -> dict | None:
        """
        MongoDB'deki tüm haberlerin embedding'leriyle karşılaştırır.
        ≥ %90 benzerlik bulunan ilk eşleşmeyi döner.
        """
        # MongoDB'den mevcut embedding'leri çek
        existing = list(self.col.find(
            {"embedding": {"$exists": True, "$ne": None}},
            {"_id": 1, "embedding": 1}
        ))

        if not existing:
            return None

        existing_embeddings = np.array([e["embedding"] for e in existing])
        scores = cosine_similarity([embedding], existing_embeddings)[0]

        max_idx   = int(np.argmax(scores))
        max_score = float(scores[max_idx])

        if max_score >= SIMILARITY_THRESHOLD:
            return existing[max_idx]

        return None

    def _add_source(self, news_id, new_source: dict):
        """
        Duplicate haberin kaynağını mevcut haberin sources listesine ekler.
        Aynı URL zaten varsa tekrar eklenmez ($addToSet gibi davranır).
        """
        self.col.update_one(
            {"_id": news_id},
            {"$addToSet": {"sources": new_source}}
        )


def deduplicate_articles(articles: list[dict]) -> list[dict]:
    """
    Tüm pipeline çıktısı üzerinde duplicate kontrolü yapar.

    Kullanım:
        from pipeline.deduplicator import deduplicate_articles
        unique_articles = deduplicate_articles(articles)
    """
    deduplicator = Deduplicator()
    return deduplicator.deduplicate(articles)