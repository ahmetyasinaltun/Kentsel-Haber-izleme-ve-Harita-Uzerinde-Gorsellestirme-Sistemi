# Anahtar kelime sınıflandırma
# pipeline/classifier.py — Anahtar kelime tabanlı haber türü sınıflandırma

# ── Anahtar kelimeler (LaTeX raporunda da bu liste kullanılacak) ───────────── #
KEYWORDS = {
    "Yangın": [
        "yangın", "yangin", "alev", "itfaiye", "yandı", "yandi",
        "tutuştu", "tutusdu", "duman", "yangına", "yangina",
        "orman yangını", "orman yangini", "fabrika yangını", "fabrika yangini",
        "köy yangını", "ev yangını", "araç yandı", "yanan",
    ],
    "Trafik Kazası": [
        "kaza", "çarpışma", "carpısma", "trafik kazası", "trafik kazasi",
        "araç devrildi", "arac devrildi", "otobüs devrildi",
        "kamyon devrildi", "tır devrildi", "tir devrildi",
        "yaralı", "yarali", "ambulans", "refakat", "çarpıştı", "carpisti",
        "zincirleme", "takla", "trafik", "kaza yaptı",
    ],
    "Hırsızlık": [
        "hırsız", "hirsiz", "çalındı", "calindi", "soygun", "gasp",
        "araç çalındı", "arac calindi", "market soygunu",
        "dükkan soygunu", "hırsızlık", "hirsizlik",
        "yakalandı", "yakalandi", "gözaltı", "gozalti",
        "hırsız yakalandı", "evden çalındı",
    ],
    "Elektrik Kesintisi": [
        "elektrik", "kesinti", "arıza", "ariza", "karanlık", "karanlik",
        "VEDAŞ", "vedas", "enerji", "trafo", "bakım", "bakim",
        "güç kesintisi", "guc kesintisi", "elektrik kesildi",
        "elektrik arızası", "elektrik arizasi", "şebeke", "sebeke",
    ],
    "Kültürel Etkinlik": [
        "konser", "festival", "sergi", "etkinlik", "tiyatro",
        "müzik", "muzik", "kültür", "kultur", "fuar",
        "kutlama", "şenlik", "senlik", "gösteri", "gosteri",
        "performans", "sanat", "resital", "açılış", "acilis",
    ],
}

# Çakışma durumunda öncelik sırası (soldan sağa → yüksekten düşüğe)
PRIORITY = ["Yangın", "Trafik Kazası", "Hırsızlık", "Elektrik Kesintisi", "Kültürel Etkinlik"]


class Classifier:
    def classify(self, article: dict) -> dict:
        """
        article["news_type"] alanını doldurur.
        Eşleşme yoksa "Diğer" olarak işaretler.
        """
        # Başlık + içeriği birleştir, küçük harfe çevir
        text = (
            (article.get("title", "") + " " + article.get("content", ""))
            .lower()
        )

        # Her kategori için eşleşen anahtar kelime sayısını bul
        scores = {category: 0 for category in PRIORITY}

        for category, keywords in KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text:
                    scores[category] += 1

        # Puan almış kategorileri bul
        matched = [cat for cat in PRIORITY if scores[cat] > 0]

        if not matched:
            article["news_type"] = "Diğer"
        elif len(matched) == 1:
            article["news_type"] = matched[0]
        else:
            # Çakışma var → öncelik sırasına göre ilkini seç
            article["news_type"] = matched[0]  # PRIORITY sırası zaten korunuyor

        return article


def classify_articles(articles: list[dict]) -> list[dict]:
    """
    Temizlenmiş article listesini sınıflandırır.

    Kullanım:
        from pipeline.classifier import classify_articles
        classified = classify_articles(cleaned_articles)
    """
    classifier = Classifier()
    counts = {cat: 0 for cat in PRIORITY}
    counts["Diğer"] = 0

    for article in articles:
        classifier.classify(article)
        counts[article["news_type"]] = counts.get(article["news_type"], 0) + 1

    print(f"✅ Classifier: {len(articles)} haber sınıflandırıldı")
    for cat, count in counts.items():
        if count > 0:
            print(f"   {cat}: {count}")

    return articles