# Ortak scraper sınıfı
import time
import random
import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


class BaseScraper:
    def __init__(self, site_name: str, base_url: str):
        self.site_name = site_name
        self.base_url  = base_url
       
        self._session  = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )

    def fetch_page(self, url: str, timeout: int = 20,
                   retries: int = 2, delay: float = 2.0) -> BeautifulSoup | None:
        last_error = None
        for attempt in range(1 + retries):
            try:
                r = self._session.get(url, timeout=timeout, allow_redirects=True)
                r.raise_for_status()
                
                soup  = BeautifulSoup(r.text, "html.parser")
                links = soup.find_all("a", href=True)
                if len(links) < 5 and attempt < retries:
                    print(f"  ⚠️  {self.site_name}: Az link ({len(links)}), tekrar deneniyor...")
                    time.sleep(delay + 2)
                    continue
                return soup
            except Exception as e:
                last_error = e
                if attempt < retries:
                    time.sleep(delay)

        print(f"❌ {self.site_name} fetch hatası: {last_error}")
        return None

    def wait(self, base: float = 1.0):
        time.sleep(base + random.uniform(0.2, 0.8))

    def is_recent(self, published_at: datetime, days: int = 3) -> bool:
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff = today_start - timedelta(days=days - 1)
        return published_at >= cutoff

    def get_news(self) -> list[dict]:
        raise NotImplementedError