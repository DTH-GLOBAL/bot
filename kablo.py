import requests
import gzip
from io import BytesIO

def get_canli_tv_m3u():
    """
    Canlı TV m3u dosyasını oluşturur.
    HEADERS kısmı VOD tarzı token, Referer ve Origin içerir.
    """
    
    url = "https://core-api.kablowebtv.com/api/channels"
    HEADERS = {
        "Authorization": "Bearer ",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://tvheryerde.com",
        "Origin": "https://tvheryerde.com"
    }
    
    try:
        print("📡 Canlı TV API'den veri alınıyor...")
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # Eğer gzip ile gelirse aç
        try:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                content = gz.read().decode('utf-8')
        except:
            content = response.content.decode('utf-8')
        
        data = response.json() if not 'content' in locals() else json.loads(content)
        
        if not data.get('IsSucceeded') or not data.get('Data', {}).get('AllChannels'):
            print("❌ Canlı TV API'den geçerli veri alınamadı!")
            return False
        
        channels = data['Data']['AllChannels']
        print(f"✅ {len(channels)} kanal bulundu")
        
        with open("kablo.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            
            kanal_sayisi = 0
            kanal_index = 1  
            
            for channel in channels:
                name = channel.get('Name')
                stream_data = channel.get('StreamData', {})
                hls_url = stream_data.get('HlsStreamUrl') if stream_data else None
                logo = channel.get('PrimaryLogoImageUrl', '')
                categories = channel.get('Categories', [])
                
                if not name or not hls_url:
                    continue
                
                group = categories[0].get('Name', 'Genel') if categories else 'Genel'
                
                if group == "Bilgilendirme":
                    continue

                tvg_id = str(kanal_index)

                f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group}",{name}\n')
                f.write(f'{hls_url}\n')

                kanal_sayisi += 1
                kanal_index += 1  
        
        print(f"📺 kablo.m3u dosyası oluşturuldu! ({kanal_sayisi} kanal)")
        return True
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

if __name__ == "__main__":
    get_canli_tv_m3u()
