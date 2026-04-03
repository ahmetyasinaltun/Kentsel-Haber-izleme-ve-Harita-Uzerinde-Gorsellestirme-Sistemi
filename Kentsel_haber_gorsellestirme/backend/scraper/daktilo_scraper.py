

import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from scraper.base_scraper import BaseScraper

AY_MAP = {
    "ocak":1, "şubat":2, "mart":3, "nisan":4, "mayıs":5, "haziran":6,
    "temmuz":7, "ağustos":8, "eylül":9, "ekim":10, "kasım":11, "aralık":12,
    "oca":1, "şub":2, "mar":3, "nis":4, "may":5, "haz":6,
    "tem":7, "ağu":8, "eyl":9, "eki":10, "kas":11, "ara":12,
}

DATE_RE = re.compile(
    r"(\d{1,2})\s+([A-Za-zÇçĞğİıÖöŞşÜü]+)\s+(\d{4})"
    r"(?:\s*[-–]\s*(\d{1,2}):(\d{2}))?",
    re.UNICODE | re.IGNORECASE,
)

ARTICLE_RE = re.compile(r"/haber/\d+/")


class DaktiloScraper(BaseScraper):
    """cagdaskocaeli, ozgurkocaeli, seskocaeli, bizimyaka için ortak scraper."""

    def __init__(self, site_name: str, base_url: str, max_workers: int = 5):
        super().__init__(site_name=site_name, base_url=base_url)
        self.max_workers = max_workers

    def get_news(self) -> list[dict]:
        soup = self.fetch_page(self.base_url)
        if not soup:
            print(f"❌ {self.site_name}: Ana sayfa alınamadı")
            return []

        visited = set()
        article_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not ARTICLE_RE.search(href):
                continue
            full_url = href if href.startswith("http") else self.base_url + href
            if full_url not in visited:
                visited.add(full_url)
                article_links.append(full_url)

        # Limit yok — tüm linkler çekilir
        print(f"  📎 {self.site_name}: {len(article_links)} makale — "
              f"paralel çekiliyor ({self.max_workers} thread)")

        news_list = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._parse_article, url): url
                       for url in article_links}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    news_list.append(result)

        news_list.sort(key=lambda x: x["published_at"], reverse=True)
        print(f"✅ {self.site_name}: {len(news_list)} haber çekildi")
        return news_list

    def _parse_article(self, url: str) -> dict | None:
        soup = self.fetch_page(url)
        if not soup:
            return None
        try:
            h1 = soup.find("h1")
            if not h1:
                return None
            title = h1.get_text(strip=True)
            if not title or len(title) < 10:
                return None

            content_tag = (
                soup.find("div", class_="detay") or
                soup.find("div", class_=lambda c: c and "detay" in c) or
                soup.find("div", class_=lambda c: c and "news-detail" in c) or
                soup.find("div", class_=lambda c: c and "article-content" in c) or
                soup.find("article")
            )
            if not content_tag:
                return None

            for bad in content_tag.find_all(
                ["script", "style", "ins", "iframe", "aside", "figure"]
            ):
                bad.decompose()

            content = content_tag.get_text(separator=" ", strip=True)
            if len(content) < 50:
                return None

            published_at = self._parse_date(soup)
            if not self.is_recent(published_at):
                return None

            return {
                "title":        title,
                "content":      content,
                "news_type":    None,
                "location_text":   None,
                "location_coords": None,
                "district":     None,
                "published_at": published_at,
                "sources":      [{"site_name": self.site_name, "url": url}],
                "embedding":    None,
                "scraped_at":   datetime.utcnow(),
            }
        except Exception as e:
            print(f"  ❌ Parse hatası ({url}): {e}")
            return None

    def _parse_date(self, soup) -> datetime:
        text = soup.get_text(" ", strip=True)
        for m in DATE_RE.finditer(text):
            ay_str = m.group(2).lower()
            if ay_str not in AY_MAP:
                continue
            try:
                return datetime(
                    int(m.group(3)), AY_MAP[ay_str], int(m.group(1)),
                    int(m.group(4) or 0), int(m.group(5) or 0),
                )
            except Exception:
                continue
        return datetime.utcnow()


class CagdasKocaeliScraper(DaktiloScraper):
    def __init__(self):
        super().__init__("cagdaskocaeli.com.tr", "https://www.cagdaskocaeli.com.tr")

class OzgurKocaeliScraper(DaktiloScraper):
    def __init__(self):
        super().__init__("ozgurkocaeli.com.tr", "https://www.ozgurkocaeli.com.tr")

class SesKocaeliScraper(DaktiloScraper):
    def __init__(self):
        super().__init__("seskocaeli.com", "https://www.seskocaeli.com")

class BizimYakaScraper(DaktiloScraper):
    def __init__(self):
        super().__init__("bizimyaka.com", "https://www.bizimyaka.com")