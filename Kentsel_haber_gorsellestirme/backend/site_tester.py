import requests
from bs4 import BeautifulSoup
import sys
import os

# Proje dizininden pipeline modülünü import edebilmek için yolu ayarlıyoruz
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.cleaner import Cleaner

URLS = [
    "https://www.ozgurkocaeli.com.tr/haber/27740382/200-bin-tllik-kablo-calan-hirsizlar-yakalandi",
    "https://www.cagdaskocaeli.com.tr/haber/27740419/basiskelede-200-bin-tllik-kablo-vurgunu-izmitteki-gizli-adreste-yakalandilar",
    "https://www.bizimyaka.com/haber/27742548/200-bin-liralik-kablo-calan-hirsizlarin-bindigi-motosiklet-de-calinti-cikti"
]

def fetch_and_test_content():
    cleaner = Cleaner()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for i, url in enumerate(URLS, 1):
        site_name = url.split('/')[2]
        print(f"\n{'='*70}")
        print(f"🔍 HABER {i} | KAYNAK: {site_name}")
        print(f"{'-'*70}")

        try:
            # HTML'i çekiyoruz
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Haber metnini almak için <p> etiketlerini topluyoruz
            # (Çoğu haber sitesi ana metni p etiketleri içinde tutar)
            paragraphs = soup.find_all('p')
            raw_text = " ".join([p.get_text() for p in paragraphs])
            
            if not raw_text.strip():
                print("⚠️ İçerik çekilemedi. Site farklı bir DOM yapısı kullanıyor olabilir.")
                continue
            
            # Senin sistemindeki Cleaner'dan geçiriyoruz
            dummy_article = {"title": "Test", "content": raw_text}
            cleaned_article = cleaner.clean(dummy_article)
            cleaned_text = cleaned_article["content"]
            
            # İlk 200 karakteri alıyoruz
            ilk_200 = cleaned_text[:200]
            
            print(f"📝 İLK 200 KARAKTER:\n")
            print(f"\"{ilk_200}\"\n")
            
        except Exception as e:
            print(f"❌ İstek sırasında hata oluştu: {e}")

if __name__ == "__main__":
    fetch_and_test_content()