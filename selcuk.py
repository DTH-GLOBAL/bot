import requests
import re
import urllib3
import warnings
import os # Dosya işlemleri için

# --- AYARLAR ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}
TIMEOUT_VAL = 15
# Selçuk Sports'un ilk erişimini proxy ile sağlamak için (Gerekli olabileceği varsayılmıştır)
PROXY_URL = "https://seep.eu.org/" 
OUTPUT_FILENAME = "selcuk-sports-iptv.m3u"

# --- SABİT LOGO TANIMI ---
# İstenen sabit logo URL'si
SABIT_LOGO_URL = "https://i.hizliresim.com/8xzjgqv.jpg"

# LOGO_MAP sözlüğü artık kullanılmayacak (temizlendi/göz ardı edilecek)
LOGO_MAP = {}

# Selçuk ID'lerini Logo Haritasındaki isimlere çeviren sözlük
SELCUK_NAMES = {
    "selcukbeinsports1": "beIN Sports 1",
    "selcukbeinsports2": "beIN Sports 2",
    "selcukbeinsports3": "beIN Sports 3",
    "selcukbeinsports4": "beIN Sports 4",
    "selcukbeinsports5": "beIN Sports 5",
    "selcukbeinsportsmax1": "beIN Sports Max 1",
    "selcukbeinsportsmax2": "beIN Sports Max 2",
    "selcukssport": "S Sport 1",
    "selcukssport2": "S Sport 2",
    "selcuksmartspor": "Smart Spor 1",
    "selcuksmartspor2": "Smart Spor 2",
    "selcuktivibuspor1": "Tivibu Spor 1",
    "selcuktivibuspor2": "Tivibu Spor 2",
    "selcuktivibuspor3": "Tivibu Spor 3",
    "selcuktivibuspor4": "Tivibu Spor 4",
    "sssplus1": "S Sport 1",
    "sssplus2": "S Sport 2",
    "selcuktabiispor1": "Tabii Spor 1",
    "selcuktabiispor2": "Tabii Spor 2",
    "selcuktabiispor3": "Tabii Spor 3",
    "selcuktabiispor4": "Tabii Spor 4",
    "selcuktabiispor5": "Tabii Spor 5"
}

def get_logo(channel_name):
    """
    Kanal adına bakmaksızın tüm kanallar için sabit logo URL'sini döndürür.
    """
    # Sabit logoyu döndürüyoruz
    return SABIT_LOGO_URL

# --- PROXY İLE HTML ÇEKME ---
def get_html_proxy(url, use_proxy=True):
    """
    Belirtilen URL'den HTML içeriğini çeker, isteğe bağlı olarak PROXY_URL üzerinden.
    """
    target_url = url
    if use_proxy and not url.startswith(PROXY_URL):
        target_url = PROXY_URL + url
    
    try:
        r = requests.get(target_url, headers=HEADERS, timeout=TIMEOUT_VAL, verify=False)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"❌ Hata ({url}): {e}")
        return None

