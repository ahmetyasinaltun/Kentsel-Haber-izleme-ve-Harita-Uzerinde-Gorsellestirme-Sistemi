import os
import sys
import requests
import re
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Backend yolunu ekleyelim ki pipeline modüllerini import edebilelim
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.cleaner import Cleaner
from pipeline.classifier import Classifier
from pipeline.location_extractor import LocationExtractor

# Mükerrer link temizlendi, tam 6 benzersiz haber (4'ü Olay 1, 2'si Olay 2)
URLS = [
    # OLAY 1: Tır Dorsesi Altında Kalan Yaşlı Çift
    "https://www.seskocaeli.com/haber/27739779/tem-otoyolu-izmit-gecisinde-feci-kaza-2-olu",
    "https://www.bizimyaka.com/haber/27742559/temde-otomobil-devrilen-tir-dorsesinin-altinda-kaldi-kari-koca-hayatini-kaybetti",
    "https://www.cagdaskocaeli.com.tr/haber/27740757/tem-kocaeli-gecisindeki-kazada-kari-koca-hayatini-kaybetti",
    "https://www.ozgurkocaeli.com.tr/haber/27742171/yasli-cift-korkunc-kazada-can-verdi",
    # OLAY 2: Yola Dökülen Atıklar Yüzünden 7 Aracın Karıştığı Kaza
    "https://www.seskocaeli.com/haber/27746065/tem-otoyolunda-zincirleme-kaza",
    "https://www.cagdaskocaeli.com.tr/haber/27746199/tem-kocaeli-gecisi-savas-alanina-dondu-doktu-kacti-otoyolu-birbirine-katti"
]

def get_raw_article(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else ""
    
    paragraphs = soup.find_all('p')
    content = " ".join([p.get_text(strip=True) for p in paragraphs])
    
    return {"title": title, "content": content, "sources": [{"url": url}]}

def normalize_text(text: str) -> str:
    """
    Genel standartlaştırma (Tüm haber tipleri için ortak)
    """
    text = text.lower()
    text = text.replace("'", " ").replace('"', " ").replace("’", " ")
    
    # Tarihleri MASKELİYORUZ -> "tarihinde"
    date_pattern = r'\b\d{1,2}\s+(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)(?:\s+\d{4})?\b'
    text = re.sub(date_pattern, 'tarihinde', text)
    
    return re.sub(r'\s+', ' ', text).strip()

def normalize_traffic(text: str) -> str:
    """
    Sadece 'Trafik Kazası' kategorisine özel gazetecilik/polisaj klişelerini temizler.
    """
    # 1. Araç Plakalarını Maskele (Örn: 34 VE 5842 -> "plakalı")
    text = re.sub(r'\b\d{2}\s+[a-zçğıöşü]{1,3}\s+\d{2,4}\b', 'plakalı', text)
    
    # 2. Yaş Bildirimlerini Sil (Örn: (78), (73) )
    text = re.sub(r'\(\d{2,3}\)', '', text)
    
    # 3. Klişe Kurum ve Müdahale Cümlelerini Maskele/Sil
    noise_patterns = [
        r"itfaiye,\s*sağlık\s*ve\s*polis\s*ekipleri(ni)?(nce)?(\s*sevk\s*edildi)?",
        r"sağlık\s*ekipleri(nce)?(\s*yapılan\s*kontrolde)?",
        r"jandarma\s*ekipleri(nce)?",
        r"karayolları\s*ekipleri(nin)?(nce)?",
        r"meydana\s*geldi",
        r"edinilen\s*bilgiye\s*göre",
        r"ihbar\s*üzerine(\s*olay\s*yerine)?",
        r"çarpışmanın\s*şiddetiyle",
        r"olay\s*yerinden\s*uzaklaştı",
        r"hayatını\s*kaybettiği\s*belirlendi",
        r"otopsi\s*işlemleri\s*için\s*morga\s*kaldırıldı",
        r"kaza\s*nedeniyle",
        r"kilometrelerce\s*araç\s*kuyruğu\s*oluştu",
        r"trafik\s*akışı\s*kontrollü\s*olarak\s*(sağlanıyor|sağlanmaya\s*başladı)",
        r"ulaşıma\s*kapan(dı|ırken)",
        r"çevredekilerin\s*ihbarı\s*üzerine",
        r"seyir\s*halinde(yken|ki)?(\s*olan)?",
        r"ilk\s*belirlemelere\s*göre",
        r"savaş\s*alanına\s*döndü"
    ]
    
    for pattern in noise_patterns:
        text = re.sub(pattern, " ", text)
    
    return re.sub(r'\s+', ' ', text).strip()

def run_test():
    cleaner = Cleaner()
    classifier = Classifier()
    extractor = LocationExtractor()
    
    print("🔄 Model Yükleniyor (paraphrase-multilingual-MiniLM-L12-v2)...")
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    
    texts_for_embedding = []
    
    for i, url in enumerate(URLS, 1):
        site_name = url.split('/')[2]
        print(f"\n{'='*70}")
        print(f"🔍 HABER {i} | KAYNAK: {site_name}")
        
        raw_article = get_raw_article(url)
        cleaned = cleaner.clean(raw_article)
        classified = classifier.classify(cleaned)
        extracted = extractor.extract(classified)
        
        news_type = extracted.get("news_type", "")
        district = extracted.get("district", "")
        title = normalize_text(extracted.get("title", ""))
        content = extracted.get("content", "")
        
        # Filtreleme (Bu sefer Trafik Kazası için devrede)
        if news_type == "Trafik Kazası":
            content = content.lower()
            content = normalize_traffic(content)
            content = normalize_text(content)
        
        content_truncated = content[:350] 
        
        prefix = ""
        if news_type and news_type != "Diğer":
            prefix += f"[{news_type.lower()}] "
        if district:
            prefix += f"[{district.lower()}] "
            
        final_text = f"{prefix} {title}. {content_truncated}".strip()
        texts_for_embedding.append(final_text)
        
        print(f"📌 Etiketler   : Kategori={news_type} | İlçe={district}")
        print(f"📝 Vektör Metni: \n\"{final_text}\"\n")
        
    print(f"\n{'='*70}")
    print("🧮 ÇAPRAZ BENZERLİK SKORLARI (Kosinüs Benzerliği)")
    print(f"{'='*70}")
    
    embeddings = model.encode(texts_for_embedding)
    matrix = cosine_similarity(embeddings)
    
    print(">>> OLAY 1 KENDİ İÇİNDE (Haber 1, 2, 3, 4) - BEKLENEN: %90+ <<<")
    for i in range(4):
        for j in range(i+1, 4):
            print(f"Haber {i+1} <---> Haber {j+1} Benzerliği : % {matrix[i][j]*100:.2f}")

    print("\n>>> OLAY 2 KENDİ İÇİNDE (Haber 5, 6) - BEKLENEN: %90+ <<<")
    print(f"Haber 5 <---> Haber 6 Benzerliği : % {matrix[4][5]*100:.2f}")
    
    print("\n>>> FARKLI OLAYLAR ARASI ÇAPRAZ KONTROL - BEKLENEN: Düşük Skor <<<")
    for i in range(4):
        for j in range(4, 6):
            print(f"Haber {i+1} (Olay 1) <---> Haber {j+1} (Olay 2) Benzerliği : % {matrix[i][j]*100:.2f}")

if __name__ == "__main__":
    run_test()