# yenikocaeli_scraper_test.py
import sys
sys.path.insert(0, ".")
from scraper.yenikocaeli import YeniKocaeliScraper

scraper = YeniKocaeliScraper(max_news=3, max_workers=3)
news = scraper.get_news()

for n in news:
    print(f"\nBaşlık  : {n['title'][:70]}")
    print(f"İçerik  : {n['content'][:200]}")
    print(f"Tarih   : {n['published_at']}")