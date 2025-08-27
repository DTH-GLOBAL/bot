import requests
import time

# === KULLANICININ GİRMESİ GEREKEN ===
BEARER_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJMSVZFIiwiaXBiIjoiMCIsImNnZCI6IjA5M2Q3MjBhLTUwMmMtNDFlZC1hODBmLTJiODE2OTg0ZmI5NSIsImNzaCI6IlRSS1NUIiwiZGN0IjoiM0VGNzUiLCJkaSI6IjMwYTM5YzllLWE4ZDYtNGEwMC05NDBmLTFjMTE4NDgzZDcxMiIsInNnZCI6ImJkNmUyNmY5LWJkMzYtNDE2ZC05YWQzLTYzNjhlNGZkYTMyMiIsInNwZ2QiOiJjYjZmZGMwMi1iOGJlLTQ3MTYtYTZjYi1iZTEyYTg4YjdmMDkiLCJpY2giOiIwIiwiaWRtIjoiMCIsImlhIjoiOjpmZmZmOjEwLjAuMC4yMDYiLCJhcHYiOiIxLjAuMCIsImFibiI6IjEwMDAiLCJuYmYiOjE3NTE3MDMxODQsImV4cCI6MTc1MTcwMzI0NCwiaWF0IjoxNzUxNzAzMTg0fQ.SGC_FfT7cU1RVM4E5rMYO2IsA4aYUoYq2SXl51-PZwM"
OUTPUT_M3U = "vodden.m3u"
VOD_ID_FILE = "vod_ids.txt"  # Her satırda 1 ID olacak

HEADERS = {
    "Authorization": BEARER_TOKEN,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://tvheryerde.com",
    "Origin": "https://tvheryerde.com"
}

def load_vod_ids(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[!] {filename} bulunamadı. Lütfen dosyayı oluşturun.")
        return []

def get_film_detail(vod_id):
    url = "https://core-api.kablowebtv.com/api/vod/detail"
    try:
        res = requests.get(url, headers=HEADERS, params={"VodUId": vod_id}, timeout=10)
        res.raise_for_status()
        data = res.json()
        if data.get("IsSucceeded") and data.get("Data"):
            return data["Data"][0]
    except Exception as e:
        print(f"[!] Hata: {vod_id} → {e}")
    return None

def write_m3u(films):
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for film in films:
            title = film.get("Title", "Bilinmeyen")
            uid = film.get("UId")
            logo = ""
            for poster in film.get("Posters", []):
                if poster.get("Type", "").lower() == "listing":
                    logo = poster.get("ImageUrl", "")
                    break
            stream = film.get("StreamData", {})
            mpd = stream.get("DashStreamUrl")
            if mpd and not stream.get("IsDrmEnabled", True):
                f.write(f'#EXTINF:-1 tvg-id="{uid}" tvg-logo="{logo}" group-title="VOD", {title}\n{mpd}\n')
    print(f"[✓] {len(films)} film yazıldı → {OUTPUT_M3U}")

def main():
    vod_ids = load_vod_ids(VOD_ID_FILE)
    if not vod_ids:
        return

    collected = []
    print(f"[▶] {len(vod_ids)} adet film işleniyor...")

    for i, vid in enumerate(vod_ids):
        print(f"[{i+1}/{len(vod_ids)}] Alınıyor: {vid}")
        detail = get_film_detail(vid)
        if detail and detail.get("StreamData", {}).get("DashStreamUrl"):
            collected.append(detail)
        time.sleep(0.5)  # Ban yememek için bekleme

    write_m3u(collected)

if __name__ == "__main__":
    main()
