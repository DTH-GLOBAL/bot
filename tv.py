import asyncio
import urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright

M3U8_FILE = "TheTVApp.m3u"
BASE_URL = "https://thetvapp.to"
CHANNEL_LIST_URL = f"{BASE_URL}/tv"

SECTIONS_TO_APPEND = {
    "/nba": "NBA",
    "/mlb": "MLB", 
    "/wnba": "WNBA",
    "/nfl": "NFL",
    "/ncaaf": "NCAAF",
    "/ncaab": "NCAAB",
    "/soccer": "Soccer",
    "/ppv": "PPV",
    "/events": "Events"
}

def extract_channel_name_from_url(url: str):
    """URL'den kanal ismini çıkar: /hls/AEEast/ -> AEEast"""
    if "/hls/" in url:
        # /hls/ sonrasındaki kısmı al
        parts = url.split("/hls/")
        if len(parts) > 1:
            # İlk slash'a kadar olan kısmı al (AEEast/tracks-v2a1/mono.m3u8 -> AEEast)
            channel_part = parts[1].split("/")[0]
            return channel_part
    return None

def extract_real_m3u8(url: str):
    if "ping.gif" in url and "mu=" in url:
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        mu = qs.get("mu", [None])[0]
        if mu:
            return urllib.parse.unquote(mu)
    if ".m3u8" in url:
        return url
    return None

async def scrape_tv_urls():
    urls = []
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        print(f"🔄 Loading /tv channel list...")
        await page.goto(CHANNEL_LIST_URL, timeout=60000)
        
        links = await page.locator("ol.list-group a").all()
        hrefs = [await link.get_attribute("href") for link in links if await link.get_attribute("href")]
        
        await page.close()

        for href in hrefs:
            full_url = BASE_URL + href
            print(f"🎯 Scraping TV page: {full_url}")
            
            for quality in ["SD", "HD"]:
                stream_url = None
                new_page = await context.new_page()
                
                async def handle_response(response):
                    nonlocal stream_url
                    real = extract_real_m3u8(response.url)
                    if real and not stream_url:
                        stream_url = real
                
                new_page.on("response", handle_response)
                await new_page.goto(full_url)
                
                try:
                    await new_page.get_by_text(f"Load {quality} Stream", exact=True).click(timeout=5000)
                except:
                    pass
                
                await asyncio.sleep(4)
                await new_page.close()
                
                if stream_url:
                    # URL'den kanal ismini çıkar
                    channel_name = extract_channel_name_from_url(stream_url)
                    if not channel_name:
                        # Eğer kanal ismi çıkarılamazsa, href'den çıkarım yap
                        channel_name = href.split("/")[-1] if "/" in href else f"Channel_{len(urls)}"
                    
                    print(f"✅ {quality}: {channel_name} -> {stream_url}")
                    urls.append((stream_url, channel_name))
                else:
                    print(f"❌ {quality} not found")
        
        await browser.close()
        return urls

async def scrape_section_urls(context, section_path, group_name):
    urls = []
    page = await context.new_page()
    section_url = BASE_URL + section_path
    print(f"\n📁 Loading section: {section_url}")
    
    await page.goto(section_url, timeout=60000)
    links = await page.locator("ol.list-group a").all()
    
    hrefs = [await link.get_attribute("href") for link in links if await link.get_attribute("href")]
    
    await page.close()

    for href in hrefs:
        full_url = BASE_URL + href
        print(f"🎯 Scraping {group_name} page: {full_url}")
        
        for quality in ["SD", "HD"]:
            stream_url = None
            new_page = await context.new_page()
            
            async def handle_response(response):
                nonlocal stream_url
                real = extract_real_m3u8(response.url)
                if real and not stream_url:
                    stream_url = real
            
            new_page.on("response", handle_response)
            await new_page.goto(full_url, timeout=60000)
            
            try:
                await new_page.get_by_text(f"Load {quality} Stream", exact=True).click(timeout=5000)
            except:
                pass
            
            await asyncio.sleep(4)
            await new_page.close()
            
            if stream_url:
                # URL'den kanal ismini çıkar - BURASI ÖNEMLİ!
                channel_name = extract_channel_name_from_url(stream_url)
                if not channel_name:
                    # Eğer kanal ismi çıkarılamazsa, href'den çıkarım yap
                    channel_name = href.split("/")[-1] if "/" in href else f"Channel_{len(urls)}"
                
                print(f"✅ {quality}: {channel_name} -> {stream_url}")
                urls.append((stream_url, group_name, channel_name))
            else:
                print(f"❌ {quality} not found")
    
    return urls

