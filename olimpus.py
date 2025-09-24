import cloudscraper
import re
from bs4 import BeautifulSoup

# Video sayfası URL'si
url = "https://pornoanne.com/bdsm-seven-hatuna-acimadi/"

# Cloudflare engelini aşmak için scraper
scraper = cloudscraper.create_scraper()
html = scraper.get(url).text

# Parse et
soup = BeautifulSoup(html, "html.parser")

# Afiş resmi
og_image_tag = soup.find("meta", property="og:image")
image_url = og_image_tag["content"] if og_image_tag else None

# Video başlığı
og_title_tag = soup.find("meta", property="og:image:alt")
video_title = og_title_tag["content"] if og_title_tag else None

# Video ID veya m3u8 linkini <script> içinde ara
m3u8_match = re.search(r'https://cdnfast\.sbs/playlists/([a-z0-9]+)/playlist\.m3u8', html)
if m3u8_match:
    video_id = m3u8_match.group(1)
    m3u8_link = f"https://cdnfast.sbs/playlists/{video_id}/playlist.m3u8"
else:
    video_id = None
    m3u8_link = None

# Sonuçları yazdır
print("Video Başlığı:", video_title)
print("Afiş Resmi:", image_url)
print("Video ID:", video_id)
print("M3U8 Linki:", m3u8_link)
