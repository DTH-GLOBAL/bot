import requests
from concurrent.futures import ThreadPoolExecutor

# --- AYARLAR ---
BASE_URL = "https://goldvod.org"
USER = "hpgdiscoo"
PASS = "123456"
THREAD_SAYISI = 15 # Aynı anda kaç link çözülsün?
CIKIS_DOSYASI = "disco.m3u"

headers = {'User-Agent': 'VLC/3.0.11 LibVLC/3.0.11'}

def link_cozumle(name, fake_url):
    """Linke gidip 302 yönlendirmesi varsa gerçek adresi döner."""
    try:
        # allow_redirects=False sayesinde gerçek kaynağın adresini (Location) yakalıyoruz
        r = requests.get(fake_url, headers=headers, timeout=8, allow_redirects=False)
        if r.status_code in [301, 302]:
            final_url = r.headers.get('Location')
            print(f"[OK] Çözüldü: {name}")
            return f"#EXTINF:-1, {name}\n{final_url}"
        return f"#EXTINF:-1, {name}\n{fake_url}"
    except:
        return f"#EXTINF:-1, {name}\n{fake_url}"

def ana_calistirici():
    sonuc_listesi = ["#EXTM3U"]
    ham_linkler = [] # (isim, link) çiftlerini burada toplayacağız

    # 1. CANLI KANALLARIN HAM LİSTESİNİ AL
    print("Canlı kanal listesi alınıyor...")
    live_url = f"{BASE_URL}/get.php?username={USER}&password={PASS}&type=m3u_plus"
    try:
        r_live = requests.get(live_url, headers=headers)
        lines = r_live.text.splitlines()
        for i in range(len(lines)):
            if lines[i].startswith("#EXTINF"):
                ham_linkler.append((lines[i].split(",")[-1], lines[i+1]))
    except: print("Canlı kanallar alınamadı.")

    # 2. FİLMLERİ AL (API ÜZERİNDEN)
    print("Film listesi çekiliyor...")
    api_url = f"{BASE_URL}/player_api.php?username={USER}&password={PASS}"
    try:
        vods = requests.get(f"{api_url}&action=get_vod_streams", headers=headers).json()
        for v in vods:
            v_name = v.get("name")
            v_id = v.get("stream_id")
            v_ext = v.get("container_extension", "mp4")
            v_link = f"{BASE_URL}/movie/{USER}/{PASS}/{v_id}.{v_ext}"
            ham_linkler.append((f"[FİLM] {v_name}", v_link))
    except: print("Filmler alınamadı.")

    # 3. DİZİLERİ VE BÖLÜMLERİ AL
    print("Dizi ve bölüm detayları çekiliyor (Bu biraz uzun sürebilir)...")
    try:
        series = requests.get(f"{api_url}&action=get_series", headers=headers).json()
        # Çok uzun sürmemesi için ilk 20 dizinin bölümlerine girer (Hepsini istersen döngüyü sınırlama)
        for s in series[:50]: # Örnek olarak ilk 50 diziyi alır, hepsini istersen [:50] kısmını sil
            s_id = s.get("series_id")
            s_name = s.get("name")
            info = requests.get(f"{api_url}&action=get_series_info&series_id={s_id}", headers=headers).json()
            episodes = info.get("episodes", {})
            for season in episodes:
                for ep in episodes[season]:
                    ep_id = ep.get("id")
                    ep_ext = ep.get("container_extension", "mp4")
                    ep_link = f"{BASE_URL}/series/{USER}/{PASS}/{ep_id}.{ep_ext}"
                    ham_linkler.append((f"[DİZİ] {s_name} S{season}E{ep.get('episode_num')}", ep_link))
    except: print("Diziler alınamadı.")

    # 4. TÜM LİNKLERİ ÇÖZÜMLE (REDIRECT TAKİBİ)
    print(f"\nToplam {len(ham_linkler)} link bulundu. Gerçek kaynaklar çözümleniyor...")
    
    with ThreadPoolExecutor(max_workers=THREAD_SAYISI) as executor:
        final_lines = list(executor.map(lambda p: link_cozumle(*p), ham_linkler))
        sonuc_listesi.extend(final_lines)

    # 5. DOSYAYA KAYDET
    with open(CIKIS_DOSYASI, "w", encoding="utf-8") as f:
        f.write("\n".join(sonuc_listesi))
    
    print(f"\nİşlem TAMAM! Her şey '{CIKIS_DOSYASI}' dosyasına kaydedildi.")

if __name__ == "__main__":
    ana_calistirici()
