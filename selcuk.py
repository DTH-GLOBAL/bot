import requests
import re
import os

def find_working_selcuksportshd(start=1904, end=2050):
    print("🧭 Selcuksportshd domainleri taranıyor...")
    headers = {"User-Agent": "Mozilla/5.0"}
    for i in range(start, end + 1):
        url = f"https://www.selcuksportshd{i}.xyz/"
        print(f"🔍 Taranıyor: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200 and "uxsyplayer" in response.text:
                print(f"✅ Aktif domain bulundu: {url}")
                return response.text, url
        except:
            continue
    print("❌ Aktif domain bulunamadı.")
    return None, None

def find_dynamic_player_domain(page_html):
    match = re.search(r'https?://(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)', page_html)
    return f"https://{match.group(1)}" if match else None

def extract_base_stream_url(html):
    match = re.search(r'this\.baseStreamUrl\s*=\s*[\'"]([^\'"]+)', html)
    return match.group(1) if match else None

def build_m3u8_links(base_stream_url, channel_ids):
    return [(cid, f"{base_stream_url}{cid}/playlist.m3u8") for cid in channel_ids]

def write_m3u_file(m3u8_links, filename="Kanallar/kerim.m3u"):
    existing_extinf_lines = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for i in range(len(lines)):
                if lines[i].startswith("#EXTINF:-1"):
                    existing_extinf_lines.append(lines[i])

    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for i, (name, url) in enumerate(m3u8_links):
            if i < len(existing_extinf_lines):
                extinf = existing_extinf_lines[i]
            else:
                extinf = f"#EXTINF:-1,{name}\n"
            f.write(extinf)
            f.write("#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5)\n")
            f.write(f"{url}\n")
    print(f"✅ M3U dosyası güncellendi: {filename}")


# Kanal ID listesi
channel_ids = [
    "selcukbeinsports1",
    "selcukbeinsports2",
    "selcukbeinsports3",
    "selcukbeinsports4",
    "selcukbeinsports5",
    "selcukbeinsportsmax1",
    "selcukbeinsportsmax2",
    "selcukssport",
    "selcukssport2",
    "selcuksmartspor",
    "selcuksmartspor2",
    "selcuktivibuspor1",
    "selcuktivibuspor2",
    "selcuktivibuspor3",
    "selcuktivibuspor4",
    "selcukbeinsportshaber",
    "selcukaspor",
    "selcukeurosport1",
    "selcukeurosport2",
    "selcuksf1",
    "selcuktabiispor",
    "ssportplus1"
]

# Ana işlem
html, referer_url = find_working_selcuksportshd()
if html:
    stream_domain = find_dynamic_player_domain(html)
    if stream_domain:
        try:
            response = requests.get(f"{stream_domain}/index.php?id={channel_ids[0]}", headers={
                "User-Agent": "Mozilla/5.0"
            })
            base_url = extract_base_stream_url(response.text)
            if base_url:
                m3u_links = build_m3u8_links(base_url, channel_ids)
                write_m3u_file(m3u_links)
            else:
                print("❌ baseStreamUrl bulunamadı.")
        except Exception as e:
            print(f"⚠️ Hata oluştu: {e}")
    else:
        print("❌ Yayın domaini bulunamadı.")
else:
    print("⛔ Hiçbir domain çalışmıyor.")
