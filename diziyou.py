import requests
from bs4 import BeautifulSoup
import re
import time

BASE = "https://www.diziyou.one"
ARCHIVE = BASE + "/dizi-arsivi/page/{}"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.headers.update(HEADERS)

def get_soup(url):
    r = session.get(url, timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def is_active(url):
    try:
        r = session.head(url, timeout=10, allow_redirects=True)
        return r.status_code == 200
    except:
        return False

output = open("diziyou_tr.m3u8", "w", encoding="utf-8")
output.write("#EXTM3U\n\n")

total_series = 0

# 🔥 SADECE İLK SAYFA
for page in range(1, 2):
    print(f"\n[+] Arşiv sayfası: {page}")
    try:
        soup = get_soup(ARCHIVE.format(page))
    except Exception as e:
        print("  ! Sayfa alınamadı:", e)
        continue

    series_on_page = {}
    
    for a in soup.select('a[title][href]'):
        name = a.get("title").strip()
        link = a.get("href").rstrip("/")

        if link.startswith(BASE):
            img = a.find("img")
            logo = img["src"] if img else ""
            series_on_page[link] = (name, logo)

    print(f"  ➜ {page}. sayfada {len(series_on_page)} dizi bulundu.")
    total_series += len(series_on_page)

    for dizi_link, (name, logo) in series_on_page.items():
        print(f"  [Dizi] {name}")

        try:
            dsoup = get_soup(dizi_link)
        except:
            continue

        for ep_a in dsoup.select('a[href]'):
            ep_link = ep_a.get("href", "")
            if re.search(r'-\d+-sezon-\d+-bolum', ep_link):
                ep_link = ep_link.rstrip("/")

                m = re.search(r'-(\d+)-sezon-(\d+)-bolum', ep_link)
                if not m:
                    continue

                sezon, bolum = m.group(1), m.group(2)
                print(f"    [Bölüm] S{sezon}E{bolum}")

                try:
                    epsoup = get_soup(ep_link)
                except:
                    continue

                iframe = epsoup.find(id="diziyouPlayer")
                if not iframe:
                    continue

                player_url = iframe.get("src")
                if not player_url:
                    continue

                try:
                    psoup = get_soup(player_url)
                except:
                    continue

                source = psoup.find(id="diziyouSource")
                if not source:
                    continue

                m3u8 = source.get("src")
                if not m3u8:
                    continue

                tr_m3u8 = m3u8.replace("/play.m3u8", "_tr/play.m3u8")

                if is_active(tr_m3u8):
                    title_line = f"TR:{name} {sezon}. Sezon {bolum}. Bölüm"
                    extinf = (
                        f'#EXTINF:-1 tvg-id="" tvg-name="{title_line}" '
                        f'tvg-logo="{logo}" group-title="Diziyou-Panel",{title_line}\n'
                    )
                    output.write(extinf)
                    output.write(tr_m3u8 + "\n\n")
                    print("      ✅ TR bulundu")
                else:
                    print("      ❌ TR yok")

                time.sleep(0.3)

    time.sleep(1)

output.close()

print("\n==============================")
print(f"Toplam bulunan dizi sayısı: {total_series}")
print("Çıktı dosyası: diziyou_tr.m3u8")
print("==============================")