# --- SELÇUK TARAMA ---
def fetch_selcuk():
    """
    Selçuk Sports sitesinden aktif M3U8 akışlarını çeker ve M3U formatında döndürür.
    """
    print("--- 📡 Selçuk Sports Taranıyor ---")
    
    # 1. Ana sayfayı Proxy ile bul
    start_url = "https://www.selcuksportshd.is/"
    html = get_html_proxy(start_url, use_proxy=True)

    if not html:
        print("❌ Ana sayfaya ulaşılamadı. İşlem iptal edildi.")
        return []

    # 2. Aktif domaini bul (Sitenin güncel adresi)
    active_domain = ""
    # Data-device-mobile içerisindeki Selcuksportshd linkini arar
    section_match = re.search(r'data-device-mobile[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
    if section_match:
        link_match = re.search(r'href=["\'](https?://[^"\']*selcuksportshd[^"\']+)["\']', section_match.group(1))
        if link_match:
            active_domain = link_match.group(1).strip()
            if active_domain.endswith('/'): active_domain = active_domain[:-1]
    
    if not active_domain:
        print("❌ Aktif domain bulunamadı. İşlem iptal edildi.")
        return []
    
    print(f"✅ Aktif Domain: {active_domain}")

    # 3. Aktif Domain sayfasına git
    # Domain'e de proxy ile gitmek gerekebilir
    domain_html = get_html_proxy(active_domain, use_proxy=True)
    if not domain_html:
        print("❌ Domain sayfasına girilemedi. İşlem iptal edildi.")
        return []

    # 4. Player linklerini bul (İçlerinde 'id=' parametresi olan linkler)
    player_links = re.findall(r'data-url=["\'](https?://[^"\']+id=[^"\']+)["\']', domain_html)
    if not player_links:
        print("❌ Player linkleri bulunamadı. İşlem iptal edildi.")
        return []

    results = []
    base_stream_url = ""

    # 5. Base URL'i çek (M3U8 akışlarının temel adresini bulmak için)
    # Birden fazla player linki olabilir, birinden base URL'i çekmek yeterlidir.
    for player_url in player_links:
        html_player = get_html_proxy(player_url, use_proxy=True)
        if html_player:
            # JavaScript kodu içerisindeki this.baseStreamUrl değişkenini arar
            stream_match = re.search(r'this\.baseStreamUrl\s*=\s*[\'"](https://[^\'"]+)[\'"]', html_player)
            if stream_match:
                base_stream_url = stream_match.group(1)
                if not base_stream_url.endswith('/'): base_stream_url += '/'
                print(f"🎯 Yayın URL Tabanı: {base_stream_url}")
                break
    
    if not base_stream_url:
        print("❌ Yayın taban URL'si bulunamadı. İşlem iptal edildi.")
        return []

    # 6. M3U listesini oluştur
    for cid, proper_name in SELCUK_NAMES.items():
        # Yayın URL'sini oluştur: BaseURL + Selcuk_ID + /playlist.m3u8
        stream_url = base_stream_url + cid + "/playlist.m3u8"
        
        channel_name = "TR: " + proper_name
        
        # Logoyu çek (Artık SABIT_LOGO_URL döndürecek)
        logo = get_logo(proper_name)
        
        # M3U formatında satırı ekle
        m3u_entry = f'#EXTINF:-1 tvg-logo="{logo}" group-title="TURKIYE DEATHLESS", {channel_name}\n{stream_url}'
        results.append(m3u_entry)

    print(f"✅ Selçuk Sports'tan toplam {len(results)} kanal akışı hazırlandı.")
    return results

# --- ANA FONKSIYON ---
def main():
    print("Kanallar taranıyor...")
    
    # Sadece Selçuk Listesini çek
    list_selcuk = fetch_selcuk() 

    if not list_selcuk:
        print("❌ Herhangi bir Selçuk Sports kanalı bulunamadı. Çıkış yapılıyor.")
        return

    # M3U içeriğini oluştur: Başlık satırı ve kanal listesi
    dynamic_m3u_content = "#EXTM3U\n" + "\n".join(list_selcuk)
    
    # Dosyaya kaydet
    try:
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write(dynamic_m3u_content)
        
        # Çalışma dizinindeki tam yolu göster
        full_path = os.path.abspath(OUTPUT_FILENAME)
        print(f"\n🎉 BAŞARILI: Yalnızca Selçuk Sports kanallarını içeren dosya oluşturuldu!")
        print(f"💾 Dosya Adı: {OUTPUT_FILENAME}")
        print(f"📝 Toplam Kanal: {len(list_selcuk)}")
        print(f"📍 Konum: {full_path}")
        
    except IOError as e:
        print(f"\n❌ Dosya kaydetme hatası: {e}")

if __name__ == "__main__":
    main()
