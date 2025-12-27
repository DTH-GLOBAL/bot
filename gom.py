import requests
import re
import base64
import string
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": "https://play.dizigom104.com/"
}

# HEDEF DİZİ LİSTESİ
TARGET_SERIES = [
    "https://dizigom104.com/dizi-izle/young-justice/",
    "https://dizigom104.com/dizi-izle/harley-quinn/",
    "https://dizigom104.com/dizi-izle/lucifer/",
    "https://dizigom104.com/dizi-izle/preacher/",
    "https://dizigom104.com/dizi-izle/gotham/",
    "https://dizigom104.com/dizi-izle/izombie/",
    "https://dizigom104.com/dizi-izle/doom-patrol/",
    "https://dizigom104.com/dizi-izle/the-flash/",
    "https://dizigom104.com/dizi-izle/constantine/",
    "https://dizigom104.com/dizi-izle/smallville/",
    "https://dizigom104.com/dizi-izle/titans/",
    "https://dizigom104.com/dizi-izle/swamp-thing/",
    "https://dizigom104.com/dizi-izle/krypton/",
    "https://dizigom104.com/dizi-izle/dcs-legends-of-tomorrow/",
    "https://dizigom104.com/dizi-izle/supergirl/",
    "https://dizigom104.com/dizi-izle/batwoman/"
]

def check_link_is_active(url):
    try:
        r = requests.head(url, headers=HEADERS, timeout=1.5, allow_redirects=True)
        return r.status_code == 200
    except:
        return False

def get_m3u8_link(embed_url):
    try:
        r = requests.get(embed_url, headers=HEADERS, timeout=10)
        m2 = re.search(r"eval\(function\(p,a,c,k,e,d\).*?\('(.+?)'\.split\('\|'\)", r.text, re.S)
        if not m2: return None

        parts = m2.group(1).split("|")
        video_hash = next((p for p in parts if re.fullmatch(r"[a-f0-9]{32}", p)), None)
        if not video_hash: return None
        
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
    m3u_filename = "dizigom-dc-ozel.m3u"
    print(f"Bot başlatıldı, '{m3u_filename}' dosyası oluşturuluyor...")
    
    with open(m3u_filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for series_url in TARGET_SERIES:
            print(f"\n--- Dizi İnceleniyor: {series_url} ---")
            try:
                r = requests.get(series_url, headers=HEADERS, timeout=10)
                
                # İSTEDİĞİN GÜNCELLEME: <title> içinden dizi ismini al
                # Örn: <title>Young Justice İzle - Dizigom</title> içinden "Young Justice" kısmını alır
                title_match = re.search(r'<title>(.*?) (?:İzle|izle)', r.text)
                d_isim = title_match.group(1).strip() if title_match else "Bilinmeyen Dizi"
                
                # İSTEDİĞİN GÜNCELLEME: "image":"..." içinden logo URL'sini al
                # URL içindeki kaçış karakterlerini ( \/ ) temizler
                logo_match = re.search(r'"image":"(.*?)"', r.text)
                d_logo = logo_match.group(1).replace("\\/", "/") if logo_match else ""

                print(f"Bulunan Dizi: {d_isim}")
                print(f"Bulunan Logo: {d_logo}")

                # Bölüm linklerini topla
                bolumler = re.findall(r'<div class="bolumust">.*?<a href="(.*?)">.*?<div class="baslik">\s*(.*?)\s*<div', r.text, re.S)
                
                if not bolumler:
                    print(f"[UYARI] {d_isim} için bölüm bulunamadı.")
                    continue

                for b_link, b_baslik in bolumler:
                    b_baslik = b_baslik.strip().replace("\n", " ").replace("  ", " ")
                    print(f"  - {b_baslik} taranıyor...", end=" ", flush=True)
                    
                    embed = get_embed_from_episode(b_link)
                    if embed:
                        m3u8 = get_m3u8_link(embed)
                        if m3u8:
                            # M3U Formatına yazma
                            f.write(f'#EXTINF:-1 tvg-id="vod.tr" tvg-name="TR: {d_isim} {b_baslik}" tvg-logo="{d_logo}" group-title="DC-Comics",TR: {d_isim} {b_baslik}\n')
                            f.write(f'{m3u8}\n')
                            f.flush()
                            print("TAMAM!")
                        else: print("M3U8 YOK")
                    else: print("PLAYER ERROR")
                    
                    time.sleep(0.05) 
            except Exception as e:
                print(f"\n[HATA] {series_url} taranırken hata: {e}")

    print(f"\n[BİTTİ] Liste '{m3u_filename}' olarak kaydedildi!")

if __name__ == "__main__":
    main()
