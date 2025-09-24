import cloudscraper
from bs4 import BeautifulSoup

# Video sayfası URL'si
url = "https://pornoanne.com/kizil-sacli-kadin-ask-acisini-unutmak-icin-amini-parcaliyor/"

# Cloudflare engelini aşmak için cloudscraper kullan
scraper = cloudscraper.create_scraper()  # requests benzeri API

html = scraper.get(url).text

# Parse et
soup = BeautifulSoup(html, "html.parser")

# Afiş resmi
og_image_tag = soup.find("meta", property="og:image")
image_url = og_image_tag["content"] if og_image_tag else None

# Video ismi
og_title_tag = soup.find("meta", property="og:image:alt")
video_title = og_title_tag["content"] if og_title_tag else None

# Resim dosyasından ID'yi al
video_id = image_url.split("/")[-1].split(".")[0] if image_url else None

# m3u8 linki oluştur
m3u8_link = f"https://cdnfast.sbs/playlists/{video_id}/playlist.m3u8" if video_id else None

print("Video Başlığı:", video_title)
print("Afiş Resmi:", image_url)
print("Video ID:", video_id)
print("M3U8 Linki:", m3u8_link)
