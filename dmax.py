import requests
import re
import os
import time
from bs4 import BeautifulSoup
from datetime import datetime

# cURL ile sayfa kaynağını çeken fonksiyon
def curl_get(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, verify=False, allow_redirects=True, headers=headers)
        response.raise_for_status()
        time.sleep(1)  # İstekler arasında 1 saniye bekle
        return response.text
    except requests.RequestException:
        return ""

# Dizi listesini çekme
def get_series_list():
    url = "https://www.dmax.com.tr/kesfet?size=80"
    html = curl_get(url)
    series = []
    unique_urls = []  # Yinelenen URL'leri kontrol etmek için

    # Regex ile tüm poster linklerini ve logoları çek
    pattern = r'<div class="poster">.*?<a.*?href="(https:\/\/www\.dmax\.com\.tr\/[a-z0-9-]+)".*?<img src="(https:\/\/img-tlctv1\.mncdn\.com\/.*?)" alt=""'
    matches = re.finditer(pattern, html, re.DOTALL)

    for match in matches:
        series_url = match.group(1)
        # URL zaten eklenmişse atla
        if series_url not in unique_urls:
            unique_urls.append(series_url)
            series.append({
                'url': series_url,
                'logo': match.group(2),
                'name': series_url.split('/')[-1]  # Geçici isim
            })
    return series

# Sezon sayısını çekme
def get_season_count(url):
    html = curl_get(url)
    season_matches = re.findall(r'<option value="(\d+)">', html)
    return list(reversed(season_matches))  # 1’den başlasın

# Bölüm bilgilerini çekme
def get_episodes(base_url, season, series_name, logo, m3u8_content, result, log):
    episode_count = 0
    filename = 'playlists/dmax.m3u'
    
    for episode in range(1, 101):
        # Bölüm zaten eklenmişse atla
        if series_name in result and season in result[series_name] and str(episode) in result[series_name][season]:
            continue

        episode_url = f"{base_url}/{season}-sezon-{episode}-bolum"
        episode_html = curl_get(episode_url)

        if 'video-player vod-player' in episode_html:
            code_match = re.search(r'data-video-code="(.*?)"', episode_html)
            if code_match:
                code = code_match.group(1)
                m3u8 = f"https://dygvideo.dygdigital.com/api/redirect?PublisherId=27&ReferenceId={code}&SecretKey=NtvApiSecret2014*&.m3u8"

                # M3U8 satırı
                m3u8_content.append(f'#EXTINF:-1 tvg-id="vod.tr" tvg-name="TR: {series_name} {season} Sezon {episode} Bölüm" tvg-logo="{logo}" group-title="DMAX BELGESELLER",TR: {series_name} {season} Sezon {episode} Bölüm\n')
                m3u8_content.append(f"{m3u8}\n")

                # Sonuçları sakla
                if series_name not in result:
                    result[series_name] = {}
                if season not in result[series_name]:
                    result[series_name][season] = {}
                result[series_name][season][str(episode)] = {
                    'code': code,
                    'm3u8': m3u8
                }

                # Anlık olarak M3U8 dosyasına yaz
                if not os.path.exists('playlists'):
                    os.makedirs('playlists', mode=0o777)
                with open(filename, 'w') as f:
                    f.write(''.join(m3u8_content))

                episode_count += 1
        else:
            break  # Bölüm yoksa döngüyü kır
    return episode_count, m3u8_content

# İlerleme logunu yaz
def write_log(message):
    log_file = 'playlists/progress.log'
    with open(log_file, 'a') as f:
        f.write(f"{message}\n")

# İşlem
result = {}
m3u8_content = ["#EXTM3U\n"]
log = []

# İlk olarak M3U8 dosyasını başlıkla başlat
filename = 'playlists/dmax.m3u'
if not os.path.exists('playlists'):
    os.makedirs('playlists', mode=0o777)
with open(filename, 'w') as f:
    f.write("#EXTM3U\n")

series_list = get_series_list()
total_series = len(series_list)
write_log(f"Toplam {total_series} dizi bulundu.")

for index, series in enumerate(series_list):
    base_url = series['url'].rstrip('/')
    main_html = curl_get(base_url)

    # Dizi adını çek
    title_match = re.search(r'<title>(.*?)</title>', main_html)
    series_name = title_match.group(1).replace(' | DMAX', '') if title_match else base_url.split('/')[-1]
    series['name'] = series_name

    # İlerleme logu
    write_log(f"{index + 1}. dizi ({series_name}) çekiliyor...")

    # Sezonları çek
    seasons = get_season_count(base_url)
    result[series_name] = {}
    total_episodes = 0

    # Bölümleri çek ve M3U8’a ekle
    for season in seasons:
        episode_count, m3u8_content = get_episodes(base_url, season, series_name, series['logo'], m3u8_content, result, log)
        total_episodes += episode_count

    # Dizi tamamlandı
    write_log(f"{series_name} tamamlandı, {total_episodes} bölüm bulundu.")

write_log("Tüm diziler işlendi!")
