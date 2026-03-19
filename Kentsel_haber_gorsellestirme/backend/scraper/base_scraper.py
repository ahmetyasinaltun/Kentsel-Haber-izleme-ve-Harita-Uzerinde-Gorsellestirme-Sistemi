# Ortak scraper sınıfı
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

class BaseScraper:
    def __init__(self, site_name: str, base_url: str):
        self.site_name = site_name
        self.base_url = base_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }

    def fetch_page(self, url: str) -> BeautifulSoup | None:
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"❌ {self.site_name} fetch hatası: {e}")
            return None

    def is_recent(self, published_at: datetime, days: int = 3) -> bool:
        """Son 3 gün içinde mi?"""
        return datetime.utcnow() - published_at <= timedelta(days=days)

    def get_news(self) -> list[dict]:
        """Alt sınıflar bu metodu implement etmeli"""
        raise NotImplementedError