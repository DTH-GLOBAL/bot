import asyncio
from playwright.async_api import async_playwright
import re

CHANNEL_ID = "UCehmwSZGPod7JFbHJspmxzQ"
OUTPUT_FILE = "1siriustv.m3u8"

async def get_live_url(channel_id):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=("Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.58 Mobile Safari/537.36")
        )
        page = await context.new_page()
        url = f"https://m.youtube.com/channel/{channel_id}/live"
        await page.goto(url, timeout=60000)

        content = await page.content()
        await browser.close()

        match = re.search(r'"hlsManifestUrl":"(.*?)"', content)
        if match:
            return match.group(1).replace("\\", "")
        return None

async def main():
    link = await get_live_url(CHANNEL_ID)
    if link:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write("#EXT-X-VERSION:5\n")
            f.write("#EXT-X-INDEPENDENT-SEGMENTS\n")
            f.write("#EXT-X-START:TIME-OFFSET=0,PRECISE=YES\n")
            f.write('#EXT-X-STREAM-INF:BANDWIDTH=7000000,AVERAGE-BANDWIDTH=5000000,'
                    'RESOLUTION=1920x1080,FRAME-RATE=25.000,CODECS="avc1.640028,mp4a.40.2",AUDIO="audio"\n')
            f.write(link + "\n")
        print("M3U8 dosyası oluşturuldu:", link)
    else:
        print("Canlı yayın bulunamadı.")

if __name__ == "__main__":
    asyncio.run(main())
