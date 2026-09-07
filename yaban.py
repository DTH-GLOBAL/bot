import requests
import re

SOURCE_URL = "https://ginikoturkish.com/xml/secure/plist.php?ch=761"

headers = {
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(SOURCE_URL, headers=headers, timeout=15)
r.raise_for_status()

source = r.text

# token değerini bul
match = re.search(
    r'https://trn03\.tulix\.tv/gt-yabantv/index\.m3u8\?token=([^"\'&\s<]+)',
    source
)

if not match:
    print("Token bulunamadı.")
    print(source[:2000])
    raise SystemExit

token = match.group(1)

stream_url = f"https://trn03.tulix.tv/gt-yabantv/index.m3u8?token={token}"

content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25
{stream_url}
"""

with open("yaban.m3u8", "w", encoding="utf-8") as f:
    f.write(content)

print("Token:", token)
print("Oluşturuldu: yaban.m3u8")
print(stream_url)
