import requests
from bs4 import BeautifulSoup
import time

# 1️⃣ Aktif domaini bul
def aktif_domain_bul():
    for i in range(1, 200):
        domain = f"https://bilyonersport{i}.com/"
        try:
            r = requests.get(domain, timeout=3)
            if r.status_code == 200:
                print(f"[+] Aktif domain bulundu: {domain}")
                return domain
        except requests.RequestException:
            continue
    return None

# 2️⃣ Kanalları çek ve M3U dosyası oluştur
def kanal_listesi_cek(domain):
    r = requests.get(domain)
    soup = BeautifulSoup(r.text, "html.parser")
    kanal_divs = soup.select(".channel-list .channel-item")
    m3u_lines = ["#EXTM3U"]
    
    for kanal in kanal_divs:
        isim_tag = kanal.select_one(".channel-name")
        kanal_ad = isim_tag.text.strip() if isim_tag else "Bilinmeyen Kanal"
        url = kanal.get("href")
        if url:
            # Referrer header için ekleme
            m3u_lines.append(f'#EXTINF:-1,{kanal_ad}')
            m3u_lines.append(f'{url} | referer={domain}')
    
    with open("bilyoner.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
    print("[+] M3U dosyası oluşturuldu: bilyoner.m3u")

if __name__ == "__main__":
    domain = aktif_domain_bul()
    if domain:
        kanal_listesi_cek(domain)
    else:
        print("[-] Aktif domain bulunamadı!")
