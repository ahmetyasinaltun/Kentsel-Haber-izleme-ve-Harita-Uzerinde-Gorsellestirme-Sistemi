# bizimyaka.com scraper
# bizimyaka.com scraper
from scraper.base_scraper import BaseScraper
from datetime import datetime
import re

TR_MONTHS = {
    "ocak": 1, "şubat": 2, "mart": 3, "nisan": 4,
    "mayıs": 5, "haziran": 6, "temmuz": 7, "ağustos": 8,
    "eylül": 9, "ekim": 10, "kasım": 11, "aralık": 12,
}

def _parse_tr_date(text: str) -> datetime | None:
    if not text:
        return None
    text = text.strip().lower()
    m = re.search(r"(\d{1,2})\s+([a-zğüşıöç]+)\s+(\d{4})", text)
    if m:
        month = TR_MONTHS.get(m.group(2))
        if month:
            return datetime(int(m.group(3)), month, int(m.group(1)))
    m = re.search(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", text)
    if m:
        try:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass
    return None


class BizimYakaScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            site_name="bizimyaka.com",
            base_url="https://www.bizimyaka.com"
        )

    def get_news(self) -> list[dict]:
        news_list = []
        soup = self.fetch_page(self.base_url)
        if not soup:
            return news_list

        articles = soup.find_all("a", href=True)
        visited = set()

        for a in articles:
            href = a["href"]

            # Bizimyaka haber URL'leri /haber/ veya /gundem/ içerir
            is_article = (
                "/haber/" in href or
                "/gundem/" in href or
                "/son-dakika/" in href or
                re.search(r'/\d{4,}/', href)
            )
            if not is_article:
                continue
            if any(x in href for x in ["/kategori/", "/tag/", "/sayfa/",
                                        "/page/", "/yazar/", "/etiket/"]):
                continue

            full_url = href if href.startswith("http") else self.base_url + href
            if full_url in visited:
                continue
            visited.add(full_url)

            article_data = self._parse_article(full_url)
            if article_data:
                news_list.append(article_data)

            if len(news_list) >= 20:
                break

        print(f"✅ {self.site_name}: {len(news_list)} haber çekildi")
        return news_list

    def _parse_article(self, url: str) -> dict | None:
        soup = self.fetch_page(url)
        if not soup:
            return None

        try:
            # Başlık
            title_tag = (
                soup.find("h1", class_=re.compile("title|baslik|news|haber", re.I)) or
                soup.find("h1")
            )
            if not title_tag:
                return None
            title = title_tag.get_text(strip=True)

            # İçerik — .news-body, .news-text veya .haber-icerik
            content_tag = (
                soup.find("div", class_=re.compile("news-body|news-text|news-content|haber-icerik|icerik|content|article", re.I)) or
                soup.find("article")
            )
            content = content_tag.get_text(separator=" ", strip=True) if content_tag else ""
            if len(content) < 50:
                return None

            # Tarih
            published_at = self._parse_date(soup)
            if not self.is_recent(published_at):
                return None

            return {
                "title": title,
                "content": content,
                "news_type": None,
                "location_text": None,
                "location_coords": None,
                "district": None,
                "published_at": published_at,
                "sources": [{"site_name": self.site_name, "url": url}],
                "embedding": None,
                "scraped_at": datetime.utcnow()
            }
        except Exception as e:
            print(f"❌ Parse hatası ({url}): {e}")
            return None

    def _parse_date(self, soup) -> datetime:
        time_tag = soup.find("time")
        if time_tag:
            dt_attr = time_tag.get("datetime", "")
            if dt_attr:
                try:
                    return datetime.fromisoformat(dt_attr[:10])
                except ValueError:
                    pass
        date_tag = soup.find(class_=re.compile(r"tarih|date", re.I))
        if date_tag:
            parsed = _parse_tr_date(date_tag.get_text())
            if parsed:
                return parsed
        return datetime.utcnow()