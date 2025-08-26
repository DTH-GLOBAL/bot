import requests
from bs4 import BeautifulSoup
import re
import json  # For potential JSON parsing if needed, but not used here

# Function to fetch and parse the main series page
def get_series_list():
    url = "https://www.showtv.com.tr/diziler"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {url}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    series = []
    
    # Find all swiper-slide divs in the swiper-wrapper
    swiper_wrapper = soup.find('div', class_='swiper-wrapper')
    if not swiper_wrapper:
        print("No swiper-wrapper found")
        return []
    
    for slide in swiper_wrapper.find_all('div', class_='swiper-slide'):
        a_tag = slide.find('a')
        if not a_tag:
            continue
        title = a_tag.get('title', '').strip()
        href = a_tag.get('href', '').strip()
        if not title or not href:
            continue
        # Full link
        full_href = "https://www.showtv.com.tr" + href if not href.startswith('http') else href
        
        img_tag = slide.find('img')
        logo = img_tag.get('src', '').strip() if img_tag else ''
        
        series.append({
            'name': title,
            'link': full_href,
            'logo': logo
        })
    
    return series

# Function to get episodes from a series page
def get_episodes(series_link):
    response = requests.get(series_link)
    if response.status_code != 200:
        print(f"Failed to fetch {series_link}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    episodes = []
    
    # Find the select with options for episodes
    select_tag = soup.find('select', id='episode-selector')  # Assuming it has this ID, adjust if needed
    if not select_tag:
        # Fallback: search for all <option> with data-href containing 'tum_bolumler'
        options = soup.find_all('option', attrs={'data-href': re.compile(r'/dizi/tum_bolumler/')})
    else:
        options = select_tag.find_all('option')
    
    for option in options:
        data_href = option.get('data-href', '').strip()
        if not data_href:
            continue
        # Extract season and episode from text or data-href
        episode_text = option.text.strip()  # e.g., "10. Bölüm"
        season_id = option.get('data-season-id', '').strip()
        
        # Parse episode number
        match = re.search(r'(\d+)\. Bölüm', episode_text)
        episode_num = match.group(1) if match else 'Unknown'
        
        # Full episode link
        full_episode_link = "https://www.showtv.com.tr" + data_href if not data_href.startswith('http') else data_href
        
        # Infer season from data-season-id or data-href
        href_match = re.search(r'sezon-(\d+)', data_href)
        season = href_match.group(1) if href_match else season_id
        
        episodes.append({
            'season': season,
            'episode': episode_num,
            'link': full_episode_link
        })
    
    return episodes

# Function to get m3u8 from episode page
def get_m3u8(episode_link):
    response = requests.get(episode_link)
    if response.status_code != 200:
        print(f"Failed to fetch {episode_link}")
        return None
    
    # Search for the pattern in the page source
    match = re.search(r'https:\/\/vmcdn\.ciner\.com\.tr\/ht\/.*?\/(.*?\.m3u8)', response.text)
    if match:
        m3u8_url = "https://vmcdn.ciner.com.tr/ht/" + match.group(0).split('/ht/')[-1]  # Reconstruct clean URL
        return m3u8_url.replace('\\', '')  # Remove escapes
    return None

# Main function to generate M3U
def generate_m3u():
    series_list = get_series_list()
    m3u_content = "#EXTM3U\n"
    
    for series in series_list:
        print(f"Processing series: {series['name']}")
        episodes = get_episodes(series['link'])
        
        for ep in episodes:
            m3u8 = get_m3u8(ep['link'])
            if not m3u8:
                continue
            
            title = f"TR: {series['name']} {ep['season']}. Sezon {ep['episode']}. Bölüm"
            m3u_content += f'#EXTINF:-1 tvg-id="vod.tr" tvg-name="{title}" tvg-logo="{series["logo"]}" group-title="SHOWTV DIZILER",{title}\n'
            m3u_content += f"{m3u8}\n"
    
    # Write to file
    with open('showtv_diziler.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    
    print("M3U file generated: showtv_diziler.m3u")

# Run the script
if __name__ == "__main__":
    generate_m3u()
