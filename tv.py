# tv.py
import requests

SOURCE_URL = "https://tvpass.org/playlist/m3u"
OUTPUT_FILE = "TheTVApp.m3u"

def fetch_final_url(url: str) -> str:
    """URL’yi açıp yönlendirilmiş tokenli gerçek linki döndürür"""
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
        return resp.url  # yönlendirme sonrası tokenli link
    except Exception as e:
        print(f"[!] Hata: {url} -> {e}")
        return url

def main():
    try:
        resp = requests.get(SOURCE_URL, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except Exception as e:
        print(f"[!] Playlist alınamadı: {e}")
        return

    lines = resp.text.strip().splitlines()
    output_lines = ["#EXTM3U"]

    # M3U dosyasında her #EXTINF’den sonra link var
    for i in range(len(lines)):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            output_lines.append(line)
            if i + 1 < len(lines):
                original_link = lines[i + 1].strip()
                real_link = fetch_final_url(original_link)
                output_lines.append(real_link)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"[+] {OUTPUT_FILE} oluşturuldu. Kanal sayısı: {len(output_lines)//2}")

if __name__ == "__main__":
    main()
