import requests
import re
import urllib3
import warnings
import os

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}
TIMEOUT_VAL = 15
PROXY_URL = "https://seep.eu.org/"
OUTPUT_FILENAME = "kanallar.txt"

# Kanal listesi (İlk kodundaki isimler ve ID'ler)
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
    target_url = PROXY_URL + url
    try:
        r = requests.get(target_url, headers=HEADERS, timeout=TIMEOUT_VAL, verify=False)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Proxy Hatası: {e}")
        return None

def get_html_direct(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT_VAL, verify=False)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Bağlantı Hatası: {e}")
        return None

def find_player_base():
    print("--- 📡 Selcuk Sports Taranıyor ---")
    
    start_url = "https://www.selcuksportshd.is/"
    html = get_html_proxy(start_url)

    if not html:
        print("❌ Ana sayfaya ulaşılamadı.")
        return None

    active_domain = ""
    # İlk koddaki gelişmiş domain bulma mantığı
    section_match = re.search(r'data-device-mobile[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
    if section_match:
        link_match = re.search(r'href=["\'](https?://[^"\']*selcuksportshd[^"\']+)["\']', section_match.group(1))
        if link_match:
            active_domain = link_match.group(1).strip()
            if active_domain.endswith('/'): active_domain = active_domain[:-1]
    
    if not active_domain:
        print("❌ Aktif domain bulunamadı.")
        return None
    
    print(f"✅ Aktif Domain: {active_domain}")

    domain_html = get_html_direct(active_domain)
    if not domain_html:
        return None

    # Player linklerini (index.php?id=...) bul
    player_links = re.findall(r'data-url=["\'](https?://[^"\']+?id=[^"\']+?)["\']', domain_html)
    if not player_links:
        player_links = re.findall(r'href=["\'](https?://[^"\']+?index\.php\?id=[^"\']+?)["\']', domain_html)
    
    if not player_links:
        print("❌ Player linkleri bulunamadı.")
        return None

    # Base URL'i ilk linkten çıkaralım
    first_link = player_links[0]
    # Örn: https://xxx.com/index.php?id=selcukbeinsports1 -> https://xxx.com/index.php?id=
    base_player_url = first_link.split('id=')[0] + 'id='
    print(f"🎯 Base Player URL: {base_player_url}")
    
    return base_player_url

def main():
    base_player = find_player_base()
    
    if not base_player:
        print("⚠️ İşlem iptal edildi.")
        return

    output_lines = []
    output_lines.append("Kanal Player Linkleri:")
    output_lines.append("---------------------\n")

    for selcuk_id, display_name in SELCUK_NAMES.items():
        full_url = f"{base_player}{selcuk_id}"
        line = f"{display_name} HD: {full_url}"
        output_lines.append(line)
        print(f"Eklendi: {display_name}")

    try:
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines))
        
        print(f"\n✅ BAŞARILI: {OUTPUT_FILENAME} dosyası oluşturuldu!")
        print(f"📍 Konum: {os.path.abspath(OUTPUT_FILENAME)}")

    except IOError as e:
        print(f"\n❌ Dosya yazma hatası: {e}")

if __name__ == "__main__":
    main()
