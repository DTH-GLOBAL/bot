import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://pornoanne.com"
START_PAGE = 1
END_PAGE = 325  # sayfa sayısı

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

OUTPUT_FILE = "pornoanne.m3u"

def get_video_pages(page_num):
    url = f"{BASE_URL}/page/{page_num}/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            print(f"Hata: Sayfa {page_num} yüklenemedi, status code: {resp.status_code}")
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        links = []
        for h2 in soup.find_all("h2", class_="entry-title"):
            a_tag = h2.find("a")
            if a_tag and a_tag.get("href"):
                links.append(a_tag["href"])
        return links
    except Exception as e:
        print(f"Sayfa {page_num} hata: {e}")
        return []

def get_video_info(video_url):
    try:
        resp = requests.get(video_url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            print(f"Hata: Video sayfası yüklenemedi {video_url}")
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        # Video başlığı
        title_tag = soup.find("meta", property="og:image:alt")
        title = title_tag["content"] if title_tag else "Unknown"

        # Resim
        img_tag = soup.find("meta", property="og:image")
        img_url = img_tag["content"] if img_tag else ""

        # Resimden ID çıkar
        video_id = img_url.split("/")[-1].split(".")[0] if img_url else ""
        if video_id:
            m3u8_link = f"https://cdnfast.sbs/playlists/{video_id}/playlist.m3u8"
        else:
            m3u8_link = ""

        return {"title": title, "img": img_url, "m3u8": m3u8_link}
    except Exception as e:
        print(f"Video linki hata: {video_url}, {e}")
        return None

def main():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for page in range(START_PAGE, END_PAGE + 1):
            print(f"Sayfa {page} çekiliyor...")
            video_links = get_video_pages(page)
            if not video_links:
                continue
            for link in video_links:
                info = get_video_info(link)
                if info and info["m3u8"]:
                    f.write(f'#EXTINF:-1 tvg-logo="{info["img"]}" group-title="pornoanne.com",{info["title"]}\n')
                    f.write(f'{info["m3u8"]}\n')
                time.sleep(1)  # fazla yüklenmeyi önlemek için
            time.sleep(2)

if __name__ == "__main__":
    main()
