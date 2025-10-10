import requests
import re
import os
import sys
from datetime import datetime

def aktif_domain_bul():
    print("🔄 Aktif domain aranıyor...")
    for i in range(1, 50):
        domain = f"https://bilyonersport{i}.com/"
        try:
            print(f"🔍 Denenen domain: {domain}")
            r = requests.get(domain, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            print(f"📡 HTTP Status: {r.status_code}")
            
            if r.status_code == 200:
                if "channel-list" in r.text or "index.m3u8" in r.text:
                    print(f"✅ Aktif domain bulundu: {domain}")
                    return domain
                else:
                    print("❌ channel-list veya m3u8 bulunamadı")
            else:
                print(f"❌ HTTP {r.status_code}")
                
        except Exception as e:
            print(f"❌ Hata: {e}")
            continue
            
    print("❌ Hiçbir domain çalışmıyor")
    return None

def kanallari_cek(domain):
    print(f"🔍 Kanallar çekiliyor: {domain}")
    try:
        r = requests.get(domain, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        html = r.text
        print(f"📄 HTML uzunluğu: {len(html)} karakter")

        # Debug için HTML'nin bir kısmını göster
        if len(html) < 1000:
            print(f"📝 HTML Önizleme: {html[:500]}")
        else:
            print("📝 HTML çok uzun, kanallar aranıyor...")

        # Kanal isimlerini ve linklerini çek
        pattern = r'<div class="channel-name">(.*?)</div>.*?href="(.*?index\.m3u8.*?)"'
        matches = re.findall(pattern, html, re.DOTALL)
        
        print(f"🔍 Regex eşleşme sayısı: {len(matches)}")
        
        if matches:
            kanallar = []
            for name, url in matches:
                kanallar.append((name.strip(), url.strip()))
                print(f"📺 Kanal bulundu: {name.strip()}")
            return kanallar
        else:
            print("❌ Regex ile kanal bulunamadı, alternatif pattern deneniyor...")
            
            # Alternatif pattern
            names = re.findall(r'<div class="channel-name">(.*?)</div>', html)
            urls = re.findall(r'href="(.*?index\.m3u8.*?)"', html)
            
            print(f"📊 Alternatif - İsimler: {len(names)}, URL'ler: {len(urls)}")
            
            if names and urls and len(names) == len(urls):
                kanallar = []
                for name, url in zip(names, urls):
                    kanallar.append((name.strip(), url.strip()))
                    print(f"📺 Kanal bulundu: {name.strip()}")
                return kanallar
            else:
                print("❌ Alternatif pattern de çalışmadı")
                return []
                
    except Exception as e:
        print(f"❌ Kanal çekme hatası: {e}")
        return []

def m3u_olustur(kanallar, referer):
    filename = "bilyoner_kanallar.m3u"
    print(f"💾 M3U dosyası oluşturuluyor: {filename}")
    print(f"📊 Toplam kanal sayısı: {len(kanallar)}")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("#PLAYLIST:Bilyoner Sport Channels\n")
        f.write(f"#UPDATED:{datetime.now().strftime('%Y%m%d%H%M%S')}\n")
        f.write("#GITHUB:https://github.com/kullaniciadi/bilyoner-sport\n\n")
        
        for name, url in kanallar:
            f.write(f'#EXTINF:-1 tvg-name="{name}" group-title="BilyonerSport", {name}\n')
            f.write(f'{url}|Referer={referer}\n\n')

    print(f"✅ M3U dosyası oluşturuldu: {filename}")
    return filename

def readme_guncelle(kanal_sayisi, domain):
    print("📄 README.md güncelleniyor...")
    repo_name = "kullaniciadi/bilyoner-sport"  # Kendi reponla değiştir
    raw_url = f"https://raw.githubusercontent.com/{repo_name}/main/bilyoner_kanallar.m3u"
    
    readme_content = f"""# 📺 Bilyoner Sport IPTV Playlist

![GitHub last commit](https://img.shields.io/github/last-commit/{repo_name})
![Kanallar](https://img.shields.io/badge/Kanallar-{kanal_sayisi}-blue)
![Otomatik Güncelleme](https://img.shields.io/badge/Güncelleme-5_Dakika-green)

## 🚀 Otomatik Bilyoner Sport Playlist

Bu repository, Bilyoner Sport kanallarını otomatik olarak çekerek M3U playlist oluşturur.

### 📊 Bilgiler
- **Son Güncelleme:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
- **Aktif Domain:** `{domain}`
- **Kanal Sayısı:** {kanal_sayisi}
- **Güncelleme Sıklığı:** 5 Dakika

### 📥 Playlist Linki
