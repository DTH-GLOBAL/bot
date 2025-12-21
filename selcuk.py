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

# Channel Map (ID -> Display Name)
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
    "sssplus1": "S Sport Plus 1",
    "sssplus2": "S Sport Plus 2",
    "selcuktabiispor1": "Tabii Spor 1",
    "selcuktabiispor2": "Tabii Spor 2",
    "selcuktabiispor3": "Tabii Spor 3",
    "selcuktabiispor4": "Tabii Spor 4",
    "selcuktabiispor5": "Tabii Spor 5"
}

def get_html_proxy(url):
    """Fetches HTML via Proxy (for blocked main pages)"""
    target_url = PROXY_URL + url
    try:
        r = requests.get(target_url, headers=HEADERS, timeout=TIMEOUT_VAL, verify=False)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Proxy Error: {e}")
        return None

def get_html_direct(url):
    """Fetches HTML directly (for player pages usually accessible)"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT_VAL, verify=False)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Direct Error: {e}")
        return None

def find_base_url():
    """Locates the dynamic base stream URL using robust regex patterns."""
    print("--- 📡 Scanning Selcuk Sports ---")
    
    # 1. Main Page (via Proxy)
    start_url = "https://www.selcuksportshd.is/"
    html = get_html_proxy(start_url)

    if not html:
        print("❌ Failed to reach main page.")
        return None

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
        return None
    
    print(f"✅ Active Domain: {active_domain}")

    # 3. Visit Domain (Direct)
    domain_html = get_html_direct(active_domain)
    if not domain_html:
        return None

    # 4. Find Player Links
    player_links = re.findall(r'data-url=["\'](https?://[^"\']+?id=[^"\']+?)["\']', domain_html)
    if not player_links:
        # Fallback regex
        player_links = re.findall(r'href=["\'](https?://[^"\']+?index\.php\?id=[^"\']+?)["\']', domain_html)
    
    if not player_links:
        print("❌ No player links found.")
        return None

    base_stream_url = ""

    # 5. Extract Base URL from Players
    # Patterns to look for in JS
    patterns = [
        r'this\.baseStreamUrl\s*=\s*[\'"](https://[^\'"]+)[\'"]',
        r'const baseStreamUrl\s*=\s*[\'"](https://[^\'"]+)[\'"]',
        r'baseStreamUrl\s*:\s*[\'"](https://[^\'"]+)[\'"]',
        r'streamUrl\s*=\s*[\'"](https://[^\'"]+)[\'"]'
    ]

    for player_url in player_links:
        # print(f"🔍 Checking player: {player_url}") # Optional verbose log
        html_player = get_html_direct(player_url)
        if html_player:
            for pattern in patterns:
                stream_match = re.search(pattern, html_player)
                if stream_match:
                    base_stream_url = stream_match.group(1)
                    # Normalize URL to end with 'live/'
                    if 'live/' in base_stream_url:
                        base_stream_url = base_stream_url.split('live/')[0] + 'live/'
                    print(f"🎯 Base Stream URL Found: {base_stream_url}")
                    break
            if base_stream_url:
                break
    
    if not base_stream_url:
        print("❌ Base stream URL not found in any player.")
        return None

    # Ensure URL formatting
    if not base_stream_url.endswith('/'):
        base_stream_url += '/'
    if 'live/' not in base_stream_url:
        base_stream_url = base_stream_url.rstrip('/') + '/live/'

    return base_stream_url

def main():
    print("Starting process...")
    
    # Find the dynamic base URL
    base_url = find_base_url()
    
    if not base_url:
        print("⚠️ Process aborted due to missing URL.")
        return

    # Prepare M3U content
    m3u_lines = ["#EXTM3U"]
    
    print(f"⚡ Generating playlist...")

    for selcuk_id, display_name in SELCUK_NAMES.items():
        # Standard link generation
        stream_url = f"{base_url}{selcuk_id}/playlist.m3u8"
        
        # M3U Entry format
        # group-title ensures they are grouped nicely in players
        entry = f'#EXTINF:-1 tvg-logo="{STATIC_LOGO_URL}" group-title="TURKIYE DEATHLESS", {display_name}\n{stream_url}'
        m3u_lines.append(entry)

    # Write to single file
    try:
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
        
        full_path = os.path.abspath(OUTPUT_FILENAME)
        print(f"\n✅ SUCCESS: Playlist created successfully!")
        print(f"💾 File: {OUTPUT_FILENAME}")
        print(f"📝 Total Channels: {len(SELCUK_NAMES)}")
        print(f"📍 Path: {full_path}")

    except IOError as e:
        print(f"\n❌ File write error: {e}")

if __name__ == "__main__":
    main()
