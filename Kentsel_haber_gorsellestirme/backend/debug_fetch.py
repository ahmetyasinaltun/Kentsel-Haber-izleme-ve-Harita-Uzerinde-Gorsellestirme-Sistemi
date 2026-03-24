# debug_fetch2.py
import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper()
r = scraper.get("https://www.cagdaskocaeli.com.tr", timeout=20)

print("Encoding (response):", r.encoding)
print("Encoding (apparent):", r.apparent_encoding)
print("Content-Type:", r.headers.get('content-type'))

# apparent_encoding değil, direkt utf-8 dene
r.encoding = 'utf-8'
soup = BeautifulSoup(r.text, "html.parser")

links = soup.find_all("a", href=True)
print(f"\nToplam link: {len(links)}")
print("İlk 10 link:")
for a in links[:10]:
    print(" ", a['href'])

# Body'nin ilk 1000 karakteri
body = soup.find("body")
if body:
    print("\nBody başlangıcı:")
    print(body.get_text()[:500])