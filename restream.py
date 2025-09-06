import requests
import json

API_KEY = "YOUR_API_KEY_HERE"
CHANNEL_ID = "UCehmwSZGPod7JFbHJspmxzQ"
OUTPUT_FILE = "1siriustv.m3u8"

# Canlı yayın video ID'sini al
def get_live_video_id(channel_id):
    url = (
        f"https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet&channelId={channel_id}"
        f"&eventType=live&type=video&key={API_KEY}"
    )
    r = requests.get(url).json()
    items = r.get("items", [])
    if not items:
        return None
    return items[0]["id"]["videoId"]

# Video ID üzerinden HLS link al
def get_hls_link(video_id):
    url = f"https://www.youtube.com/get_video_info?video_id={video_id}&el=detailpage"
    r = requests.get(url)
    data = dict(x.split('=') for x in r.text.split('&') if '=' in x)
    # "player_response" JSON'u al
    player_response = json.loads(requests.utils.unquote(data["player_response"]))
    streaming_data = player_response.get("streamingData", {})
    hls_manifest_url = streaming_data.get("hlsManifestUrl")
    return hls_manifest_url

def main():
    video_id = get_live_video_id(CHANNEL_ID)
    if not video_id:
        print("Canlı yayın bulunamadı.")
        return

    hls_url = get_hls_link(video_id)
    if not hls_url:
        print("HLS manifest linki bulunamadı.")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("#EXT-X-VERSION:5\n")
        f.write("#EXT-X-INDEPENDENT-SEGMENTS\n")
        f.write("#EXT-X-START:TIME-OFFSET=0,PRECISE=YES\n")
        f.write('#EXT-X-STREAM-INF:BANDWIDTH=7000000,AVERAGE-BANDWIDTH=5000000,'
                'RESOLUTION=1920x1080,FRAME-RATE=25.000,CODECS="avc1.640028,mp4a.40.2",AUDIO="audio"\n')
        f.write(hls_url + "\n")

    print("M3U8 dosyası oluşturuldu:", hls_url)

if __name__ == "__main__":
    main()
