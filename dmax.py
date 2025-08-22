import os
import re
import time
import requests
import urllib3

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PLAYLIST_FILE = "dmax.m3u"
LOG_FILE = "progress.log"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                  " AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/91.0.4472.124 Safari/537.36"
}

# Başlıktan silinecek ifadeler
REMOVE_TITLES = ["Bölümler", "Kısa Videolar", "Haberler"]

def curl_get(url):
    try:
        resp = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        time.sleep(1)
        return resp.text
    except Exception as e:
        print(f"Hata: {e}", flush=True)
        return ""

def write_log(message):
    print(message, flush=True)  # GitHub Actions logunda anlık görünür
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def get_series_list():
    url = "https://www.dmax.com.tr/kesfet?size=80"
    html = curl_get(url)
    series = []
    seen = set()

    matches = re.findall(
        r'<div class="poster">.*?<a.*?href="(https://www\.dmax\.com\.tr/[a-z0-9-]+)".*?<img src="(https://img-tlctv1\.mncdn\.com/.*?)" alt=""',
        html, re.S
    )

    for series_url, logo in matches:
        if series_url not in seen:
            seen.add(series_url)
            series.append({
                "url": series_url,
                "logo": logo,
                "name": os.path.basename(series_url)
            })
    return series

def get_season_count(url):
    html = curl_get(url)
    seasons = re.findall(r'<option value="(\d+)">', html)
    return list(reversed(seasons)) if seasons else []

def clean_series_name(name):
    for word in REMOVE_TITLES:
        name = name.replace(word, "")
    return name.strip()

def get_episodes(base_url, season, series_name, logo, m3u8_content, result):
    episode_count = 0

    for episode in range(1, 101):
        if episode in result.get(series_name, {}).get(season, {}):
            continue

        episode_url = f"{base_url}/{season}-sezon-{episode}-bolum"
        html = curl_get(episode_url)

        if "video-player vod-player" not in html:
            break

        code_match = re.search(r'data-video-code="(.*?)"', html)
        if code_match:
            code = code_match.group(1)
            m3u8 = f"https://dygvideo.dygdigital.com/api/redirect?PublisherId=27&ReferenceId={code}&SecretKey=NtvApiSecret2014*&.m3u8"

            m3u8_line = (
                f'#EXTINF:-1 tvg-id="vod.tr" tvg-name="TR: {series_name} {season} Sezon {episode} Bölüm" '
                f'tvg-logo="{logo}" group-title="DMAX BELGESELLER",TR: {series_name} {season} Sezon {episode} Bölüm\n'
                f'{m3u8}\n'
            )

            m3u8_content += m3u8_line

            result.setdefault(series_name, {}).setdefault(season, {})[episode] = {
                "code": code,
                "m3u8": m3u8
            }

            with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
                f.write(m3u8_content)

            # Anlık olarak GitHub loguna yaz
            print(f"[{series_name} S{season}E{episode}] {m3u8}", flush=True)

            episode_count += 1

    return episode_count, m3u8_content, result

def main():
    # Başlangıç dosyalarını temizle
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("")

    result = {}
    m3u8_content = "#EXTM3U\n"

    series_list = get_series_list()
    total_series = len(series_list)
    write_log(f"Toplam {total_series} dizi bulundu.")

    for idx, series in enumerate(series_list, start=1):
        base_url = series["url"].rstrip("/")
        main_html = curl_get(base_url)

        title_match = re.search(r"<title>(.*?)</title>", main_html)
        series_name = title_match.group(1).replace(" | DMAX", "") if title_match else os.path.basename(base_url)

        # Fazlalıkları sil
        series_name = clean_series_name(series_name)
        series["name"] = series_name

        write_log(f"{idx}. dizi ({series_name}) çekiliyor...")

        seasons = get_season_count(base_url)
        result[series_name] = {}
        total_episodes = 0

        for season in seasons:
            ep_count, m3u8_content, result = get_episodes(base_url, season, series_name, series["logo"], m3u8_content, result)
            total_episodes += ep_count

        write_log(f"{series_name} tamamlandı, {total_episodes} bölüm bulundu.")

    write_log("Tüm diziler işlendi!")

if __name__ == "__main__":
    main()
