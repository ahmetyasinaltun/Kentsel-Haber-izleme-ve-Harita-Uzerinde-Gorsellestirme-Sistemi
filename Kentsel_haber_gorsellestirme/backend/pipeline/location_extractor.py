# NER / regex konum çıkarımı
# pipeline/location_extractor.py — Haber metninden konum çıkarımı (NER + regex)

import re

# ── Kocaeli ilçeleri ──────────────────────────────────────────────────────── #
DISTRICTS = [
    "İzmit", "Izmit", "Gebze", "Körfez", "Korfez", "Darıca", "Darica",
    "Çayırova", "Cayirova", "Dilovası", "Dilovasi", "Gölcük", "Golcuk",
    "Kandıra", "Kandira", "Karamürsel", "Karamursel", "Kartepe",
    "Başiskele", "Basiskele", "İzmit Merkez",
]

# ── Sık geçen mahalle ve semt adları ─────────────────────────────────────── #
# Ne kadar çok eklersen o kadar iyi — sahadan ekleyebilirsin
NEIGHBORHOODS = [
    # İzmit mahalleleri
    "Yahya Kaptan", "Kuruçeşme", "Kurucesme", "Kozluk", "Yenidoğan", "Yenidogan",
    "Bekirdere", "Çukurbağ", "Çukurbag", "Orhan", "Serdar", "Durhasan",
    "Turgut", "Hacıhasan", "Hacihasan", "Gündoğdu", "Gundogdu", "Yeniköy", "Yenikoy",
    "Nişantepe", "Nisantepe", "Akçaray", "Akcaray", "Tavşantepe", "Tavsantepe",
    "Ömerağa", "Omeraga", "Alemdar", "Arızlı", "Arizli",
    # Gebze mahalleleri
    "Güzeller", "Guzeller", "Pelitli", "Çoban Çeşme", "Çoban Cesme",
    "Kullar", "Tavşanlı", "Tavsanli", "Balçık", "Balcik",
    # Körfez / Gölcük
    "Denizçalı", "Denizcali", "Köseköy", "Kosekoy", "Kaletaşı", "Kaletasi",
    "Sekapark", "Izmit Merkez",
    # Diğer
    "Bağçeşme", "Bagcesme", "Hisareyn", "Nüzhetiye", "Nuzhetiye",
    "Kazandere", "Serindere", "Ayvazpınar", "Ayvazpinar",
]

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
    def extract(self, article: dict) -> dict:
        """
        article["location_text"] ve article["district"] alanlarını doldurur.
        Konum bulunamazsa her ikisi de None kalır.
        """
        text = (article.get("title", "") + " " + article.get("content", ""))

        location_text, district = self._find_location(text)

        article["location_text"] = location_text
        article["district"]      = district
        return article

    def _find_location(self, text: str):
        """
        En spesifik konumdan başlayarak arar:
          1. Mahalle / semt adı  → en spesifik
          2. Sokak / cadde regex
          3. Bağlam kalıpları ("X mahallesinde")
          4. İlçe adı            → en genel
        Bulunan konum + ilçe çifti döner. Hiçbiri bulunamazsa (None, None).
        """
        found_location = None
        found_district = None

        # 1) Mahalle adı ara
        for neighborhood in NEIGHBORHOODS:
            if re.search(re.escape(neighborhood), text, re.IGNORECASE):
                found_location = neighborhood
                break

        # 2) Sokak / cadde / bulvar regex
        if not found_location:
            match = STREET_PATTERN.search(text)
            if match:
                found_location = match.group(1).strip()

        # 3) Bağlam kalıpları ("Yahya Kaptan Mahallesinde")
        if not found_location:
            match = CONTEXT_PATTERN.search(text)
            if match:
                found_location = match.group(1).strip()

        # 4) İlçe adı ara (her durumda — district alanını doldurmak için)
        for district in DISTRICTS:
            if re.search(r'\b' + re.escape(district) + r'\b', text, re.IGNORECASE):
                found_district = district
                break

        # Konum bulunduysa ama ilçe bulunmadıysa → location_text'i ilçe olarak da kullan
        if found_location and not found_district:
            found_district = self._guess_district(found_location)

        # İlçe varsa location_text'e ekle (yoksa sadece mahalle adı kalır)
        if found_location and found_district:
            # Zaten ilçe adı içeriyorsa tekrar ekleme
            if found_district.lower() not in found_location.lower():
                found_location = f"{found_location}, {found_district}"

        # Sadece ilçe bulunduysa location_text = ilçe adı
        if not found_location and found_district:
            found_location = found_district

        return found_location, found_district

    def _guess_district(self, location_text: str) -> str | None:
        """Mahalle adından ilçeyi tahmin et (bilinen eşleşmeler)."""
        izmit_neighborhoods = [
            "Yahya Kaptan", "Kuruçeşme", "Kurucesme", "Yenidoğan", "Yenidogan",
            "Bekirdere", "Durhasan", "Gündoğdu", "Gundogdu", "Serdar",
            "Nişantepe", "Nisantepe", "Alemdar", "Ömerağa", "Omeraga",
            "Sekapark",
        ]
        gebze_neighborhoods = [
            "Güzeller", "Guzeller", "Pelitli", "Kullar", "Balçık", "Balcik",
        ]
        gölcük_neighborhoods = [
            "Denizçalı", "Denizcali", "Hisareyn", "Nüzhetiye", "Nuzhetiye",
        ]

        loc_lower = location_text.lower()
        if any(n.lower() in loc_lower for n in izmit_neighborhoods):
            return "İzmit"
        if any(n.lower() in loc_lower for n in gebze_neighborhoods):
            return "Gebze"
        if any(n.lower() in loc_lower for n in gölcük_neighborhoods):
            return "Gölcük"
        return None


def extract_locations(articles: list[dict]) -> list[dict]:
    """
    Tüm article listesi için konum çıkarımı yapar.

    Kullanım:
        from pipeline.location_extractor import extract_locations
        articles = extract_locations(articles)
    """
    extractor = LocationExtractor()
    found = 0

    for article in articles:
        extractor.extract(article)
        if article.get("location_text"):
            found += 1

    print(f"✅ LocationExtractor: {len(articles)} haberden {found} tanesinde konum bulundu")
    print(f"   ⚠️  {len(articles) - found} haberde konum bulunamadı → haritada gösterilmeyecek")
    return articles