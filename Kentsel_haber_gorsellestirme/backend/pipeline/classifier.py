import re

# ── 1. GENEL NEGATİF KELİMELER (Context Killers) ─────────────────────────── #
# Bu kelimeler geçiyorsa, haber muhtemelen siyaset, şikayet, açılış veya TV programıdır.
# Sıcak bir "olay/asayiş" haberi olma ihtimali çok düşüktür. Tüm kategoriler için skoru sıfırlar.
GLOBAL_NEGATIVE_KEYWORDS = [
    "değerlendirdi", "açılış", "proje", "tepki", "milletvekili", 
    "soru önergesi", "meclis", "tv'de", "konuk", "açıklama yaptı", 
    "basın toplantısı", "gündemine taşıdı", "röportaj", "eleştirdi",
    "önerge", "ziyaret etti", "faaliyete geçti"
]

# ── 2. KATEGORİ BAZLI NEGATİF KELİMELER ──────────────────────────────────── #
# Sadece o kategoriye özel yanlış anlaşılmaları engeller. (Örn: "yangın çıksa", "itfaiye giremez")
NEGATIVE_KEYWORDS = {
    "Yangın": [
        "tatbikat", "film", "sinema", "dizi", "roman", "şarkı", "klip", 
        "yangın çıksa", "olası bir yangın", "itfaiye giremez", "itfaiye aracı giremedi",
        "yangın merdiveni", "hidrant", "yangın tüpü", "yangın dolabı"
    ],
    "Trafik Kazası": ["tatbikat", "simülasyon", "film", "dizi", "oyun", "şaka", "kaza yapsa"],
    "Hırsızlık": ["film", "dizi", "senaryo", "oyun", "tiyatro", "şaka"],
    "Elektrik Kesintisi": ["planlı kesinti duyurusu", "ihale", "fatura", "ödeme", "abonelik"],
    "Kültürel Etkinlik": ["iptal edildi", "ertelendi", "tepki"]
}

# ── 3. ANAHTAR KELİMELER ─────────────────────────────────────────────────── #
KEYWORDS = {
    "Yangın": [
        "yangın", "alev aldı", "itfaiye", "ev yandı", "araç yandı", 
        "bina yandı", "fabrika yandı", "tutuştu", "duman çıktı", 
        "orman yangını", "kül oldu", "alevlere teslim", "söndürme çalışması"
    ],
    "Trafik Kazası": [
        "trafik kazası", "kaza yaptı", "zincirleme kaza", "araç devrildi", 
        "otobüs devrildi", "kamyon devrildi", "tır devrildi", "çarpışma", 
        "çarpıştı", "takla attı", "şarampole yuvarlandı", "kaza geçirdi",
        "maddi hasarlı kaza", "feci kaza"
    ],
    "Hırsızlık": [
        "hırsız", "çalındı", "soygun", "gasp", "araç çalındı", 
        "market soygunu", "dükkan soygunu", "evden çalındı", 
        "kapkaç", "kuyumcu soygunu", "çaldı"
    ],
    "Elektrik Kesintisi": [
        "elektrik kesintisi", "elektrik kesildi", "elektrik arızası", 
        "trafo arızası", "güç kesintisi", "elektrik verilemiyor", 
        "karanlıkta kaldı", "elektrikler gitti", "vedaş", "edaş", "ayedaş", "sedaş"
    ],
    "Kültürel Etkinlik": [
        "konser", "festival", "sergi açıldı", "tiyatro gösterisi", 
        "kültür festivali", "fuar açıldı", "şenlik", "müzik dinletisi", 
        "sanat etkinliği", "resital", "film festivali", "halk konseri",
        "imza günü", "söyleşi"
    ],
}

PRIORITY = ["Yangın", "Trafik Kazası", "Hırsızlık", "Elektrik Kesintisi", "Kültürel Etkinlik"]
MIN_SCORE = 2
COMPOUND_WORD_THRESHOLD = 1

def tr_lower(text: str) -> str:
    """Türkçe karakterleri koruyarak küçük harfe çevirir."""
    return text.replace("I", "ı").replace("İ", "i").lower()

def _is_compound(phrase: str) -> bool:
    return len(phrase.strip().split()) > COMPOUND_WORD_THRESHOLD

def _match(kw: str, text: str) -> bool:
    if _is_compound(kw):
        return kw in text
    # Sadece sol sınır koyuyoruz, kelime ek alabilir (yangın -> yangına)
    pattern = r'(?<![a-zçğışöü])' + re.escape(kw)
    return bool(re.search(pattern, text, re.IGNORECASE | re.UNICODE))

def _score(text_title: str, text_content: str, category: str, keywords: list[str]) -> int:
    score = 0
    combined_text = f"{text_title} {text_content}"
    
    # 1. Genel Negatif Kontrolü (Haberin türü siyaset/şikayet/açılış ise direkt ele)
    # Bunu sadece başlıkta veya ilk paragrafta aramak performansı ve doğruluğu artırır, 
    # ancak şimdilik tüm metinde kontrol ediyoruz.
    for global_neg in GLOBAL_NEGATIVE_KEYWORDS:
        if global_neg in combined_text:
            return 0
            
    # 2. Kategoriye Özel Negatif Kontrolü
    for neg_kw in NEGATIVE_KEYWORDS.get(category, []):
        if neg_kw in combined_text:
            return 0 

    # 3. Puanlama
    for kw in keywords:
        kw_lower = kw 
        bonus = 1 if _is_compound(kw) else 0
        
        if _match(kw_lower, text_title):
            score += 3 + bonus   # Başlık ağırlıklı
        elif _match(kw_lower, text_content):
            score += 1 + bonus   # İçerik
            
    return score

class Classifier:
    def classify(self, article: dict) -> dict:
        title = tr_lower(article.get("title", ""))
        content = tr_lower(article.get("content", ""))

        scores = {}
        for category, keywords in KEYWORDS.items():
            scores[category] = _score(title, content, category, keywords)

        matched = [cat for cat in PRIORITY if scores[cat] >= MIN_SCORE]

        if not matched:
            article["news_type"] = "Diğer"
        elif len(matched) == 1:
            article["news_type"] = matched[0]
        else:
            matched.sort(key=lambda c: (-scores[c], PRIORITY.index(c)))
            article["news_type"] = matched[0]

        return article

def classify_articles(articles: list[dict]) -> list[dict]:
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