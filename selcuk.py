import requests
import re

def find_active_site(start=1829, end=1999):
    print("🔎 Domainler taranıyor...")
    headers = {"User-Agent": "Mozilla/5.0"}
    for i in range(start, end + 1):
        test_url = f"https://www.selcuksportshd{i}.xyz/"
        try:
            r = requests.head(test_url, headers=headers, timeout=5)
            if r.status_code == 200:
                print(f"✅ Aktif site bulundu: {test_url}")
                return test_url
        except:
            continue
    return None

def get_base_url(active_site):
    try:
        source = requests.get(active_site, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).text
    except:
        return None
    match = re.search(r'https:\/\/[^"]+\/index\.php\?id=selcukbeinsports1', source)
    if not match:
        return None
    return match.group(0).replace("selcukbeinsports1", "")

def fetch_stream_url(url, channel_id):
    try:
        source = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).text
    except:
        return None

    # Tam m3u8 linkini ara
    match = re.search(r'(https:\/\/[^\'"]+\/live\/[^\'"]+\/playlist\.m3u8)', source)
    if match:
        return match.group(1)

    # Alternatif yöntem
    base_match = re.search(r'(https:\/\/[^\'"]+\/live\/)', source)
    if base_match:
        return f"{base_match.group(1)}{channel_id}/playlist.m3u8"

    return None

def build_m3u(base_url, channels):
    m3u_content = "#EXTM3U\n"
    for cid in channels:
        url = base_url + cid
        stream_url = fetch_stream_url(url, cid)
        if not stream_url:
            continue

        # Gereksiz ekleri temizle
        stream_url = re.sub(r"[\'\";].*$", "", stream_url).strip()

        channel_name = cid.replace("selcuk", "TR:").upper()
        m3u_content += (
            f'#EXTINF:-1 tvg-id="" tvg-name="{channel_name} HD" '
            f'tvg-logo="https://i.hizliresim.com/b6xqz10.jpg" '
            f'group-title="SPOR KANALLARI",{channel_name} HD\n'
        )
        m3u_content += f"{stream_url}\n"
    return m3u_content

if __name__ == "__main__":
    channels = [
        "selcukbeinsports1", "selcukbeinsports2", "selcukbeinsports3",
        "selcukbeinsports4", "selcukbeinsports5", "selcukbeinsportsmax1",
        "selcukbeinsportsmax2", "selcukssport", "selcukssport2",
        "selcuksmartspor", "selcuksmartspor2", "selcuktivibuspor1",
        "selcuktivibuspor2", "selcuktivibuspor3", "selcuktivibuspor4"
    ]

    active_site = find_active_site()
    if not active_site:
        print("❌ Hiçbir site aktif değil!")
        exit()

    base_url = get_base_url(active_site)
    if not base_url:
        print("❌ base_url bulunamadı!")
        exit()

    m3u_content = build_m3u(base_url, channels)

    # Çıktıyı selcuk.m3u olarak kaydediyoruz
    with open("selcuk.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print("✅ M3U dosyası oluşturuldu: selcuk.m3u")
