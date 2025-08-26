import requests
from bs4 import BeautifulSoup
import re
import time
from requests.adapters import HTTPAdapter, Retry

BASE_URL = "https://www.showtv.com.tr"

# Session + retry ayarı
session = requests.Session()
retries = Retry(total=5, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

def get_soup(url):
    try:
        r = session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"[!] Hata: {e} -> {url}")
        return None

def scrape():
    m3u_lines = ["#EXTM3U"]

    # 1. Ana diziler sayfasını al
    soup = get_soup(f"{BASE_URL}/diziler")
    if not soup:
        print("[!] Ana sayfa alınamadı")
        return

    for a in soup.select("a[title]"):
        title = a.get("title")
        href = a.get("href")
        img_tag = a.find("img")

        if not href or not img_tag:
            continue
        if "/dizi/tanitim/" not in href:
            continue

        dizi_url = href if href.startswith("http") else BASE_URL + href
        logo_url = img_tag.get("src").split("(")[0].replace("[","").replace("]","")
        print(f"[+] Dizi bulundu: {title} -> {dizi_url}")

        # 2. Dizi tanıtım sayfasına gir
        dizi_soup = get_soup(dizi_url)
        if not dizi_soup:
            print(f"[!] Dizi sayfası alınamadı: {dizi_url}")
            continue

        for option in dizi_soup.select("option[data-href]"):
            bolum_href = option.get("data-href")
            bolum_name = option.text.strip()

            if not bolum_href:
                continue
            # Fragman veya galeri linklerini atla
            if "fragman" in bolum_href.lower() or "galeri" in bolum_href.lower():
                continue

            bolum_url = BASE_URL + bolum_href
            print(f"    [-] Bölüm: {bolum_name} -> {bolum_url}")

            # 3. Bölüm sayfasına girip m3u8 çek
            bolum_soup = get_soup(bolum_url)
            if not bolum_soup:
                print(f"[!] Bölüm alınamadı, atlanıyor: {bolum_url}")
                continue

            matches = re.findall(r'https:\\/\\/vmcdn\.ciner\.com\.tr[^"]+\.m3u8', str(bolum_soup))

            for raw in matches:
                m3u8_url = raw.replace("\\/", "/")
                line = f'#EXTINF:-1 tvg-id="vod.tr" tvg-name="TR: {title} {bolum_name}" tvg-logo="{logo_url}" group-title="SHOWTV DIZILER",TR: {title} {bolum_name}\n{m3u8_url}'
                m3u_lines.append(line)

            # Yavaş çekmek için 1-2 saniye bekle
            time.sleep(2)

    with open("showtv.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))

if __name__ == "__main__":
    scrape()
