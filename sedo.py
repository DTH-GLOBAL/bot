import requests
import re

HEADERS = {"User-Agent": "Mozilla/5.0"}

CHANNELS = [
    {"id": "bein1", "source_id": "selcukbeinsports1", "name": "BeIN Sports 1", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "bein1", "source_id": "selcukobs1", "name": "BeIN Sports 1", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "bein2", "source_id": "selcukbeinsports2", "name": "BeIN Sports 2", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "bein3", "source_id": "selcukbeinsports3", "name": "BeIN Sports 3", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "bein4", "source_id": "selcukbeinsports4", "name": "BeIN Sports 4", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "bein5", "source_id": "selcukbeinsports5", "name": "BeIN Sports 5", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "beinmax1", "source_id": "selcukbeinsportsmax1", "name": "BeIN Sports Max 1", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "beinmax2", "source_id": "selcukbeinsportsmax2", "name": "BeIN Sports Max 2", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "tivibu1", "source_id": "selcuktivibuspor1", "name": "Tivibu Spor 1", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "tivibu2", "source_id": "selcuktivibuspor2", "name": "Tivibu Spor 2", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "tivibu3", "source_id": "selcuktivibuspor3", "name": "Tivibu Spor 3", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "tivibu4", "source_id": "selcuktivibuspor4", "name": "Tivibu Spor 4", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "ssport1", "source_id": "selcukssport", "name": "S Sport 1", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "ssport2", "source_id": "selcukssport2", "name": "S Sport 2", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "smart1", "source_id": "selcuksmartspor", "name": "Smart Spor 1", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "smart2", "source_id": "selcuksmartspor2", "name": "Smart Spor 2", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "aspor", "source_id": "selcukaspor", "name": "A Spor", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "eurosport1", "source_id": "selcukeurosport1", "name": "Eurosport 1", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
    {"id": "eurosport2", "source_id": "selcukeurosport2", "name": "Eurosport 2", "logo": "https://i.hizliresim.com/2noijky.jpg", "group": "Spor"},
]

def get_active_site():
    entry_url = "https://www.selcuksportshd78.is/"
    try:
        entry_source = requests.get(entry_url, headers=HEADERS, timeout=5).text
        match = re.search(r'url=(https:\/\/[^"]+)', entry_source)
        if match:
            print(f"Aktif site: {match.group(1)}")
            return match.group(1)
        else:
            print("Aktif site bulunamadı.")
            return None
    except:
        print("Giriş URL'sine erişilemedi.")
        return None

def get_base_url(active_site):
    try:
        source = requests.get(active_site, headers=HEADERS, timeout=5).text
        match = re.search(r'https:\/\/[^"]+\/index\.php\?id=selcukbeinsports1', source)
        if match:
            base_url = match.group(0).replace("selcukbeinsports1", "")
            print(f"Base URL: {base_url}")
            return base_url
        else:
            print("Base URL bulunamadı.")
            return None
    except:
        print("Aktif siteye erişilemedi.")
        return None

def fetch_streams(base_url):
    result = []
    for ch in CHANNELS:
        url = f"{base_url}{ch['source_id']}"
        try:
            source = requests.get(url, headers=HEADERS, timeout=5).text
            match = re.search(r'(https:\/\/[^\'"]+\/live\/[^\'"]+\/playlist\.m3u8)', source)
            if match:
                stream_url = match.group(1)
            else:
                match = re.search(r'(https:\/\/[^\'"]+\/live\/)', source)
                if match:
                    stream_url = f"{match.group(1)}{ch['source_id']}/playlist.m3u8"
                else:
                    continue
            stream_url = re.sub(r'[\'";].*$', '', stream_url).strip()
            if stream_url and re.match(r'^https?://', stream_url):
                print(f"{ch['name']} → {stream_url}")
                result.append((ch, stream_url))
        except:
            continue
    return result

def generate_html(streams, filename="sadom.html"):
    print(f"\nHTML dosyası yazılıyor: {filename}")
    
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeaTHLesS TV</title>
    <script src="https://cdn.jsdelivr.net/npm/clappr@latest/dist/clappr.min.js"></script>
    <style>
        *:not(input):not(textarea) {
            -moz-user-select: -moz-none;
            -khtml-user-select: none;
            -webkit-user-select: none;
            -o-user-select: none;
            -ms-user-select: none;
            user-select: none;
        }

        body {
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a1a 100%);
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: 500;
            -webkit-tap-highlight-color: transparent;
            line-height: 20px;
            -webkit-text-size-adjust: 100%;
            text-decoration: none;
            min-height: 100vh;
        }

        a {
            text-decoration: none;
            color: white;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            background: linear-gradient(135deg, rgba(23, 43, 67, 0.95) 0%, rgba(35, 65, 95, 0.95) 100%);
            backdrop-filter: blur(10px);
            border-bottom: 2px solid #ff0000;
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 99999;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
        }

        .logo {
            width: 60px;
            height: 60px;
            margin-right: 15px;
            border-radius: 50%;
            border: 2px solid #ff0000;
            box-shadow: 0 0 10px rgba(255, 0, 0, 0.5);
        }

        .title-container {
            display: flex;
            flex-direction: column;
            margin-right: auto;
        }

        .title {
            font-size: 24px;
            font-weight: bold;
            color: #ffffff;
            text-shadow: 0 0 10px rgba(255, 0, 0, 0.7);
            letter-spacing: 1px;
        }

        .subtitle {
            font-size: 14px;
            color: #cccccc;
            margin-top: 2px;
        }

        .channel-list {
            padding: 0;
            margin: 0;
            margin-top: 90px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1px;
            background-color: #1a1a1a;
        }

        .channel-item {
            display: flex;
            align-items: center;
            background: linear-gradient(135deg, #16202a 0%, #1e2a3a 100%);
            transition: all 0.3s ease;
            cursor: pointer;
            border: 1px solid #333;
            margin: 5px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }

        .channel-item:hover {
            background: linear-gradient(135deg, #ff0000 0%, #cc0000 100%);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 0, 0, 0.4);
        }

        .channel-item a {
            text-decoration: none;
            color: #e1e1e1;
            padding: 15px;
            display: flex;
            align-items: center;
            width: 100%;
            transition: color 0.3s ease;
        }

        .channel-item:hover a {
            color: #ffffff;
        }

        .channel-item img {
            width: 50px;
            height: 50px;
            border-radius: 8px;
            margin-right: 15px;
            border: 2px solid #333;
            transition: border-color 0.3s ease;
        }

        .channel-item:hover img {
            border-color: #ffffff;
        }

        .channel-item span {
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .channel-item:hover span {
            font-weight: 700;
        }

        #player-container {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: #000;
            z-index: 100000;
        }

        #player {
            width: 100%;
            height: 100%;
        }

        @media (max-width: 768px) {
            .channel-list {
                grid-template-columns: 1fr;
                margin-top: 80px;
            }
            
            .header {
                padding: 10px 15px;
            }
            
            .logo {
                width: 50px;
                height: 50px;
            }
            
            .title {
                font-size: 20px;
            }
        }

        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <img src="https://i.hizliresim.com/2noijky.jpg" alt="Logo" class="logo">
        <div class="title-container">
            <div class="title">DeaTHLesS TV</div>
            <div class="subtitle"></div>
        </div>
    </div>
    <div class="channel-list">
"""

    for ch, url in streams:
        html_template += f"""        <div class='channel-item' data-channel='{ch["name"]}' data-href='{url}'>
            <a><img src='{ch["logo"]}' alt='Logo'><span>{ch["name"]}</span></a>
        </div>
"""

    html_template += """    </div>

    <div class="footer">
        DeaTHLesS TV © 2024 - Premium Spor Yayınları
    </div>

    <div id="player-container">
        <div id="player"></div>
    </div>

    <script>
        let player = null;
        document.querySelectorAll('.channel-item').forEach(item => {
            item.addEventListener('click', function() {
                const channelName = this.getAttribute('data-channel');
                const channelUrl = this.getAttribute('data-href');
                
                document.querySelector('.subtitle').textContent = channelName;
                document.getElementById('player-container').style.display = 'block';
                
                if (player) {
                    player.destroy();
                }
                
                player = new Clappr.Player({
                    source: channelUrl,
                    parentId: '#player',
                    autoPlay: true,
                    mute: false,
                    height: '100%',
                    width: '100%',
                    plugins: [],
                    events: {
                        onError: function() {
                            alert('Yayın açılamadı. Lütfen daha sonra tekrar deneyin.');
                        }
                    }
                });
            });
        });

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                if (player) {
                    player.destroy();
                    player = null;
                }
                document.getElementById('player-container').style.display = 'none';
                document.querySelector('.subtitle').textContent = '';
            }
        });

        document.getElementById('player-container').addEventListener('click', function(e) {
            if (e.target === this) {
                if (player) {
                    player.destroy();
                    player = null;
                }
                this.style.display = 'none';
                document.querySelector('.subtitle').textContent = '';
            }
        });
    </script>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    print("Tamamlandı. Kanal sayısı:", len(streams))

def main():
    active_site = get_active_site()
    if not active_site:
        return
    base_url = get_base_url(active_site)
    if not base_url:
        return
    streams = fetch_streams(base_url)
    if streams:
        generate_html(streams)
    else:
        print("Hiçbir yayın alınamadı.")

if __name__ == "__main__":
    main()
