import requests
from bs4 import BeautifulSoup
import re
import time

# Base URL
base_url = "https://www.showtv.com.tr"

# Headers to mimic a browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Function to get all series from the main page
def get_series():
    print("Fetching series list from:", base_url + "/diziler")
    try:
        response = requests.get(f"{base_url}/diziler", headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        series_list = []
        swiper_wrapper = soup.find('div', class_='swiper-wrapper')
        if swiper_wrapper:
            slides = swiper_wrapper.find_all('div', class_='swiper-slide')
            for slide in slides:
                a_tag = slide.find('a')
                if a_tag:
                    relative_href = a_tag['href']
                    full_link = base_url + relative_href if relative_href.startswith('/') else relative_href
                    name = a_tag['title']
                    img_tag = slide.find('img')
                    logo = img_tag['src'] if img_tag else ''
                    logo = re.sub(r'\?v=\d+', '', logo)
                    series_list.append({
                        'name': name,
                        'logo': logo,
                        'link': full_link
                    })
                    print(f"Found series: {name} ({full_link})")
        
        print(f"Total series found: {len(series_list)}")
        return series_list
    except Exception as e:
        print(f"Error fetching series list: {e}")
        return []

# Function to get episodes for a series
def get_episodes(series_link):
    print(f"Fetching episodes for: {series_link}")
    try:
        response = requests.get(series_link, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        episodes = []
        options = soup.find_all('option', {'data-href': True, 'data-season-id': True})
        for option in options:
            relative_href = option['data-href']
            full_episode_link = base_url + relative_href if relative_href.startswith('/') else relative_href
            season_id = option['data-season-id']
            episode_text = option.text.strip()
            episode_num = re.search(r'(\d+)\.', episode_text).group(1) if re.search(r'(\d+)\.', episode_text) else ''
            episodes.append({
                'season': season_id,
                'episode': episode_num,
                'link': full_episode_link
            })
            print(f"Found episode: Season {season_id}, Episode {episode_num} ({full_episode_link})")
        
        print(f"Total episodes found for this series: {len(episodes)}")
        return episodes
    except Exception as e:
        print(f"Error fetching episodes for {series_link}: {e}")
        return []

# Function to get m3u8 from episode page
def get_m3u8(episode_link):
    print(f"Fetching m3u8 for: {episode_link}")
    try:
        response = requests.get(episode_link, headers=headers, timeout=10)
        response.raise_for_status()
        text = response.text
        
        # Try multiple regex patterns to find m3u8
        m3u8_matches = re.findall(r'https?://[^\s\'"]+\.m3u8', text)
        if not m3u8_matches:
            # Try searching for escaped URLs
            m3u8_matches = re.findall(r'https?\\:\\/\\/[^\s\'"]+\\.m3u8', text)
        
        if m3u8_matches:
            m3u8_url = m3u8_matches[0].replace('\\', '')
            print(f"Found m3u8: {m3u8_url}")
            return m3u8_url
        
        print("No m3u8 found for this episode. Page content sample:")
        print(text[:500])  # Log first 500 chars for debugging
        return None
    except Exception as e:
        print(f"Error fetching m3u8 for {episode_link}: {e}")
        return None

# Main function to generate M3U
def generate_m3u():
    print("Starting M3U generation...")
    series = get_series()
    m3u_content = "#EXTM3U\n"
    
    for ser in series:
        print(f"\nProcessing series: {ser['name']}")
        episodes = get_episodes(ser['link'])
        for ep in episodes:
            time.sleep(1)  # Add delay to avoid rate-limiting
            m3u8 = get_m3u8(ep['link'])
            if m3u8:
                title = f"TR: {ser['name']} {ep['season']}. Sezon {ep['episode']}. Bölüm"
                m3u_content += f'#EXTINF:-1 tvg-id="vod.tr" tvg-name="{title}" tvg-logo="{ser["logo"]}" group-title="SHOWTV DIZILER",{title}\n'
                m3u_content += f"{m3u8}\n"
                print(f"Added to M3U: {title}")
    
    with open('showtv_diziler.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    
    print("\nM3U file generated: showtv_diziler.m3u")

# Run the script
if __name__ == "__main__":
    generate_m3u()
