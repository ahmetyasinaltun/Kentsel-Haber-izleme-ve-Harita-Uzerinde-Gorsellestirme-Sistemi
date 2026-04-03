# pipeline/normalizer.py — Metin Maskeleme ve Embedding Optimizasyonu

import re

def _normalize_general(text: str) -> str:
    """Tüm haber kategorileri için geçerli standartlaştırma"""
    text = text.lower()
    text = text.replace("'", " ").replace('"', " ").replace("’", " ")
    
    
    date_pattern = r'\b\d{1,2}\s+(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)(?:\s+\d{4})?\b'
    text = re.sub(date_pattern, 'tarihinde', text)
    text = re.sub(r'\b(?:ve\s+)?tarihlerinde\b', 'tarihinde', text)
    
    return text

def _normalize_theft(text: str) -> str:
    """Hırsızlık haberlerine özel gürültü temizleme ve maskeleme"""
    # Para birimi
    text = re.sub(r'\btl[\s\']*lik\b', 'lira', text)
    text = re.sub(r'\bliralık\b', 'lira', text)
    text = re.sub(r'\btl\b', 'lira', text)
    
    
    text = re.sub(r'[a-zçğıöşü]\.\s?[a-zçğıöşü]\.?', 'şüpheli', text)
    
    noise_patterns = [
        r"kocaeli\s*emniyet\s*müdürlüğü\s*asayiş\s*şube\s*müdürlüğü\s*hırsızlık\s*büro\s*amirliği\s*ekipleri",
        r"kocaeli\s*il\s*emniyet\s*müdürlüğü\s*ekipleri",
        r"il\s*emniyet\s*müdürlüğü\s*ekipleri",
        r"polis\s*ekiplerinin\s*operasyonuyla",
        r"teknik\s*ve\s*saha\s*çalışmaları\s*sonucu(nda)?",
        r"düzenlenen\s*operasyonla",
        r"teknik\s*takip\s*ve\s*saha\s*incelemeleri\s*sonucunda",
        r"yapılan\s*teknik\s*taki[a-z]*",
        r"yakalanarak\s*tutuklandı",
        r"tutuklanarak\s*cezaevine\s*gönderildi",
        r"adliyeye\s*sevk\s*edildi",
        r"gözaltına\s*alındı",
        r"ele\s*geçirildi",
        r"tespit\s*edildi",
        r"tespit\s*edilen",
        r"belirlenen",
        r"yakalandı",
        r"çalışma\s*başlattı",
        r"yapılan\s*inceleme(lerde)?",
        r"şüpheli(lerin)?",
        r"zanlı(ların)?",
        r"şahıs(ların)?",
        r"yaklaşık",
        r"toplam",
        r"değerinde(ki)?",
        r"olay(ları)?na\s*ilişkin",
        r"olay(ı)?yla\s*ilgili",
        r"gerçekleştirdiği\s*belirl[a-z]*",
        r"olduğu\s*tespit\s*edildi",
        r"çalındığı\s*belirlendi",
        r"adres(ler)?inde",
        r"gizli\s*adreste",
        r"vurgunu",
        r"meydana\s*gelen",
        r"gerçekleştirdikleri",
        r"suçta\s*kullanıldığı\s*değerlendirilen\s*malzemeler\s*(ile)?"
    ]
    
    for pattern in noise_patterns:
        text = re.sub(pattern, " ", text)
        
    return text

def _normalize_traffic(text: str) -> str:
    """Trafik Kazası haberlerine özel gürültü temizleme ve maskeleme"""
    # Araç Plakalarını Maskele -> "plakalı"
    text = re.sub(r'\b\d{2}\s+[a-zçğıöşü]{1,3}\s+\d{2,4}\b', 'plakalı', text)
    
    # Yaş Bildirimlerini Sil (Örn: (78), (73) )
    text = re.sub(r'\(\d{2,3}\)', '', text)
    
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
        
    return text