async def scrape_all_append_sections():
    all_urls = []
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        
        for section_path, group_name in SECTIONS_TO_APPEND.items():
            urls = await scrape_section_urls(context, section_path, group_name)
            all_urls.extend(urls)
        
        await browser.close()
        return all_urls

def replace_urls_in_tv_section(lines, tv_urls):
    result = []
    url_idx = 0
    
    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF:-1") and i + 1 < len(lines) and lines[i + 1].startswith("http"):
            # EXTINF satırını koru ama tvg-name'i güncelle
            extinf_line = lines[i]
            
            # Mevcut tvg-name'i bul ve değiştir
            if 'tvg-name="' in extinf_line and url_idx < len(tv_urls):
                # Eski tvg-name'i yeni kanal ismiyle değiştir
                stream_url, channel_name = tv_urls[url_idx]
                extinf_parts = extinf_line.split('tvg-name="')
                if len(extinf_parts) > 1:
                    new_extinf = extinf_parts[0] + f'tvg-name="{channel_name}"' + extinf_parts[1].split('"', 1)[1]
                else:
                    # tvg-name yoksa ekle
                    new_extinf = extinf_line.replace('group-title="', f'tvg-name="{channel_name}" group-title="')
                
                result.append(new_extinf)
                result.append(stream_url)
                url_idx += 1
            else:
                # Sadece URL'yi değiştir
                if url_idx < len(tv_urls):
                    result.append(extinf_line)
                    result.append(tv_urls[url_idx][0])
                    url_idx += 1
                else:
                    result.append(extinf_line)
                    result.append(lines[i + 1])
            i += 2
        else:
            result.append(lines[i])
            i += 1
    
    return result

def append_new_streams(lines, new_urls_with_groups):
    lines = [line for line in lines if line.strip() != "#EXTM3U"]
    existing_channels = set()
    
    # Mevcut kanalları bul
    i = 0
    while i < len(lines) - 1:
        if lines[i].startswith("#EXTINF:-1") and i + 1 < len(lines) and lines[i + 1].startswith("http"):
            # Kanal ismini bul
            channel_name = None
            if 'tvg-name="' in lines[i]:
                channel_name = lines[i].split('tvg-name="')[1].split('"')[0]
            elif "," in lines[i]:
                channel_name = lines[i].split(",")[-1].strip()
            
            if channel_name:
                existing_channels.add(channel_name)
            i += 2
        else:
            i += 1

    # Yeni kanalları ekle
    for stream_url, group_name, channel_name in new_urls_with_groups:
        if channel_name not in existing_channels:
            if group_name == "MLB":
                extinf_line = f'#EXTINF:-1 tvg-id="MLB.Baseball.Dummy.us" tvg-name="{channel_name}" tvg-logo="http://drewlive24.duckdns.org:9000/Logos/Baseball-2.png" group-title="{group_name}",{channel_name}'
            else:
                extinf_line = f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{group_name}",{channel_name}'
            
            lines.append(extinf_line)
            lines.append(stream_url)
            existing_channels.add(channel_name)
            print(f"➕ Added new channel: {channel_name}")
        else:
            print(f"⏩ Channel already exists: {channel_name}")
    
    lines = [line for line in lines if line.strip()]
    lines.insert(0, "#EXTM3U")
    return lines

async def main():
    if not Path(M3U8_FILE).exists():
        print(f"❌ File not found: {M3U8_FILE}")
        return
    
    with open(M3U8_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    
    print("🔧 Replacing only /tv stream URLs...")
    tv_new_urls = await scrape_tv_urls()
    
    if not tv_new_urls:
        print("❌ No TV URLs scraped.")
        return
    
    updated_lines = replace_urls_in_tv_section(lines, tv_new_urls)
    
    print("\n📦 Scraping all other sections (NBA, NFL, Events, etc)...")
    append_new_urls = await scrape_all_append_sections()
    
    if append_new_urls:
        updated_lines = append_new_streams(updated_lines, append_new_urls)
    
    with open(M3U8_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(updated_lines))
    
    print(f"\n✅ {M3U8_FILE} updated with proper channel names from URLs!")

if __name__ == "__main__":
    asyncio.run(main())
