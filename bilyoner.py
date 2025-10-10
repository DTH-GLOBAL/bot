import requests
from bs4 import BeautifulSoup
import sys

def find_active_domain():
    """1'den 199'a kadar domain'leri test et, aktif olanı bul."""
    for i in range(1, 200):
        domain = f"bilyonersport{i}.com"
        url = f"https://{domain}/"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"Aktif domain bulundu: {domain}")
                return domain, url
        except Exception as e:
            print(f"{domain} hatası: {e}", file=sys.stderr)
            continue
    return None, None

def extract_channels(base_url):
    """Sayfa kaynağından kanalları çıkar."""
    try:
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        channel_div = soup.find('div', id='channelList')
        if not channel_div:
            print("Kanal listesi bulunamadı!", file=sys.stderr)
            return []

        channels = []
        for a_tag in channel_div.find_all('a', class_='channel-item'):
            name_div = a_tag.find('div', class_='channel-name')
            if name_div:
                name = name_div.get_text(strip=True)
                href = a_tag.get('href')
                if name and href:
                    channels.append((name, href))
        print(f"{len(channels)} kanal çıkarıldı.")
        return channels
    except Exception as e:
        print(f"Çıkarma hatası: {e}", file=sys.stderr)
        return []

def generate_m3u(channels, output_file='bilyoner.m3u'):
    """M3U dosyasını üret."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for name, url in channels:
            f.write(f'#EXTINF:-1 tvg-name="{name}",{name}\n')
            f.write(f'{url}\n')
    print(f"M3U dosyası kaydedildi: {output_file}")

if __name__ == "__main__":
    active_domain, base_url = find_active_domain()
    if not active_domain:
        print("Aktif domain bulunamadı! Çıkılıyor.", file=sys.stderr)
        sys.exit(1)
    
    channels = extract_channels(base_url)
    if channels:
        generate_m3u(channels)
    else:
        print("Kanal bulunamadı!", file=sys.stderr)
        sys.exit(1)
