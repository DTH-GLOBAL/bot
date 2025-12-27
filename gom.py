import requests
import re
import base64
import string
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": "https://play.dizigom104.com/"
}

# TARANACAK KATEGORİ SAYFALARI BURADA SABİT
TARGET_PAGES = [
    "https://dizigom104.com/dc-comics-dizileri-hd1/",
    "https://dizigom104.com/dc-comics-dizileri-hd1/page/2/"
]

def check_link_is_active(url):
    """Linkin aktif olup olmadığını (200 OK) kontrol eder."""
    try:
        r = requests.head(url, headers=HEADERS, timeout=1.5, allow_redirects=True)
        return r.status_code == 200
    except:
        return False

def get_m3u8_link(embed_url):
    """Embed içinden video hash'ini alır ve brute-force ile m3u8 bulur."""
    try:
        r = requests.get(embed_url, headers=HEADERS, timeout=10)
        m2 = re.search(r"eval\(function\(p,a,c,k,e,d\).*?\('(.+?)'\.split\('\|'\)", r.text, re.S)
        if not m2: return None

        parts = m2.group(1).split("|")
        video_hash = next(p for p in parts if re.fullmatch(r"[a-f0-9]{32}", p))
        
        letters = string.ascii_lowercase
        for char in letters:
            for num in ["1", "2"]:
                prefix = f"{char}{num}"
                test_url = f"https://{prefix}.df856-54hilsnz.xyz/storage/media/{video_hash}-720.mp4/gomindex.m3u8"
                if check_link_is_active(test_url):
                    return test_url
        return None
    except:
        return None

def get_embed_from_episode(episode_url):
    """Bölüm sayfasındaki karmaşık yapıyı çözüp embed linkini döner."""
    try:
        r = requests.get(episode_url, headers=HEADERS, timeout=10)
        pattern = r'eval\(function\(h,u,n,t,e,r\).*?\("(.*?)",(\d+),"(.*?)",(\d+),(\d+),(\d+)\)'
        match = re.search(pattern, r.text)
        if not match: return None

        h_data, u_val, n_data, t_val, e_val, r_val = match.groups()
        u_val, t_val, e_val, r_val = int(u_val), int(t_val), int(e_val), int(r_val)
        
        def _0xe2c(d, e, f):
            g = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/"
            h, i = g[0:e], g[0:f]
            j = 0
            for idx, char in enumerate(d[::-1]):
                if char in h: j += h.find(char) * (e ** idx)
            k = ""
            while j > 0:
                k = i[j % f] + k
                j = (j - (j % f)) // f
            return k or "0"

        decoded_js = ""
        idx_i = 0
        while idx_i < len(h_data):
            s = ""
            while idx_i < len(h_data) and h_data[idx_i] != n_data[e_val]:
                s += h_data[idx_i]
                idx_i += 1
            for j in range(len(n_data)): s = s.replace(n_data[j], str(j))
            if s: decoded_js += chr(int(_0xe2c(s, e_val, 10)) - t_val)
            idx_i += 1
        
        api_path_match = re.search(r'/(api/watch/.*?\.dizigom)', decoded_js)
        if not api_path_match: return None
        
        api_res = requests.get("https://dizigom104.com/" + api_path_match.group(1), headers=HEADERS)
        final_html = base64.b64decode(api_res.text).decode('utf-8')
        embed_match = re.search(r'src=["\'](https?://.*?)["\']', final_html)
        return embed_match.group(1) if embed_match else None
    except:
        return None

def main():
    m3u_filename = "dizigom-dc.m3u"
    print(f"Bot başlatıldı, '{m3u_filename}' dosyası oluşturuluyor...")
    
    with open(m3u_filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for cat_url in TARGET_PAGES:
            print(f"\n--- Tarama Başladı: {cat_url} ---")
            try:
                r = requests.get(cat_url, headers=HEADERS, timeout=10)
                diziler = re.findall(r'<div class="categorytitle">\s*<a href="(.*?)">(.*?)</a>.*?<img src="(.*?)">', r.text, re.S)
                
                if not diziler:
                    print(f"[UYARI] {cat_url} sayfasında dizi bulunamadı.")
                    continue

                for d_link, d_isim, d_logo in diziler:
                    d_isim = d_isim.strip()
                    print(f"\n>>> DİZİ: {d_isim}")
                    
                    dr = requests.get(d_link, headers=HEADERS, timeout=10)
                    bolumler = re.findall(r'<div class="bolumust">.*?<a href="(.*?)">.*?<div class="baslik">\s*(.*?)\s*<div', dr.text, re.S)
                    
                    for b_link, b_baslik in bolumler:
                        b_baslik = b_baslik.strip().replace("\n", " ").replace("  ", " ")
                        print(f"  - {b_baslik} taranıyor...", end=" ", flush=True)
                        
                        embed = get_embed_from_episode(b_link)
                        if embed:
                            m3u8 = get_m3u8_link(embed)
                            if m3u8:
                                f.write(f'#EXTINF:-1 tvg-id="vod.tr" tvg-name="TR: {d_isim} {b_baslik}" tvg-logo="{d_logo}" group-title="DC-Comics",TR: {d_isim} {b_baslik}\n')
                                f.write(f'{m3u8}\n')
                                f.flush() # Anlık dosyaya kaydeder
                                print("OK!")
                            else: print("M3U8 BULUNAMADI")
                        else: print("PLAYER ÇÖZÜLEMEDİ")
                        
                        time.sleep(0.1)
            except Exception as e:
                print(f"\n[HATA] Sayfa taranırken hata oluştu: {e}")

    print(f"\n[BİTTİ] Her şey '{m3u_filename}' dosyasına kaydedildi!")

if __name__ == "__main__":
    main()