def _normalize_fire(text: str) -> str:
    """Yangın haberlerine özel gürültü temizleme ve maskeleme"""
    noise_patterns = [
        r"itfaiye\s*ekipleri(ni)?(nce)?(\s*sevk\s*edildi)?",
        r"söndürme\s*çalışmaları",
        r"kontrol\s*altına\s*alındı",
        r"soğutma\s*çalışmaları",
        r"kısa\s*sürede\s*büyüdü",
        r"alevlere\s*teslim\s*oldu",
        r"maddi\s*hasar\s*meydana\s*geldi",
        r"vatandaşların\s*ihbarı\s*üzerine",
        r"olay\s*yerine\s*gelen",
        r"kullanılamaz\s*hale\s*geldi",
        r"dumanları\s*gören"
    ]
    
    for pattern in noise_patterns:
        text = re.sub(pattern, " ", text)
        
    return text

def _normalize_power_outage(text: str) -> str:
    """Elektrik Kesintisi haberlerine özel gürültü temizleme ve maskeleme"""
    noise_patterns = [
        r"(sedaş|ayedaş|vedaş)\s*tarafından\s*yapılan\s*açıklamada",
        r"planlı\s*elektrik\s*kesintisi",
        r"şebeke\s*bakım\s*onarım\s*çalışmaları",
        r"elektrik\s*verilemeyecektir",
        r"yaşanacaktır",
        r"anlayışınız\s*için\s*teşekkür\s*ederiz",
        r"saatleri\s*arasında",
        r"kesinti\s*yapılacak"
    ]
    
    for pattern in noise_patterns:
        text = re.sub(pattern, " ", text)
        
    return text

def _normalize_cultural_event(text: str) -> str:
    """Kültürel Etkinlik haberlerine özel gürültü temizleme ve maskeleme"""
    noise_patterns = [
        r"büyükşehir\s*belediyesi(nin)?",
        r"kültür\s*ve\s*sosyal\s*işler\s*daire\s*başkanlığı",
        r"tarafından\s*düzenlenen",
        r"yoğun\s*ilgi\s*gördü",
        r"ücretsiz\s*olarak\s*sahnelenecek",
        r"biletler\s*satışa\s*çıktı",
        r"vatandaşlar\s*akın\s*etti",
        r"kapsamında\s*gerçekleştirilen",
        r"unutulmaz\s*bir\s*gece\s*yaşattı"
    ]
    
    for pattern in noise_patterns:
        text = re.sub(pattern, " ", text)
        
    return text


def generate_embedding_text(article: dict) -> str:
    """
    Deduplicator'ın Cosine Similarity modeli için maskelenmiş özel string üretir.
    Haberin veritabanına gidecek olan orijinal 'title' ve 'content' alanlarını BOZMAZ.
    """
    title = article.get("title", "")
    content = article.get("content", "")
    news_type = article.get("news_type", "")
    district = article.get("district", "")

    # 1. Genel Normalizasyon
    norm_title = _normalize_general(title)
    norm_content = _normalize_general(content)

    # 2. Kategori Bazlı Özel Maskeleme
    if news_type == "Hırsızlık":
        norm_content = _normalize_theft(norm_content)
    elif news_type == "Trafik Kazası":
        norm_content = _normalize_traffic(norm_content)
    elif news_type == "Yangın":
        norm_content = _normalize_fire(norm_content)
    elif news_type == "Elektrik Kesintisi":
        norm_content = _normalize_power_outage(norm_content)
    elif news_type == "Kültürel Etkinlikler" or news_type == "Kültürel Etkinlikler":
        norm_content = _normalize_cultural_event(norm_content)
    
    # 3. Gürültüler atıldıktan sonra fazla boşlukları toparla ve kırp
    norm_content = re.sub(r'\s+', ' ', norm_content).strip()
    content_truncated = norm_content[:350] 

    # 4. Model için Anchor (Çapa) Etiketlerini Ekle
    prefix = ""
    if news_type and news_type != "Diğer":
        prefix += f"[{news_type.lower()}] "
    if district:
        prefix += f"[{district.lower()}] "
        
    final_text = f"{prefix} {norm_title}. {content_truncated}".strip()
    return final_text