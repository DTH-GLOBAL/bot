# tv.py
import requests

OUTPUT_FILE = "TheTVApp.m3u"

CHANNELS = [
    ('#EXTINF:-1 tvg-id="ae-us-eastern-feed" tvg-name="A&E US Eastern Feed SD" group-title="Live",A&E US Eastern Feed SD',
     'https://tvpass.org/live/AEEast/sd'),
    ('#EXTINF:-1 tvg-id="ae-us-eastern-feed" tvg-name="A&E US Eastern Feed HD" group-title="Live",A&E US Eastern Feed HD',
     'https://tvpass.org/live/AEEast/hd'),
    ('#EXTINF:-1 tvg-id="abc-kabc-los-angeles-ca" tvg-name="ABC (KABC) Los Angeles SD" group-title="Live",ABC (KABC) Los Angeles SD',
     'https://tvpass.org/live/abc-kabc-los-angeles-ca/sd'),
    ('#EXTINF:-1 tvg-id="abc-kabc-los-angeles-ca" tvg-name="ABC (KABC) Los Angeles HD" group-title="Live",ABC (KABC) Los Angeles HD',
     'https://tvpass.org/live/abc-kabc-los-angeles-ca/hd'),
    ('#EXTINF:-1 tvg-id="abc-wabc-new-york-ny" tvg-name="ABC (WABC) New York, NY SD" group-title="Live",ABC (WABC) New York, NY SD',
     'https://tvpass.org/live/WABCDT1/sd'),
]

def fetch_final_url(url: str) -> str:
    """Kanal URL’sini açıp yönlendirilmiş tokenli gerçek linki döndürür"""
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
        return resp.url  # yönlendirme sonrası gerçek tokenli link
    except Exception as e:
        print(f"[!] Hata: {url} -> {e}")
        return url  # fallback

def main():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for extinf, link in CHANNELS:
            real_link = fetch_final_url(link)
            f.write(f"{extinf}\n{real_link}\n")
    print(f"[+] {OUTPUT_FILE} oluşturuldu.")

if __name__ == "__main__":
    main()
