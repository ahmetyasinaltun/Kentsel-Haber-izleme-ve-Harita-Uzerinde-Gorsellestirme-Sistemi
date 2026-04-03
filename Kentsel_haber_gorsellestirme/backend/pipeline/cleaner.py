# HTML temizleme, normalizasyon

import re


class Cleaner:
    def clean(self, article: dict) -> dict:
        """
        Scraper'dan gelen ham article dict'ini temizler.
        title ve content alanlarını işler, diğer alanları olduğu gibi bırakır.
        """
        article["title"]   = self._clean_text(article.get("title", ""))
        article["content"] = self._clean_text(article.get("content", ""))
        return article

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""

        # 1) HTML tag'lerini kaldır (<p>, <br>, <span class="x"> vs.)
        text = re.sub(r"<[^>]+>", " ", text)

        # 2) HTML entity'lerini düzelt (&nbsp; &amp; &lt; &gt; &quot;)
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;",  "&")
        text = text.replace("&lt;",   "<")
        text = text.replace("&gt;",   ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;",  "'")

        # 3) Reklam / takip metinlerini kaldır
        #   =
        ad_patterns = [
            r"javascript\s*:",
            r"window\.__[A-Z_]+\s*=",        # JS global değişkenler
            r"googletag\.[a-z]+\(",           # Google reklam
            r"(adsbygoogle|advert|reklam)\s*=",
            r"Bu haberi paylaş.*",
            r"Abone ol.*",
            r"Haberi oku.*",
            r"Devamını oku.*",
            r"İlgili haberler.*",
            r"Yorum yap.*",
            r"Yorum Yaz.*",
            r"Sosyal medyada paylaş.*",
        ]
        for pattern in ad_patterns:
            text = re.sub(pattern, " ", text, flags=re.IGNORECASE | re.DOTALL)

        # 4) URL'leri kaldır (http/https ile başlayanlar)
        text = re.sub(r"https?://\S+", " ", text)

        # 5) E-posta adreslerini kaldır
        text = re.sub(r"\S+@\S+\.\S+", " ", text)

        # 6) Gereksiz özel karakterleri temizle
        #    Türkçe harf, rakam, noktalama ve boşluk dışındakileri sil
        text = re.sub(r"[^\w\s\.,;:!?\"'\(\)\-–—/çÇğĞıİöÖşŞüÜ]", " ", text)

        # 7) Fazla boşlukları ve satır sonlarını normalize et
        text = re.sub(r"\s+", " ", text)

        # 8) Baş ve sondaki boşlukları kaldır
        text = text.strip()

        return text


def clean_articles(articles: list[dict]) -> list[dict]:
    """
    Scraper'dan gelen tüm article listesini temizler.

    Kullanım:
        from pipeline.cleaner import clean_articles
        cleaned = clean_articles(raw_articles)
    """
    cleaner = Cleaner()
    cleaned = []

    for article in articles:
        cleaned_article = cleaner.clean(article)

        # Temizleme sonrası içerik çok kısaldıysa listeden çıkar
        if len(cleaned_article.get("content", "")) < 50:
            print(f"⚠️  İçerik çok kısa, atlandı: {cleaned_article.get('title', 'başlıksız')[:50]}")
            continue

        cleaned.append(cleaned_article)

    print(f"✅ Cleaner: {len(articles)} haberden {len(cleaned)} tanesi temizlendi")
    return cleaned