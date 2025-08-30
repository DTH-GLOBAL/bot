import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import json
import re
import time
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

site_url = "https://www.showtv.com.tr"
diziler_url = "https://www.showtv.com.tr/diziler"
m3u_file = "showtv.m3u"

# Retry ve session ayarı
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    })
    return session

session = create_session()

# Bölüm sayfasından stream URL al
def parse_bolum_page(url):
    try:
        time.sleep(0.5)
        r = session.get(url, timeout=10)
        r.raise_for_status()
        match = re.search(r'data-hope-video=\'(.*?)\'', r.text)
        if match:
            video_data = json.loads(match.group(1).replace('&quot;', '"'))
            m3u8_list = video_data.get("media", {}).get("m3u8", [])
            for item in m3u8_list:
                if "src" in item and item["src"].endswith(".m3u8"):
                    return item["src"]
    except:
        return None
    return None

# Sezon sayfasından bölümleri al
def parse_episodes_page(url):
    try:
        time.sleep(0.3)
        r = session.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()["episodes"]
        items = []
        for item in data:
            items.insert(0, {
                "name": item["title"],
                "img": item["image"],
                "url": site_url + item["link"]
            })
        return items
    except:
        return []

# Bir dizinin tüm sayfalarını tarayıp tüm bölümleri al
def get_episodes_page(serie_url):
    all_items = []
    base_url = "https://www.showtv.com.tr/dizi/pagination/SERIE_ID/2/"
    serie_id = serie_url.split("/")[-1]
    url = base_url.replace("SERIE_ID", serie_id)
    page_no = 0
    while True:
        page_url = url + str(page_no)
        page_items = parse_episodes_page(page_url)
        if not page_items:
            break
        all_items = page_items + all_items
        page_no += 1
    return all_items

# Ana diziler sayfasını oku
def get_arsiv_page(url):
    items_list = []
    try:
        time.sleep(0.3)
        r = session.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        items = soup.find_all("div", {"data-name": "box-type6"})
        for item in items:
            item_url = site_url + item.find("a").get("href")
            item_img = item.find("img").get("src")
            item_name = item.find("span", {"class": "line-clamp-3"}).get_text().strip()
            items_list.append({
                "name": item_name,
                "img": item_img,
                "url": item_url
            })
    except:
        pass
    return items_list

# EXTNFİF M3U dosyası oluştur
def create_m3u_file(data):
    with open(m3u_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for serie in data:
            for ep in serie["episodes"]:
                line = f'#EXTINF:-1 tvg-id="vod.tr" tvg-name="TR: {ep["full_name"]}" tvg-logo="{ep["img"]}" group-title="SHOWTV DİZİLERİ",TR: {ep["full_name"]}\n{ep["stream_url"]}\n'
                f.write(line)
    print(f"{m3u_file} başarıyla oluşturuldu!")

def main(start=0, end=0):
    data = []
    series_list = get_arsiv_page(diziler_url)
    if end == 0:
        end = len(series_list)

    print(f"Toplam {len(series_list)} dizi bulundu.")
    
    for i in tqdm(range(start, end)):
        serie = series_list[i]
        episodes = get_episodes_page(serie["url"])
        if episodes:
            temp_serie = serie.copy()
            temp_serie["episodes"] = []
            for ep in episodes:
                stream_url = parse_bolum_page(ep["url"])
                if stream_url:
                    ep["stream_url"] = stream_url
                    ep["full_name"] = f'{serie["name"]} {ep["name"].replace(" ", "")}'
                    temp_serie["episodes"].append(ep)
            if temp_serie["episodes"]:
                data.append(temp_serie)

    create_m3u_file(data)

if __name__ == "__main__":
    main(0,0)
