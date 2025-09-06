import re
import requests

def get_youtube_live(channel_id: str):
    # İlk istek: cookie almak için
    headers1 = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.58 Mobile Safari/537.36",
        "Referer": "https://yandex.com.tr/",
    }
    r = requests.get("https://m.youtube.com/", headers=headers1)
    text = r.text.replace(";", '","')

    info = re.search(r'VISITOR_INFO1_LIVE=(.*?)"', text)
    data = re.search(r'VISITOR_PRIVACY_METADATA=(.*?)"', text)
    token = re.search(r'__Secure-ROLLOUT_TOKEN=(.*?)"', text)

    if not (info and data and token):
        raise Exception("Cookie bilgileri bulunamadı")

    cookies = {
        "VISITOR_INFO1_LIVE": info.group(1),
        "VISITOR_PRIVACY_METADATA": data.group(1),
        "__Secure-ROLLOUT_TOKEN": token.group(1),
    }

    # İkinci istek: canlı yayını almak için
    headers2 = {
        "User-Agent": headers1["User-Agent"],
        "Referer": "https://m.youtube.com/",
    }
    url = f"https://m.youtube.com/channel/{channel_id}/live?app=TABLET"
    r2 = requests.get(url, headers=headers2, cookies=cookies)

    match = re.search(r'"hlsManifestUrl":"(.*?)"', r2.text)
    if match:
        return match.group(1).replace("\\", "")
    else:
        return None


if __name__ == "__main__":
    channel = "UCehmwSZGPod7JFbHJspmxzQ"  # senin kanal id
    m3u8 = get_youtube_live(channel)
    if m3u8:
        with open("1siriustv.m3u8", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write("#EXT-X-VERSION:5\n")
            f.write("#EXT-X-INDEPENDENT-SEGMENTS\n")
            f.write("#EXT-X-START:TIME-OFFSET=0,PRECISE=YES\n")
            f.write('#EXT-X-STREAM-INF:BANDWIDTH=7000000,AVERAGE-BANDWIDTH=5000000,'
                    'RESOLUTION=1920x1080,FRAME-RATE=25.000,CODECS="avc1.640028,mp4a.40.2",AUDIO="audio"\n')
            f.write(m3u8 + "\n")
        print("M3U8 dosyası oluşturuldu:", m3u8)
    else:
        print("Canlı yayın bulunamadı.")
