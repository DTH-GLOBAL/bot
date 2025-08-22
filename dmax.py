import requests
import re
import os
import time
from urllib.parse import urlparse

# Function to fetch page content using requests
def curl_get(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers, allow_redirects=True, verify=False)
    time.sleep(1)  # Wait 1 second between requests
    return response.text

# Function to get series list
def get_series_list():
    url = "https://www.dmax.com.tr/kesfet?size=80"
    html = curl_get(url)
    series = []
    unique_urls = []  # To check for duplicate URLs

    # Regex to extract all poster links and logos
    matches = re.findall(r'<div class="poster">.*?<a.*?href="(https:\/\/www\.dmax\.com\.tr\/[a-z0-9-]+)".*?<img src="(https:\/\/img-tlctv1\.mncdn\.com\/.*?)" alt=""', html, re.DOTALL)
    
    for match in matches:
        series_url = match[0]
        if series_url not in unique_urls:
            unique_urls.append(series_url)
            series.append({
                'url': series_url,
                'logo': match[1],
                'name': urlparse(series_url).path.split('/')[-1]  # Temporary name
            })
    return series

# Function to get season count
def get_season_count(url):
    html = curl_get(url)
    matches = re.findall(r'<option value="(\d+)">', html)
    return list(reversed(matches or []))  # Start from 1

# Function to get episode information
def get_episodes(base_url, season, series_name, logo, m3u8_content, result, log):
    episode_count = 0
    filename = 'dmax.m3u'
    
    for episode in range(1, 101):  # Check up to 100 episodes
        if series_name in result and season in result[series_name] and str(episode) in result[series_name][season]:
            continue

        episode_url = f"{base_url}/{season}-sezon-{episode}-bolum"
        episode_html = curl_get(episode_url)

        if 'video-player vod-player' in episode_html:
            code_match = re.search(r'data-video-code="(.*?)"', episode_html)
            if code_match:
                code = code_match.group(1)
                m3u8 = f"https://dygvideo.dygdigital.com/api/redirect?PublisherId=27&ReferenceId={code}&SecretKey=NtvApiSecret2014*&.m3u8"

                # M3U8 line
                m3u8_content.append(f'#EXTINF:-1 tvg-id="vod.tr" tvg-name="TR: {series_name} {season} Sezon {episode} Bölüm" tvg-logo="{logo}" group-title="DMAX BELGESELLER",TR: {series_name} {season} Sezon {episode} Bölüm')
                m3u8_content.append(m3u8)

                # Store results
                if series_name not in result:
                    result[series_name] = {}
                if season not in result[series_name]:
                    result[series_name][season] = {}
                result[series_name][season][str(episode)] = {
                    'code': code,
                    'm3u8': m3u8
                }

                # Write to M3U8 file incrementally
                os.makedirs('playlists', exist_ok=True)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(m3u8_content))

                episode_count += 1
        else:
            break  # No more episodes
    return episode_count, m3u8_content

# Function to write progress log
def write_log(message):
    log_file = 'playlists/progress.log'
    os.makedirs('playlists', exist_ok=True)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(message + '\n')

# Main process
def main():
    result = {}
    m3u8_content = ['#EXTM3U']
    log = ''

    # Initialize M3U8 file
    filename = 'dmax.m3u'
    os.makedirs('playlists', exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')

    series_list = get_series_list()
    total_series = len(series_list)
    write_log(f"Toplam {total_series} dizi bulundu.")

    for index, series in enumerate(series_list):
        base_url = series['url'].rstrip('/')
        main_html = curl_get(base_url)

        # Extract series name
        title_match = re.search(r'<title>(.*?)</title>', main_html)
        series_name = title_match.group(1) if title_match else urlparse(base_url).path.split('/')[-1]
        series_name = series_name.replace(' | DMAX', '')
        series['name'] = series_name

        # Log progress
        write_log(f"{index + 1}. dizi ({series_name}) çekiliyor...")

        # Get seasons
        seasons = get_season_count(base_url)
        result[series_name] = {}
        total_episodes = 0

        # Get episodes and add to M3U8
        for season in seasons:
            episode_count, m3u8_content = get_episodes(base_url, season, series_name, series['logo'], m3u8_content, result, log)
            total_episodes += episode_count

        # Series completed
        write_log(f"{series_name} tamamlandı, {total_episodes} bölüm bulundu.")

    write_log("Tüm diziler işlendi!")

if __name__ == "__main__":
    main()
