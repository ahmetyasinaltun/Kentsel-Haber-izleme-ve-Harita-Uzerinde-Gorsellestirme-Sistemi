# cagdaskocaeli.com scraper
from scraper.base_scraper import BaseScraper
from datetime import datetime
import re

class CagdasKocaeliScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            site_name="cagdaskocaeli.com.tr",
            base_url="https://www.cagdaskocaeli.com.tr"
        )

    def get_news(self) -> list[dict]:
        news_list = []
        soup = self.fetch_page(self.base_url)
        if not soup:
            return news_list

        # Haber linklerini bul (site yapısına göre güncellenir)
        articles = soup.find_all("a", href=True)
        visited = set()

        for a in articles:
            href = a["href"]
            # Haber URL'si genellikle /haber/ veya rakam içerir
            if "/haber/" not in href and not re.search(r'/\d+/', href):
                continue
            
            full_url = href if href.startswith("http") else self.base_url + href
            if full_url in visited:
                continue
            visited.add(full_url)

            article_data = self._parse_article(full_url)
            if article_data:
                news_list.append(article_data)

            if len(news_list) >= 20:  # Test için limit
                break

        print(f"✅ {self.site_name}: {len(news_list)} haber çekildi")
        return news_list

    def _parse_article(self, url: str) -> dict | None:
        soup = self.fetch_page(url)
        if not soup:
            return None

        try:
            # Başlık
            title_tag = (soup.find("h1") or 
                        soup.find("h2", class_=re.compile("title|baslik", re.I)))
            if not title_tag:
                return None
            title = title_tag.get_text(strip=True)

            # İçerik
            content_tag = (soup.find("div", class_=re.compile("content|icerik|article|haber", re.I)) or
                          soup.find("article"))
            content = content_tag.get_text(separator=" ", strip=True) if content_tag else ""

            if len(content) < 50:  # Çok kısa içerik → atla
                return None

            return {
                "title": title,
                "content": content,
                "news_type": None,       # Sonra classifier dolduracak
                "location_text": None,   # Sonra extractor dolduracak
                "location_coords": None, # Sonra geocoder dolduracak
                "district": None,
                "published_at": datetime.utcnow(),  # Sonra tarih parse eklenecek
                "sources": [{
                    "site_name": self.site_name,
                    "url": url
                }],
                "embedding": None,       # Sonra deduplicator dolduracak
                "scraped_at": datetime.utcnow()
            }
        except Exception as e:
            print(f"❌ Parse hatası ({url}): {e}")
            return None