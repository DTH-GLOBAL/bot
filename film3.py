import requests
import re
from bs4 import BeautifulSoup
import time

BASE_URL = "https://filmdizionline.com"
START_PAGE = 1
END_PAGE = 104
OUTPUT_FILE = "film-panel-3.m3u"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': BASE_URL
}

def isim_temizle(isim):
    parcalanmis = re.split(r'[:\-]', isim)
    return parcalanmis[0].strip()

def m3u8_bul(film_url):
    try:
        res = requests.get(film_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        iframe = soup.find('iframe', src=re.compile(r'japierdolevid\.com'))
        
        if iframe:
            iframe_url = iframe['src']
            video_res = requests.get(iframe_url, headers=headers, timeout=10)
            m3u8_match = re.search(r'["\'](?P<url>https?://[^"\']+\.m3u8)', video_res.text)
            if m3u8_match:
                return m3u8_match.group("url").replace('\\/', '/')
    except:
        pass
    return None

def baslat():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for page in range(START_PAGE, END_PAGE + 1):
            page_url = f"{BASE_URL}/filmler?page={page}"
            
            try:
                response = requests.get(page_url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                filmler = soup.find_all('div', class_='poster-long')
                
                for film in filmler:
                    anchor = film.find('a', href=True)
                    img_tag = film.find('img', class_='lazy')
                    
                    if anchor and img_tag:
                        ham_isim = img_tag.get('alt', '')
                        temiz_isim = isim_temizle(ham_isim)
                        film_link = anchor['href']
                        resim_url = img_tag.get('data-src') or img_tag.get('src')

                        m3u8_link = m3u8_bul(film_link)
                        
                        if m3u8_link:
                            f.write(f'#EXTINF:-1 tvg-id="vod.tr" tvg-name="TR: {temiz_isim}" tvg-logo="{resim_url}" group-title="Film Panel-3",TR: {temiz_isim}\n')
                            f.write(f'{m3u8_link}\n')
                
                time.sleep(1)
                
            except:
                continue

if __name__ == "__main__":
    baslat()
