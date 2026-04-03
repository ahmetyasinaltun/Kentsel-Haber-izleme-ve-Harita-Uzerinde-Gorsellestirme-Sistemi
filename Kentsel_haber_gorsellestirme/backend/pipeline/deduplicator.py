# Embedding benzerlik kontrolü
# pipeline/deduplicator.py — Embedding tabanlı duplicate haber kontrolü


from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from db.connection import get_db

# Kategori bazlı maskeleme fonksiyonumuzu dahil ediyoruz
from pipeline.normalizer import generate_embedding_text


MODEL_NAME       = "paraphrase-multilingual-MiniLM-L12-v2"
SIMILARITY_THRESHOLD = 0.9   


_model = None

def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print("🔄 Embedding modeli yükleniyor (ilk seferinde biraz sürebilir)...")
        _model = SentenceTransformer(MODEL_NAME)
        print("✅ Model hazır")
    return _model

class Deduplicator:
    def __init__(self):
        self.model = _get_model()
        self.db    = get_db()
        self.col   = self.db["news"]

    def deduplicate(self, articles: list[dict]) -> list[dict]:
        """
        Gelen article listesini işler:
          1. Önce link duplicate kontrolü (aynı URL → direkt atla)
          2. Batch içi embedding benzerlik kontrolü (aynı turda gelen haberler)
          3. DB'deki mevcut haberlerle embedding benzerlik kontrolü
             - Duplicate ise: mevcut haberin sources listesine ekle, haberi atla

        Dönen liste: MongoDB'ye kaydedilecek benzersiz haberler
        """
        unique    = []
        duplicate = 0
        link_dup  = 0

       
        texts = [generate_embedding_text(a) for a in articles]
        embeddings = self.model.encode(texts, show_progress_bar=False)

        batch_accepted_embeddings = []  
        batch_accepted_articles   = []  

        for i, article in enumerate(articles):
            url = article["sources"][0]["url"]

            if self._url_exists(url):
                link_dup += 1
                continue

            emb = embeddings[i]
            article["embedding"] = emb.tolist()

            batch_match = None
            if batch_accepted_embeddings:
                batch_matrix = np.array(batch_accepted_embeddings)
                scores       = cosine_similarity([emb], batch_matrix)[0]
                max_idx      = int(np.argmax(scores))
                if float(scores[max_idx]) >= SIMILARITY_THRESHOLD:
                    batch_match = batch_accepted_articles[max_idx]

            if batch_match:
                existing_sources = [s["url"] for s in batch_match.get("sources", [])]
                if article["sources"][0]["url"] not in existing_sources:
                    batch_match.setdefault("sources", []).append(article["sources"][0])
                duplicate += 1
                continue

            db_match = self._find_similar(emb)
            if db_match:
                self._add_source(db_match["_id"], article["sources"][0])
                duplicate += 1
                continue

            unique.append(article)
            batch_accepted_embeddings.append(emb)
            batch_accepted_articles.append(article)

        print(f"✅ Deduplicator İşlemi Tamamlandı:")
        print(f"   ➕ {len(unique)} adet yepyeni haber oluşturuldu.")
        print(f"   🔗 {duplicate} adet haber, sistemdeki aynı olayın kaynaklarına eklendi.")
        print(f"   ⏭️  {link_dup} adet URL zaten veritabanında var olduğu için atlandı.")
        return unique

    def _url_exists(self, url: str) -> bool:
        return self.col.find_one({"sources.url": url}) is not None

    def _find_similar(self, embedding: np.ndarray) -> dict | None:
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
        self.col.update_one(
            {"_id": news_id},
            {"$addToSet": {"sources": new_source}}
        )

def deduplicate_articles(articles: list[dict]) -> list[dict]:
    deduplicator = Deduplicator()
    return deduplicator.deduplicate(articles)