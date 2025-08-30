import sys
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import json
import re
import time
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

sys.path.insert(0, '../../utilities')
from jsontom3u import create_single_m3u, create_m3us, create_json

site_url = "https://www.showtv.com.tr"
diziler_url = "https://www.showtv.com.tr/diziler"
m3u_file = "showtv.m3u"

# Retry stratejisi ve session ayarları
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
    except Exception as e:
        print(f"Bölüm hatası: {url} - {str(e)}")
    return None

def parse_episodes_page(url):
    try:
        time.sleep(0.3)
        r = session.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()["episodes"]
        item_list = []
        for item in data:
            item_name = item["title"]
            item_img = item["image"]
            item_url = site_url + item["link"]
            item_list.insert(0, {"name": item_name, "img": item_img, "url": item_url})
        return item_list
    except:
        return []

def get_episodes_page(serie_url):
    all_items = []
    base_url = "https://www.showtv.com.tr/dizi/pagination/SERIE_ID/2/"
    serie_id = serie_url.split("/")[-1]
    url = base_url.replace("SERIE_ID", serie_id)
    flag = True
    page_no = 0
    while flag:
        page_url = url + str(page_no)
        page_items = parse_episodes_page(page_url)
        if not page_items:
            flag = False
        else:
            all_items = page_items + all_items
        page_no += 1
    return all_items

def get_arsiv_page(url):
    item_list = []
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
            item_id = item_url.split("/")[-1]
            item_list.append({"name": item_name, "img": item_img, "url": item_url, "id": item_id})
    except:
        pass
    return item_list

def main(start=0, end=0):
    data = []
    series_list = get_arsiv_page(diziler_url)
    if end == 0:
        end_index = len(series_list)
    else:
        end_index = end

    print(f"Toplam {len(series_list)} dizi bulundu.")
    
    for i in tqdm(range(start, end_index)):
        serie = series_list[i]
        episodes = get_episodes_page(serie["url"])
        if episodes:
            temp_serie = serie.copy()
            temp_serie["episodes"] = []
            for ep in episodes:
                stream_url = parse_bolum_page(ep["url"])
                ep["stream_url"] = stream_url
                if stream_url:
                    # Full name: dizi adı + sezon ve bölüm numarası (gereksiz boşluk kaldırıldı)
                    ep["full_name"] = f'{serie["name"]} {ep["name"].replace(" ", "")}'
                    temp_serie["episodes"].append(ep)
            if temp_serie["episodes"]:
                data.append(temp_serie)

    # M3U oluştur
    with open(m3u_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for serie in data:
            for ep in serie["episodes"]:
                line = f'#EXTINF:-1 tvg-id="vod.tr" tvg-name="TR: {ep["full_name"]}" tvg-logo="{ep["img"]}" group-title="SHOWTV DİZİLERİ",TR: {ep["full_name"]}\n{ep["stream_url"]}\n'
                f.write(line)
    print(f"{m3u_file} başarıyla oluşturuldu!")

    # JSON ve M3U alternatifleri
    create_single_m3u("showtv", data)
    create_m3us("../../lists/video/sources/www-showtv-com-tr/video", data)
    create_json("www-showtv-com-tr-diziler.json", data)

if __name__ == "__main__":
    main(0,0)
