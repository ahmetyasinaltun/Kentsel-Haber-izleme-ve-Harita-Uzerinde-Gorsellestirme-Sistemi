# NER / regex konum çıkarımı
# pipeline/location_extractor.py — Haber metninden konum çıkarımı (NER + regex)

import re

# ── Kocaeli ilçeleri ──────────────────────────────────────────────────────── #
DISTRICTS = [
    "İzmit", "Izmit", "Gebze", "Körfez", "Korfez", "Darıca", "Darica",
    "Çayırova", "Cayirova", "Dilovası", "Dilovasi", "Gölcük", "Golcuk",
    "Kandıra", "Kandira", "Karamürsel", "Karamursel", "Kartepe", "Derince",
    "Başiskele", "Basiskele", "İzmit Merkez",
]

# ── Mahalle → İlçe eşleştirme tablosu (tek kaynak) ───────────────────────── #
# Hem NEIGHBORHOODS listesi hem de _guess_district buradan türetilir.
LOCATION_MAPPING = {
    # İZMİT
    "Yahya Kaptan": "İzmit", "Yahyakaptan": "İzmit", "Kuruçeşme": "İzmit",
    "Kurucesme": "İzmit", "Kozluk": "İzmit", "Yenidoğan": "İzmit", "Yenidogan": "İzmit",
    "Bekirdere": "İzmit", "Çukurbağ": "İzmit", "Cukurbag": "İzmit", "Orhan": "İzmit",
    "Serdar": "İzmit", "Durhasan": "İzmit", "Turgut": "İzmit", "Hacıhasan": "İzmit",
    "Gündoğdu": "İzmit", "Gundogdu": "İzmit", "Nişantepe": "İzmit", "Nisantepe": "İzmit",
    "Tavşantepe": "İzmit", "Tavsantepe": "İzmit", "Ömerağa": "İzmit", "Omeraga": "İzmit",
    "Alemdar": "İzmit", "Arızlı": "İzmit", "Arizli": "İzmit", "Cedit": "İzmit",
    "Doğan": "İzmit", "Erenler": "İzmit", "Gültepe": "İzmit", "Yenişehir": "İzmit",
    "Yeşilova": "İzmit", "Alikahya": "İzmit", "Akmeşe": "İzmit", "Tepeköy": "İzmit",
    "Topçular": "İzmit", "Tüysüzler": "İzmit", "Şirintepe": "İzmit", "Zabıtan": "İzmit",
    "Kadıköy": "İzmit", "Karabaş": "İzmit", "Sanayi": "İzmit", "Sekapark": "İzmit",
    "Akçaray": "İzmit", "Bağçeşme": "İzmit", "Fethiye": "İzmit",
    # GEBZE
    "Arapçeşme": "Gebze", "Osman Yılmaz": "Gebze", "Köşklüçeşme": "Gebze",
    "Köşklü Çeşme": "Gebze", "Gaziler": "Gebze", "Güzeller": "Gebze", "Guzeller": "Gebze",
    "Mustafapaşa": "Gebze", "Mevlana": "Gebze", "Yenikent": "Gebze", "Tatlıkuyu": "Gebze",
    "İstasyon": "Gebze", "Barış": "Gebze", "Mimar Sinan": "Gebze", "Ulus": "Gebze",
    "Adem Yavuz": "Gebze", "Beylikbağı": "Gebze", "Sultan Orhan": "Gebze", "Hürriyet": "Gebze",
    "Yavuz Selim": "Gebze", "Hacıhalil": "Gebze", "Kirazpınar": "Gebze",
    "Cumaköy": "Gebze", "Balçık": "Gebze", "Balcik": "Gebze", "Pelitli": "Gebze",
    "Tavşanlı": "Gebze", "Tavsanli": "Gebze", "Muallimköy": "Gebze", "Ovacık": "Gebze",
    # ÇAYIROVA
    "Şekerpınar": "Çayırova", "Sekerpinar": "Çayırova", "Akse": "Çayırova",
    "Özgürlük": "Çayırova", "Ozgurluk": "Çayırova", "Emek": "Çayırova",
    "İnönü": "Çayırova", "Inonu": "Çayırova", "Yeni Mahalle": "Çayırova",
    "Yenimahalle": "Çayırova",
    # DARICA
    "Bayramoğlu": "Darıca", "Bayramoglu": "Darıca", "Bağlarbaşı": "Darıca",
    "Baglarbasi": "Darıca", "Nenehatun": "Darıca", "Osmangazi": "Darıca",
    "Sırasöğütler": "Darıca", "Sirasogutler": "Darıca", "Abdi İpekçi": "Darıca",
    "Fevziçakmak": "Darıca", "Kazımkarabekir": "Darıca", "Piri Reis": "Darıca",
    "Yalı": "Darıca",
    # DİLOVASI
    "Diliskelesi": "Dilovası", "Tavşancıl": "Dilovası", "Tavsancil": "Dilovası",
    "Çerkeşli": "Dilovası", "Cerkesli": "Dilovası", "Demirciler": "Dilovası",
    "Köseler": "Dilovası", "Kayapınar": "Dilovası", "Orhangazi": "Dilovası",
    # BAŞİSKELE
    "Kullar": "Başiskele", "Yeniköy": "Başiskele", "Yenikoy": "Başiskele",
    "Karşıyaka": "Başiskele", "Yuvacık": "Başiskele", "Döngel": "Başiskele",
    "Seymen": "Başiskele", "Bahçecik": "Başiskele", "Barbaros": "Başiskele",
    "Kılıçarslan": "Başiskele", "Yeşilyurt": "Başiskele",
    # GÖLCÜK
    "Değirmendere": "Gölcük", "Halıdere": "Gölcük", "Ulaşlı": "Gölcük",
    "Şirinköy": "Gölcük", "Çiftlik": "Gölcük", "Hisareyn": "Gölcük",
    "Nüzhetiye": "Gölcük", "Nuzhetiye": "Gölcük", "İhsaniye": "Gölcük",
    "Yazlık": "Gölcük", "Kavaklı": "Gölcük", "Piyalepaşa": "Gölcük",
    "Saraylı": "Gölcük", "Örcün": "Gölcük", "Denizçalı": "Gölcük",
    "Denizcali": "Gölcük", "Donanma": "Gölcük",
    # KARTEPE
    "Köseköy": "Kartepe", "Kosekoy": "Kartepe", "Ataevler": "Kartepe",
    "Suadiye": "Kartepe", "Maşukiye": "Kartepe", "Derbent": "Kartepe",
    "Arslanbey": "Kartepe", "Uzunçiftlik": "Kartepe", "Uzuntarla": "Kartepe",
    "Sarımeşe": "Kartepe", "Acısu": "Kartepe", "Eşme": "Kartepe",
    # KÖRFEZ
    "Çamlıtepe": "Körfez", "Yeniyalı": "Körfez", "Hereke": "Körfez",
    "Kaletaşı": "Körfez", "Yarımca": "Körfez", "Tütünçiftlik": "Körfez",
    "Körfez Kent": "Körfez", "Kuzey Mahallesi": "Körfez", "Güney Mahallesi": "Körfez",
    "Mimar Sinan Mahallesi": "Körfez",
    # DERİNCE
    "Çenedağ": "Derince", "Sırrıpaşa": "Derince", "Çınarlı": "Derince",
    "İbni Sina": "Derince", "Yavuz Sultan": "Derince", "Dumlupınar": "Derince",
    # KARAMÜRSEL
    "Ereğli": "Karamürsel", "Eregli": "Karamürsel", "4 Temmuz": "Karamürsel",
    "Kayacık": "Karamürsel", "Dereköy": "Karamürsel",
    # ORTAK İSİMLER
    "Fatih": "Gebze",
    "Cumhuriyet": "İzmit",
    "Atatürk": "Çayırova",
}

