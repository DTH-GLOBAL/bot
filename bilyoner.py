import requests, re, os

# 1️⃣ Aktif domaini bul
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

# 2️⃣ Kanal listesi çek
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

# 3️⃣ M3U dosyasını oluştur
def m3u_olustur(kanallar, referer):
    path = os.path.join("/sdcard", "bilyoner_kanallar.m3u")
    print(f"💾 M3U dosyası oluşturuluyor: {path}")

    with open(path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for name, url in kanallar:
            f.write(f'#EXTINF:-1 tvg-name="{name}" group-title="BilyonerSport", {name}\n')
            f.write(f'#EXTVLCOPT:http-referrer={referer}\n')
            f.write(f"{url}\n\n")

    print(f"✅ {len(kanallar)} kanal eklendi!")
    print(f"📁 Dosya kaydedildi: {path}")

# 🔄 Ana işlem
aktif = aktif_domain_bul()
if aktif:
    kanallar = kanallari_cek(aktif)
    if kanallar:
        m3u_olustur(kanallar, aktif)
    else:
        print("Kanal bulunamadı.")
else:
    print("Domain bulunamadı.")
