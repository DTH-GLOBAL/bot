
import requests
import re
import urllib3
import warnings
import os

# --- CONFIGURATION ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}
TIMEOUT_VAL = 15
PROXY_URL = "https://seep.eu.org/" 
OUTPUT_FILENAME = "selcuk.m3u"
STATIC_LOGO_URL = "https://i.hizliresim.com/8xzjgqv.jpg"

# Channel ID to Name Mapping
SELCUK_NAMES = {
    "selcukbeinsports1": "beIN Sports 1",
    "selcukbeinsports2": "beIN Sports 2",
    "selcukbeinsports3": "beIN Sports 3",
    "selcukbeinsports4": "beIN Sports 4",
    "selcukbeinsports5": "beIN Sports 5",
    "selcukbeinsportsmax1": "beIN Sports Max 1",
    "selcukbeinsportsmax2": "beIN Sports Max 2",
    "selcukssport": "S Sport 1",
    "selcukssport2": "S Sport 2",
    "selcuksmartspor": "Smart Spor 1",
    "selcuksmartspor2": "Smart Spor 2",
    "selcuktivibuspor1": "Tivibu Spor 1",
    "selcuktivibuspor2": "Tivibu Spor 2",
    "selcuktivibuspor3": "Tivibu Spor 3",
    "selcuktivibuspor4": "Tivibu Spor 4",
    "sssplus1": "S Sport 1",
    "sssplus2": "S Sport 2",
    "selcuktabiispor1": "Tabii Spor 1",
    "selcuktabiispor2": "Tabii Spor 2",
    "selcuktabiispor3": "Tabii Spor 3",
    "selcuktabiispor4": "Tabii Spor 4",
    "selcuktabiispor5": "Tabii Spor 5"
}

def get_html_proxy(url, use_proxy=True):
    target_url = url
    if use_proxy and not url.startswith(PROXY_URL):
        target_url = PROXY_URL + url
    
    try:
        r = requests.get(target_url, headers=HEADERS, timeout=TIMEOUT_VAL, verify=False)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return None

def fetch_selcuk():
    print("--- 📡 Scanning Selcuk Sports ---")
    
    # 1. Get Main Page
    start_url = "https://www.selcuksportshd.is/"
    html = get_html_proxy(start_url, use_proxy=True)

    if not html:
        print("❌ Failed to reach main page.")
        return []

    # 2. Find Active Domain
    active_domain = ""
    section_match = re.search(r'data-device-mobile[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
    if section_match:
        link_match = re.search(r'href=["\'](https?://[^"\']*selcuksportshd[^"\']+)["\']', section_match.group(1))
        if link_match:
            active_domain = link_match.group(1).strip()
            if active_domain.endswith('/'): active_domain = active_domain[:-1]
    
    if not active_domain:
        print("❌ Active domain not found.")
        return []
    
    print(f"✅ Active Domain: {active_domain}")

    # 3. Go to Active Domain
    domain_html = get_html_proxy(active_domain, use_proxy=True)
    if not domain_html:
        print("❌ Failed to reach active domain.")
        return []

    # 4. Find Player Links
    player_links = re.findall(r'data-url=["\'](https?://[^"\']+id=[^"\']+)["\']', domain_html)
    if not player_links:
        print("❌ No player links found.")
        return []

    results = []
    base_stream_url = ""

    # 5. Extract Base Stream URL
    for player_url in player_links:
        html_player = get_html_proxy(player_url, use_proxy=True)
        if html_player:
            stream_match = re.search(r'this\.baseStreamUrl\s*=\s*[\'"](https://[^\'"]+)[\'"]', html_player)
            if stream_match:
                base_stream_url = stream_match.group(1)
                if not base_stream_url.endswith('/'): base_stream_url += '/'
                print(f"🎯 Base Stream URL: {base_stream_url}")
                break
    
    if not base_stream_url:
        print("❌ Base stream URL not found.")
        return []

    # 6. Build M3U List
    for cid, proper_name in SELCUK_NAMES.items():
        stream_url = base_stream_url + cid + "/playlist.m3u8"
        channel_name = "TR: " + proper_name
        
        m3u_entry = f'#EXTINF:-1 tvg-logo="{STATIC_LOGO_URL}" group-title="TURKIYE DEATHLESS", {channel_name}\n{stream_url}'
        results.append(m3u_entry)

    print(f"✅ Prepared {len(results)} channels.")
    return results

def main():
    print("Starting process...")
    
    list_selcuk = fetch_selcuk() 

    if not list_selcuk:
        print("❌ No channels found. Exiting.")
        return

    dynamic_m3u_content = "#EXTM3U\n" + "\n".join(list_selcuk)
    
    try:
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write(dynamic_m3u_content)
        
        full_path = os.path.abspath(OUTPUT_FILENAME)
        print(f"\n🎉 SUCCESS: Playlist created!")
        print(f"💾 File: {OUTPUT_FILENAME}")
        print(f"📝 Total Channels: {len(list_selcuk)}")
        print(f"📍 Path: {full_path}")
        
    except IOError as e:
        print(f"\n❌ File save error: {e}")

if __name__ == "__main__":
    main()
