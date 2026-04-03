import re

# ── 1. GENEL NEGATİF KELİMELER (Context Killers) ─────────────────────────── #


GLOBAL_NEGATIVE_KEYWORDS = [
    "soru önergesi", "tbmm", "gündemine taşıdı", "önerge",
    "basın toplantısı", "basın açıklaması", "siyasi parti", "parti binası",
    "aday adayı", "seçim çalışması", "il binası",
    "mahkeme", "duruşma",
    "yatırım", "proje", "altyapı", "üstyapı",
    "ihale", "açılış töreni", "temel atma",
    "tanıtım", "kampanya", "duyuru"
]


# ── 2. KATEGORİ BAZLI NEGATİF KELİMELER ── #

NEGATIVE_KEYWORDS = {

    "Yangın": [
        "tatbikat", "yangın tatbikatı",
        "film", "sinema", "dizi", "roman", "şarkı", "klip",
        "olası yangın", "yangın riski",
        "yangın merdiveni", "yangın tüpü", "yangın dolabı",
        "yangın eğitimi", "yangın güvenliği",
        "itfaiye eğitimi"
    ],

    "Trafik Kazası": [
        "tatbikat", "simülasyon",
        "film", "dizi", "oyun",
        "kaza yaparsa", "kaza riski",
        "yol çalışması", "bakım çalışması", "yenileme çalışması",
        "trafik eğitimi"
    ],

    "Hırsızlık": [
        "film", "dizi", "senaryo",
        "oyun", "tiyatro",
        "hırsızlık şakası", "hırsızlık filmi",
        "dolandırıcılık uyarısı"
    ],

    "Elektrik Kesintisi": [
        "fatura", "ödeme", "abonelik",
        "indirim", "kampanya",
        "fiyat artışı", "zam",
        "altyapı çalışması", "kazı çalışması",
        "elektrik direği dikildi"
    ],

    "Kültürel Etkinlikler": [
        "iptal edildi",
        "ertelendi",
        "bilet satış",
        "bilet fiyat",
        "tanıtım toplantısı"
    ]
}


# ── 3. ANAHTAR KELİMELER ── #

KEYWORDS = {

    "Yangın": [
        "yangın", "yangın çıktı",
        "alev aldı", "alevlere teslim",
        "ev yandı", "bina yandı", "araç yandı",
        "fabrika yandı", "depo yandı",
        "orman yangını",
        "duman yükseldi", "duman çıktı",
        "itfaiye sevk edildi",
        "söndürme çalışması",
        "kundaklama",
        "yangın paniği"
    ],

    "Trafik Kazası": [
        "trafik kazası",
        "kaza yaptı", "kaza meydana geldi",
        "zincirleme kaza", "zincirleme trafik kazası",
        "çarpıştı", "çarpışma",
        "araç devrildi",
        "otobüs devrildi", "kamyon devrildi", "tır devrildi",
        "takla attı",
        "şarampole yuvarlandı",
        "yayaya çarptı",
        "motosiklet kazası",
        "yoldan çıktı",
        "feci kaza",
        "kontrolden çıktı"
    ],

    "Hırsızlık": [
        "hırsız", "hırsızlık",
        "çalındı", "çaldı",
        "soygun", "gasp",
        "kapkaç",
        "evden hırsızlık",
        "iş yerinden hırsızlık",
        "market soygunu",
        "dükkan soygunu",
        "kuyumcu soygunu",
        "araç çalındı",
        "kablo hırsızlığı",
        "yankesicilik"
    ],

    "Elektrik Kesintisi": [
        "elektrik kesintisi",
        "elektrik kesildi",
        "elektrikler kesildi",
        "elektrikler gitti",
        "elektrik arızası",
        "trafo arızası",
        "güç kesintisi",
        "karanlıkta kaldı",
        "elektrik verilemiyor",
        "planlı kesinti",
        "sedaş", "ayedaş", "vedaş", "edaş", "sepaş"
    ],

    "Kültürel Etkinlikler": [
        "konser",
        "festival",
        "sergi",
        "tiyatro",
        "şenlik",
        "fuar",
        "müzik dinletisi",
        "resital",
        "film festivali",
        "halk konseri",
        "imza günü",
        "söyleşi",
        "koro",
        "sanat etkinliği",
        "kültürel etkinlik",
        "gösteri",
        "konferans"
    ]
}

PRIORITY = ["Yangın", "Trafik Kazası", "Hırsızlık", "Elektrik Kesintisi", "Kültürel Etkinlikler"]
MIN_SCORE = 2
COMPOUND_WORD_THRESHOLD = 1

def tr_lower(text: str) -> str:
    return text.replace("I", "ı").replace("İ", "i").lower()

def _is_compound(phrase: str) -> bool:
    return len(phrase.strip().split()) > COMPOUND_WORD_THRESHOLD

def _match(kw: str, text: str) -> bool:
    if _is_compound(kw):
        return kw in text
    pattern = r'(?<![a-zçğışöü])' + re.escape(kw)
    return bool(re.search(pattern, text, re.IGNORECASE | re.UNICODE))

def _score(text_title: str, text_content: str, category: str, keywords: list[str]) -> int:
    score = 0
    combined_text = f"{text_title} {text_content}"
    
    for global_neg in GLOBAL_NEGATIVE_KEYWORDS:
        if global_neg in combined_text:
            return 0
            
    for neg_kw in NEGATIVE_KEYWORDS.get(category, []):
        if neg_kw in combined_text:
            return 0 

    for kw in keywords:
        kw_lower = kw 
        bonus = 1 if _is_compound(kw) else 0
        
        if _match(kw_lower, text_title):
            score += 3 + bonus   
        elif _match(kw_lower, text_content):
            score += 1 + bonus   
            
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