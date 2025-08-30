import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import yaml

main_url = "https://puhutv.com/"
diziler_url = "https://puhutv.com/dizi"

def get_series_details(series_id):
    url = f"https://appservice.puhutv.com/service/serie/getSerieInformations?id={series_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()[0]
    return {"title": "", "seasons": []}

def get_stream_urls(season_slug):
    url = urljoin(main_url, season_slug)
    r = requests.get(url)
    if r.status_code != 200:
        print(f"Error: {r.status_code}, URL: {url}")
        return []

    soup = BeautifulSoup(r.content, "html.parser")
    try:
        content = json.loads(soup.find("script", {"id": "__NEXT_DATA__"}).string)["props"]["pageProps"]["episodes"]["data"]
    except:
        return []

    episodes = []
    for ep in content["episodes"]:
        episodes.append({
            "id": ep["id"],
            "name": ep["name"],
            "img": ep["image"],
            "url": urljoin(main_url, ep["slug"]),
            "stream_url": f"https://dygvideo.dygdigital.com/api/redirect?PublisherId=29&ReferenceId={ep['video_id']}&SecretKey=NtvApiSecret2014*&.m3u8"
        })
    return episodes

def get_all_content():
    r = requests.get(diziler_url)
    if r.status_code != 200:
        print(f"Error: {r.status_code}")
        return []

    soup = BeautifulSoup(r.content, "html.parser")
    try:
        container_items = json.loads(soup.find("script", {"id": "__NEXT_DATA__"}).string)["props"]["pageProps"]["data"]["data"]["container_items"]
    except:
        return []

    series_list = []
    for item in container_items:
        for content in item["items"]:
            series_list.append(content)

    all_series = []
    for series in tqdm(series_list, desc="Processing Series"):
        series_id = series["id"]
        series_name = series["name"]
        series_slug = series["meta"]["slug"]
        series_img = series["image"]

        series_details = get_series_details(series_id)
        if not series_details["seasons"]:
            continue

        temp_series = {
            "name": series_name,
            "img": series_img,
            "url": urljoin(main_url, series_slug),
            "episodes": []
        }

        for season in series_details["seasons"]:
            season_slug = season["slug"]
            season_name = season["name"]
            episodes = get_stream_urls(season_slug)
            for ep in episodes:
                ep["name"] = f"{season_name} - {ep['name']}"
                temp_series["episodes"].append(ep)

        all_series.append(temp_series)

    return all_series

def create_m3u_file(data, filename="puhutv.m3u"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for series in data:
            for ep in series["episodes"]:
                line = f'#EXTINF:-1 tvg-id="vod.tr" tvg-name="TR: {ep["name"]}" tvg-logo="{ep["img"]}" group-title="PUHUTV DİZİLER",TR: {ep["name"]}\n{ep["stream_url"]}\n'
                f.write(line)
    print(f"{filename} başarıyla oluşturuldu!")

def create_yaml_file(data, filename="puhutv.yml"):
    with open(filename, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)
    print(f"{filename} başarıyla oluşturuldu!")

def main():
    data = get_all_content()
    create_m3u_file(data)
    create_yaml_file(data)

if __name__ == "__main__":
    main()
