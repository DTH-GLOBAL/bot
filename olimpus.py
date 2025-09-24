import cloudscraper
from bs4 import BeautifulSoup
import time

BASE_URL = "https://pornoanne.com"
TOTAL_PAGES = 3
M3U_FILE = "pornoanne.m3u"

scraper = cloudscraper.create_scraper()  # Cloudflare engelini geçer

def get_video_links(page_url):
    try:
        resp = scraper.get(page_url, timeout=15)
        if resp.status_code != 200:
            print(f"Hata {resp.status_code} : {page_url}")
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        video_tags = soup.find_all("h2", class_="entry-title")
        links = []
        for tag in video_tags:
            a_tag = tag.find("a")
            if a_tag and a_tag.get("href"):
                links.append(a_tag['href'])
        return links
    except Exception as e:
        print(f"Exception: {e}")
        return []

def get_video_data(video_url):
    try:
        resp = scraper.get(video_url, timeout=15)
        if resp.status_code != 200:
            print(f"Hata {resp.status_code} : {video_url}")
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Afiş resmi
        og_image = soup.find("meta", property="og:image")
        image_url = og_image['content'] if og_image else ""
        
        # Video başlığı
        og_title = soup.find("meta", property="og:image:alt")
        title = og_title['content'] if og_title else video_url.split("/")[-2]
        
        # ID: Resim URL'sinden al
        video_id = image_url.split("/")[-1].split(".")[0] if image_url else ""
        m3u_link = f"https://cdnfast.sbs/playlists/{video_id}/playlist.m3u8"
        
        return {
            "title": title,
            "image": image_url,
            "m3u": m3u_link
        }
    except Exception as e:
        print(f"Exception video: {e}")
        return None

with open(M3U_FILE, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for page in range(1, TOTAL_PAGES+1):
        page_url = f"{BASE_URL}/page/{page}/"
        print(f"Sayfa: {page_url}")
        video_links = get_video_links(page_url)
        for vlink in video_links:
            data = get_video_data(vlink)
            if data:
                f.write(f'#EXTINF:-1 tvg-logo="{data["image"]}" group-title="Pornoanne",{data["title"]}\n')
                f.write(f"{data['m3u']}\n")
        time.sleep(2)  # sayfa yükleme hızını yavaşlat, Cloudflare engeli için
print(f"M3U dosyası kaydedildi: {M3U_FILE}")
