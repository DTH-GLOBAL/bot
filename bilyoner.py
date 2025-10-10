import requests
import re
import os
import sys
from datetime import datetime

def aktif_domain_bul():
    for i in range(1, 200):
        domain = f"https://bilyonersport{i}.com/"
        try:
            r = requests.get(domain, timeout=3)
            if r.status_code == 200 and "channel-list" in r.text:
                print(f"✅ Aktif domain bulundu: {domain}")
                return domain
        except:
            pass
    print("❌ Aktif domain bulunamadı.")
    return None

def kanallari_cek(domain):
    print("🔍 Kanal listesi çekiliyor...")
    r = requests.get(domain, timeout=5)
    html = r.text

    # Esnek regex - domain sabit değil!
    hrefs = re.findall(r'href="([^"]+index\.m3u8[^"]*)"', html)
    names = re.findall(r'<div class="channel-name">(.*?)</div>', html)

    if not hrefs or not names:
        print("⚠️ Kanal listesi bulunamadı.")
        return []

    kanallar = []
    for name, link in zip(names, hrefs):
        name = name.strip()
        link = link.strip()
        kanallar.append((name, link))
    return kanallar

def m3u_olustur(kanallar, referer):
    filename = "bilyoner_kanallar.m3u"
    print(f"💾 M3U dosyası oluşturuluyor: {filename}")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("#PLAYLIST:Bilyoner Sport Channels\n")
        f.write(f"#UPDATED:{datetime.now().strftime('%Y%m%d%H%M%S')}\n")
        f.write("#GITHUB:https://github.com/kullaniciadi/bilyoner-sport\n\n")
        
        for name, url in kanallar:
            f.write(f'#EXTINF:-1 tvg-name="{name}" group-title="BilyonerSport", {name}\n')
            f.write(f'#EXTVLCOPT:http-referrer={referer}\n')
            f.write(f"{url}\n\n")

    print(f"✅ {len(kanallar)} kanal eklendi!")
    print(f"📁 Dosya kaydedildi: {filename}")
    return filename

def readme_guncelle(kanal_sayisi, domain):
    readme_content = f"""# 📺 Bilyoner Sport IPTV Playlist

![GitHub last commit](https://img.shields.io/github/last-commit/kullaniciadi/bilyoner-sport)
![Kanallar](https://img.shields.io/badge/Kanallar-{kanal_sayisi}-blue)
![Otomatik Güncelleme](https://img.shields.io/badge/Güncelleme-5 Dakika-green)

## 🚀 Otomatik Bilyoner Sport Playlist

Bu repository, Bilyoner Sport kanallarını otomatik olarak çekerek M3U playlist oluşturur.

### 📊 Bilgiler
- **Son Güncelleme:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
- **Aktif Domain:** `{domain}`
- **Kanal Sayısı:** {kanal_sayisi}
- **Güncelleme Sıklığı:** 5 Dakika

### 📥 Playlist Linki