# NEIGHBORHOODS: LOCATION_MAPPING'den otomatik türetilir — ayrıca bakım gerekmez
NEIGHBORHOODS = list(LOCATION_MAPPING.keys())

# ── Sokak / cadde / bulvar / meydan regex kalıpları ──────────────────────── #
STREET_PATTERN = re.compile(
    r"([A-ZÇĞİÖŞÜa-zçğışöşü\s]{3,40}?\s+(?:Sokak|Sokağı|Caddesi|Bulvarı|Mahallesi|Meydan|Meydanı|Kavşağı|Yolu|Köyü))",
    re.UNICODE
)

# ── "X ilçesinde", "X mahallesinde" gibi kalıplar ────────────────────────── #
CONTEXT_PATTERN = re.compile(
    r"(\b[A-ZÇĞİÖŞÜ][a-zçğışöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğışöşü]+)?)"
    r"\s+(?:ilçesinde|mahallesinde|semtinde|köyünde|caddesinde|sokağında|mevkiinde|yakınında)",
    re.UNICODE
)


class LocationExtractor:
    def _find_location(self, text: str, title: str = ""):
        """
        Öncelik sırası:
          1. Bağlam kalıpları (Örn: "Başiskele ilçesinde" -> En kesin sonuç)
          2. Başlıkta geçen ilçe adı (Başlıklar genelde olayın yerini vurgular)
          3. Mahalle / semt eşleşmesi
          4. Metin içinde geçen rastgele ilçe adı
        """
        found_location = None
        found_district = None

        # 1) Bağlam Kalıpları ("Başiskele ilçesinde") - En güvenilir!
        match = CONTEXT_PATTERN.search(text)
        if match:
            found_location = match.group(1).strip()
            # Eğer bulunan konum bir ilçe ise doğrudan ata
            for d in DISTRICTS:
                if d.lower() in found_location.lower():
                    found_district = d
                    break

        # 2) Başlıkta İlçe Kontrolü (Haber gövdesindeki İzmit'e aldanmamak için)
        if not found_district and title:
            for district in DISTRICTS:
                if re.search(r'\b' + re.escape(district) + r'\b', title, re.IGNORECASE):
                    found_district = district
                    break

        # 3) Mahalle adı ara (LOCATION_MAPPING üzerinden)
        if not found_district:
            for neighborhood, district in LOCATION_MAPPING.items():
                if re.search(r'\b' + re.escape(neighborhood) + r'\b', text, re.IGNORECASE):
                    found_location = neighborhood
                    found_district = district
                    break

        # 4) Sadece İlçe adı ara (Gövdede)
        if not found_district:
            for district in DISTRICTS:
                if re.search(r'\b' + re.escape(district) + r'\b', text, re.IGNORECASE):
                    found_district = district
                    break

        # Sokak/Cadde regex'i (Mahalle bulunamadıysa)
        if not found_location:
            match = STREET_PATTERN.search(text)
            if match:
                found_location = match.group(1).strip()

        # Formatlama
        if found_location and found_district:
            if found_district.lower() not in found_location.lower():
                found_location = f"{found_location}, {found_district}"

        if not found_location and found_district:
            found_location = found_district

        return found_location, found_district

    def extract(self, article: dict) -> dict:
        title = article.get("title", "")
        content = article.get("content", "")
        text = title + " " + content
        
        # Fonksiyona başlığı da parametre olarak gönderiyoruz
        location_text, district = self._find_location(text, title)
        
        article["location_text"] = location_text
        article["district"]      = district
        return article


def extract_locations(articles: list[dict]) -> list[dict]:
    extractor = LocationExtractor()
    found = 0
    for article in articles:
        extractor.extract(article)
        if article.get("location_text"):
            found += 1
    print(f"✅ LocationExtractor: {len(articles)} haberden {found} tanesinde konum bulundu")
    print(f"   ⚠️  {len(articles) - found} haberde konum bulunamadı → haritada gösterilmeyecek")
    return articles