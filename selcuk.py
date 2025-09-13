import requests
import re
from pathlib import Path

# Çıkış dosyası
output_file = Path("selcuk.m3u")

m3u_content = "#EXTM3U\n"

# Ana site
entry_url = "https://www.selcuksportshd78.is/"

try:
    entry_source = requests.get(entry_url, timeout=10).text
except:
    exit()

# Aktif siteyi bul
match = re.search(r'url=(https://[^"]+)', entry_source)
if not match:
    exit()
active_site = match.group(1)

try:
    source = requests.get(active_site, timeout=10).text
except:
    exit()

iframe_match = re.search(r'https://[^"]+/index\.php\?id=selcukbeinsports1', source)
if not iframe_match:
    exit()

base_url = iframe_match.group(0).replace("selcukbeinsports1", "")

channels = [
    "selcukbeinsports1", "selcukbeinsports2", "selcukbeinsports3",
    "selcukbeinsports4", "selcukbeinsports5", "selcukbeinsportsmax1",
    "selcukbeinsportsmax2", "selcukssport", "selcukssport2",
    "selcuksmartspor", "selcuksmartspor2", "selcuktivibuspor1",
    "selcuktivibuspor2", "selcuktivibuspor3", "selcuktivibuspor4"
]

proxy_prefix = "https://plain-night-3215.aykara463.workers.dev/?url="

for id in channels:
    try:
        src = requests.get(base_url + id, timeout=10).text
    except:
        continue

    stream_url = None
    m = re.search(r'(https://[^\'"]+/live/[^\'"]+/playlist\.m3u8)', src)
    if m:
        stream_url = m.group(1)
    else:
        m2 = re.search(r'(https://[^\'"]+/live/)', src)
        if m2:
            stream_url = f"{m2.group(1)}{id}/playlist.m3u8"
        else:
            continue

    stream_url = stream_url.strip()
    if not stream_url.startswith("http"):
        continue

    channel_name = id.upper().replace("SELcuk".upper(), "TR:")

    m3u_content += f'#EXTINF:-1 tvg-id="" tvg-name="{channel_name} HD" tvg-logo="https://i.hizliresim.com/b6xqz10.jpg" group-title="TURKIYE DEATHLESS",{channel_name} HD\n'
    m3u_content += proxy_prefix + stream_url + "\n"

# Dosyayı kaydet
output_file.write_text(m3u_content, encoding="utf-8")
print("selcuk.m3u oluşturuldu!")
