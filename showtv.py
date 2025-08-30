import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import re
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return session

session = create_session()
pattern = r'data-hope-video=\'(.*?)\''

def parse_bolum_page(url):
    try:
        time.sleep(0.5)
        r = session.get(url, timeout=10)
        r.raise_for_status()
        match = re.search(pattern, r.text)
        if match:
            video_data = match.group(1).replace('&quot;', '"')
            import json
            video_data = json.loads(video_data)
            m3u8_list = video_data.get("media", {}).get("m3u8", [])
            for item in m3u8_list:
                if "src" in item and item["src"].endswith(".m3u8"):
                    return item["src"]
    except Exception as e:
        print(f"Bölüm sayfası hatası: {url} - {str(e)}")
    return None

def parse_episodes_page(url):
    try:
        time.sleep(0.3)
        r = session.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()["episodes"]
        item_list = []
        for item in data:
            item_name = item["title"].replace("-", " ")  # Boşluk olarak düzeltildi
            item_img = item["image"]
            item_url = site_url + item["link"]
            item_list.insert(0, {"name": item_name, "img": item_img, "url": item_url})
        return item_list
    except Exception as e:
        print(f"Bölümler sayfası hatası: {url} - {str(e)}")
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
            item_name = item.find("span", {"class": "line-clamp-3"}).get_text().strip().replace("-", " ")
            item_id = item_url.split("/")[-1]
            item_list.append({"name": item_name, "img": item_img, "url": item_url, "id": item_id})
    except Exception as e:
        print(f"Arşiv sayfası hatası: {url} - {str(e)}")
    return item_list

def main(start=0, end=0):
    data = []
    series_list = get_arsiv_page(diziler_url)
    if end == 0:
        end_index = len(series_list)
    else:
        end_index = end

    print(f"Toplam {len(series_list)} dizi bulundu. İşlem başlıyor...")

    for i in tqdm(range(start, end_index)):
        serie = series_list[i]
        print(f"{i+1}/{end_index} - {serie['name']}")

        try:
            episodes = get_episodes_page(serie["url"])
            if episodes:
                temp_serie = serie.copy()
                temp_serie["episodes"] = []

                print(f"  {len(episodes)} bölüm bulundu")
                for j in range(len(episodes)):
                    episode = episodes[j]
                    stream_url = parse_bolum_page(episode["url"])
                    episode["stream_url"] = stream_url
                    if stream_url:
                        temp_serie["episodes"].append(episode)

                if temp_serie["episodes"]:
                    data.append(temp_serie)
                    print(f"  {len(temp_serie['episodes'])} bölüm stream URL'si bulundu")
                else:
                    print(f"  Hiçbir bölümde stream URL'si bulunamadı")
            else:
                print(f"  Bölüm bulunamadı")

        except Exception as e:
            print(f"  Dizi işlenirken hata: {str(e)}")
            continue

    print(f"\nToplam {len(data)} dizi işlendi")

    # M3U oluştur
    with open(m3u_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for serie in data:
            for ep in serie["episodes"]:
                line = f'#EXTINF:-1 tvg-id="vod.tr" tvg-name="TR: {ep["name"]}" tvg-logo="{ep["img"]}" group-title="SHOWTV Dizileri",TR: {ep["name"]}\n{ep["stream_url"]}\n'
                f.write(line)

    print(f"{m3u_file} başarıyla oluşturuldu!")

if __name__ == "__main__":
    main()
