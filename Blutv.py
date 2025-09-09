import asyncio
import aiohttp
import re
import os
from itertools import islice
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging
from concurrent.futures import ThreadPoolExecutor
import time


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


BASE_URL = "https://dizifun5.com/blutv"
PROXY_BASE_URL = "https://3.nejyoner19.workers.dev/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def create_proxy_url(original_url):
    """Yeni proxy sistemine göre M3U8 URL'yi dönüştürür"""
    if not original_url:
        return None

    # Yeni proxy adresine göre yapılandır
    proxy_url = f"https://3.nejyoner19.workers.dev/?url={original_url}"
    logger.info(f"[PROXY] {original_url} -> {proxy_url}")
    return proxy_url


def sanitize_id(text):
    """Metni ID formatına dönüştürür - Türkçe karakterleri düzgün handle eder"""
    if not text:
        return "UNKNOWN"


    turkish_chars = {
        'ç': 'c', 'Ç': 'C',
        'ğ': 'g', 'Ğ': 'G', 
        'ı': 'i', 'I': 'I',
        'İ': 'I', 'i': 'i',
        'ö': 'o', 'Ö': 'O',
        'ş': 's', 'Ş': 'S',
        'ü': 'u', 'Ü': 'U'
    }


    for turkish_char, english_char in turkish_chars.items():
        text = text.replace(turkish_char, english_char)


    import unicodedata
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')


    text = re.sub(r'[^A-Za-z0-9\s]', '', text)


    text = re.sub(r'\s+', '_', text.strip())


    text = text.upper()


    text = re.sub(r'_+', '_', text)


    text = text.strip('_')

    return text if text else "UNKNOWN"

def chunked_iterable(iterable, size):
    """Listeyi belirli boyutlarda parçalara ayırır"""
    it = iter(iterable)
    for first in it:
        yield [first] + list(islice(it, size-1))

def fix_url(url, base=BASE_URL):
    """URL'yi düzeltir"""
    if not url:
        return None
    if url.startswith('/'):
        return urljoin(base, url)
    return url

def extract_season_episode_from_url(url):
    """URL'den sezon ve bölüm bilgisini çıkarır"""
    season_match = re.search(r'sezon[=-]?(\d+)', url, re.IGNORECASE)
    episode_match = re.search(r'(bolum|episode)[=-]?(\d+)', url, re.IGNORECASE)

    season = season_match.group(1) if season_match else "1"
    episode = episode_match.group(2) if episode_match else "?"

    return season, episode

def normalize_episode_numbers(episode_links):
    """Bölüm numaralarını sezona göre 1'den başlayacak şekilde düzenler"""

    seasons = {}
    for episode_url, season_num in episode_links:
        if season_num not in seasons:
            seasons[season_num] = []
        seasons[season_num].append(episode_url)


    normalized_episodes = []
    for season_num in sorted(seasons.keys()):
        episode_urls = seasons[season_num]
        for idx, episode_url in enumerate(episode_urls, 1):
            normalized_episodes.append((episode_url, season_num, idx))

    return normalized_episodes

async def fetch_page(session, url, timeout=45):  
    """Async olarak sayfa içeriğini getirir - geliştirilmiş versiyon"""
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
            if response.status == 200:
                content = await response.text()
                return content
            else:
                logger.warning(f"[!] HTTP {response.status} hatası: {url}")
                return None
    except asyncio.TimeoutError:
        logger.error(f"[!] Timeout hatası ({timeout}s): {url}")
        return None
    except Exception as e:
        logger.error(f"[!] Sayfa getirme hatası ({url}): {e}")
        return None

async def extract_gujan_m3u8(session, gujan_iframe_url):
    """Gujan iframe'inden m3u8 URL'sini çıkarır"""
    try:

        if gujan_iframe_url.startswith("//"):
            gujan_iframe_url = "https:" + gujan_iframe_url

        logger.info(f"[GUJAN] İframe URL'sine istek atılıyor: {gujan_iframe_url}")


        content = await fetch_page(session, gujan_iframe_url)
        if not content:
            logger.warning(f"[GUJAN] İframe içeriği alınamadı: {gujan_iframe_url}")
            return None


        soup = BeautifulSoup(content, 'html.parser')


        source_element = soup.select_one('source[type="application/x-mpegURL"]')
        if source_element:
            m3u8_url = source_element.get('src')
            if m3u8_url:
                logger.info(f"[GUJAN] ✅ M3U8 URL bulundu: {m3u8_url}")
                return m3u8_url


        scripts = soup.find_all('script')
        for script in scripts:
            script_content = script.get_text() or ""


            m3u8_patterns = [
                r'https?://[^"\s]+/hls/[^"/\s]+/playlist\.m3u8',
                r'https?://[^"\s]+\.m3u8',
                r'"(https?://gujan\.premiumvideo\.click/hls/[^"]+)"'
            ]

            for pattern in m3u8_patterns:
                matches = re.findall(pattern, script_content)
                if matches:
                    m3u8_url = matches[0]
                    logger.info(f"[GUJAN] ✅ Script'ten M3U8 URL bulundu: {m3u8_url}")
                    return m3u8_url


        file_id_match = re.search(r'/e/([a-zA-Z0-9]+)', gujan_iframe_url)
        if file_id_match:
            file_id = file_id_match.group(1)
            constructed_m3u8 = f"https://gangamstyle2.dailymonvideo.biz/hls/{file_id}_o/playlist.m3u8"
            logger.info(f"[GUJAN] ✅ Constructed M3U8 URL: {constructed_m3u8}")
            return constructed_m3u8

        logger.warning(f"[GUJAN] ❌ M3U8 URL bulunamadı: {gujan_iframe_url}")
        return None

    except Exception as e:
        logger.error(f"[GUJAN] ❌ Hata: {e}")
        return None

async def get_correct_domain_from_playhouse(session, file_id, timeout=15):
    """Playhouse URL'ine istek atıp redirect edilen doğru domain'i bulur"""
    playhouse_url = f"https://playhouse.premiumvideo.click/player/{file_id}"

    try:
        logger.info(f"[*] Playhouse URL'ine redirect testi: {playhouse_url}")


        async with session.get(playhouse_url, 
                              headers=HEADERS, 
                              timeout=aiohttp.ClientTimeout(total=timeout),
                              allow_redirects=True) as response:

            final_url = str(response.url)
            logger.info(f"[*] Final redirect URL: {final_url}")


            domain_match = re.search(r'https://([^.]+)\.premiumvideo\.click', final_url)
            if domain_match:
                domain = domain_match.group(1)
                logger.info(f"[✅] Redirect edilen domain bulundu: {domain}")


                m3u8_url = f"https://{domain}.premiumvideo.click/uploads/encode/{file_id}/master.m3u8"


                is_valid = await test_m3u8_url(session, m3u8_url)
                if is_valid:
                    logger.info(f"[✅] M3U8 URL doğrulandı: {m3u8_url}")
                    return domain, m3u8_url
                else:
                    logger.warning(f"[⚠️] M3U8 URL doğrulanamadı ama domain bulundu: {domain}")
                    return domain, m3u8_url
            else:
                logger.warning(f"[⚠️] Redirect URL'den domain çıkarılamadı: {final_url}")


                logger.info(f"[*] Fallback: Eski domain test sistemi kullanılıyor")
                return await find_working_domain_fallback(session, file_id)

    except asyncio.TimeoutError:
        logger.warning(f"[⚠️] Playhouse timeout, fallback sistem kullanılıyor")
        return await find_working_domain_fallback(session, file_id)
    except Exception as e:
        logger.warning(f"[⚠️] Playhouse hatası: {e}, fallback sistem kullanılıyor")
        return await find_working_domain_fallback(session, file_id)

async def find_working_domain_fallback(session, file_id, domains=["d1", "d2", "d3", "d4"]):
    """Fallback: Eski sistem ile çalışan domain bulma"""
    logger.info(f"[*] Fallback domain testi başlıyor...")

    for domain in domains:
        m3u8_url = f"https://{domain}.premiumvideo.click/uploads/encode/{file_id}/master.m3u8"

        logger.info(f"[*] Fallback test: {domain}")
        is_working = await test_m3u8_url(session, m3u8_url)

        if is_working:
            logger.info(f"[✅] Fallback domain çalışıyor: {domain}")
            return domain, m3u8_url


    logger.warning(f"[⚠️] Hiçbir domain çalışmıyor! Default d2 kullanılacak.")
    return "d2", f"https://gangamstyle2.dailymonvideo.biz/uploads/encode/{file_id}/master.m3u8"

async def test_m3u8_url(session, url, timeout=15):
    """Geliştirilmiş m3u8 URL test fonksiyonu"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout), allow_redirects=True) as response:
            final_url = str(response.url)
            content_type = response.headers.get("Content-Type", "").lower()
            content_length = response.headers.get("Content-Length")

            logger.info(f"[DEBUG] Test URL: {url}")
            logger.info(f"[DEBUG] Final URL: {final_url}")
            logger.info(f"[DEBUG] Status: {response.status}")
            logger.info(f"[DEBUG] Content-Type: {content_type}")


            if response.status != 200:
                logger.info(f"[DEBUG] Status code 200 değil: {response.status}")
                return False


            if "premiumvideo.click" not in final_url:
                logger.info(f"[DEBUG] Redirect: premiumvideo.click domain'inden çıkmış: {final_url}")
                return False


            try:
                content = await response.content.read(4096)
                text = content.decode('utf-8', errors='ignore')

                logger.info(f"[DEBUG] İçerik ilk 100 karakter: {text[:100]}")


                if not text.strip().startswith("#EXTM3U"):
                    logger.info(f"[DEBUG] İçerik #EXTM3U ile başlamıyor")
                    return False


                suspicious_patterns = [
                    r"<html", r"<body", r"<title", r"error", r"not found", 
                    r"access denied", r"kerimkirac\.com", r"404", r"403", r"500"
                ]

                for pattern in suspicious_patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        logger.info(f"[DEBUG] Şüpheli pattern bulundu: {pattern}")
                        return False


                if content_length and int(content_length) < 50:
                    logger.info(f"[DEBUG] Content-Length çok küçük: {content_length}")
                    return False


                if "master.m3u8" not in final_url and "playlist.m3u8" not in final_url:
                    logger.info(f"[DEBUG] URL'de m3u8 yok: {final_url}")
                    return False

                logger.info(f"[DEBUG] ✅ Tüm kontroller başarılı!")
                return True

            except UnicodeDecodeError:
                logger.info(f"[DEBUG] Unicode decode hatası - muhtemelen binary content")

                return False

    except asyncio.TimeoutError:
        logger.info(f"[DEBUG] Timeout: {url}")
        return False
    except Exception as e:
        logger.warning(f"[DEBUG] Test hatası: {e}")
        return False

async def get_series_from_page(session, page_num):
    """Belirli bir sayfadan dizi listesini alır"""
    diziler_url = f"{BASE_URL}/diziler?p={page_num}"
    logger.info(f"Sayfa {page_num} alınıyor: {diziler_url}")

    content = await fetch_page(session, diziler_url)
    if not content:
        logger.warning(f"[!] Sayfa {page_num} alınamadı.")
        return [], False

    soup = BeautifulSoup(content, 'html.parser')


    series_links = []
    link_elements = soup.select("a.uk-position-cover[href*='/dizi/']")


    for element in link_elements:
        href = element.get("href")
        if href:
            full_url = fix_url(href)
            if full_url and full_url not in series_links:
                series_links.append(full_url)


    has_next_page = False


    pagination_selectors = [
        ".uk-pagination .uk-pagination-next",
        ".pagination .next",
        "a[href*='?p=']",
        ".uk-pagination a"
    ]

    for selector in pagination_selectors:
        pagination_elements = soup.select(selector)
        for element in pagination_elements:
            href = element.get("href", "")
            if href and f"?p={page_num + 1}" in href:
                has_next_page = True
                break
        if has_next_page:
            break


    if not has_next_page and series_links:
        next_page_url = f"{BASE_URL}/diziler?p={page_num + 1}"
        next_content = await fetch_page(session, next_page_url)
        if next_content:
            next_soup = BeautifulSoup(next_content, 'html.parser')
            next_links = next_soup.select(".uk-grid .uk-width-large-1-6 a.uk-position-cover")
            if next_links:
                has_next_page = True

    logger.info(f"[+] Sayfa {page_num}: {len(series_links)} dizi linki toplandı. Sonraki sayfa: {'Var' if has_next_page else 'Yok'}")
    return series_links, has_next_page

async def get_series_from_homepage():
    """Tüm sayfalardan dizi listesini alır"""
    async with aiohttp.ClientSession() as session:
        all_series_links = []
        page_num = 1
        max_pages = 100  

        while page_num <= max_pages:
            series_links, has_next_page = await get_series_from_page(session, page_num)

            if not series_links:
                logger.info(f"[!] Sayfa {page_num} boş, tarama durduruluyor.")
                break


            new_count = 0
            for link in series_links:
                if link not in all_series_links:
                    all_series_links.append(link)
                    new_count += 1

            logger.info(f"[+] Sayfa {page_num}: {new_count} yeni dizi eklendi. Toplam: {len(all_series_links)}")

            if not has_next_page:
                logger.info(f"[✓] Son sayfa ({page_num}) işlendi.")
                break

            page_num += 1


            await asyncio.sleep(0.5)

        logger.info(f"[✓] Toplam {len(all_series_links)} benzersiz dizi linki toplandı ({page_num} sayfa tarandı).")
        return all_series_links

async def get_series_metadata(session, series_url):
    """Dizi meta verilerini alır"""
    content = await fetch_page(session, series_url)
    if not content:
        return "Bilinmeyen Dizi", ""

    soup = BeautifulSoup(content, 'html.parser')


    title_element = soup.select_one(".text-bold")
    title = title_element.get_text(strip=True) if title_element else "Bilinmeyen Dizi"


    logo_url = ""
    logo_element = soup.select_one(".media-cover img")
    if logo_element:
        logo_url = logo_element.get("src") or ""

    logo_url = fix_url(logo_url)

    return title, logo_url

async def get_episode_links(session, series_url):
    """Dizi sayfasından bölüm linklerini alır"""
    content = await fetch_page(session, series_url)
    if not content:
        return []

    soup = BeautifulSoup(content, 'html.parser')
    episode_links = []


    season_buttons = soup.select(".season-menu .season-btn")

    if season_buttons:
        logger.info(f"[+] {len(season_buttons)} sezon bulundu.")


        for button in season_buttons:
            season_text = button.get_text(strip=True)


            season_num = "".join(filter(str.isdigit, season_text))
            if not season_num:
                button_id = button.get("id", "")
                if button_id:
                    season_num = str(button_id).split("-")[-1]
                else:
                    continue


            season_detail_id = f"season-{season_num}"
            season_detail = soup.select_one(f"#{season_detail_id}")

            if season_detail:
                episode_elements = season_detail.select(".uk-width-large-1-5 a")

                for ep_element in episode_elements:
                    href = ep_element.get("href")
                    if href:
                        if isinstance(href, str) and href.startswith("?"):
                            full_url = f"{series_url}{href}"
                        else:
                            full_url = fix_url(href)

                        if full_url and full_url != series_url and full_url not in [e[0] for e in episode_links]:
                            episode_links.append((full_url, int(season_num)))
    else:

        logger.info("Sezon butonu yok, fallback seçiciler kullanılıyor.")
        selectors = [
            ".bolumler .bolumtitle a", 
            ".episodes-list .episode a", 
            ".episode-item a", 
            "#season1 .uk-width-large-1-5 a"
        ]

        for selector in selectors:
            episode_elements = soup.select(selector)

            for ep_element in episode_elements:
                href = ep_element.get("href")
                if href:
                    if isinstance(href, str) and href.startswith("?"):
                        full_url = f"{series_url}{href}"
                    else:
                        full_url = fix_url(href)

                    if full_url and full_url != series_url and full_url not in [e[0] for e in episode_links]:

                        season_match = re.search(r'sezon[=-]?(\d+)', full_url, re.IGNORECASE)
                        season_num = int(season_match.group(1)) if season_match else 1
                        episode_links.append((full_url, season_num))


    normalized_episodes = normalize_episode_numbers(episode_links)

    logger.info(f"[+] Toplam {len(normalized_episodes)} bölüm bulundu ve normalize edildi.")
    return normalized_episodes

async def extract_m3u8_from_episode(session, episode_url, season_num, episode_num):
    """Bölüm sayfasından m3u8 linkini çıkarır - YENİ SİSTEM (Gujan + Playhouse + Proxy)"""
    content = await fetch_page(session, episode_url)
    if not content:
        return None, None, None

    soup = BeautifulSoup(content, 'html.parser')


    title_element = soup.select_one("title")
    episode_name = title_element.get_text(strip=True) if title_element else "Bilinmeyen Bölüm"

    logger.info(f"[*] İşleniyor: Sezon {season_num}, Bölüm {episode_num}")

    m3u8_url = None

    try:

        gujan_iframe_selectors = [
            'iframe[title="dizifunplay"]',
            'iframe[id="altPlayerFrame"]',
            'iframe[src*="gangamstyle2.dailymonvideo.biz"]'
        ]

        for selector in gujan_iframe_selectors:
            iframe_element = soup.select_one(selector)
            if iframe_element:
                src = iframe_element.get("src")
                if src and "gangamstyle2.dailymonvideo.biz" in src:
                    logger.info(f"[+] Gujan iframe bulundu: {src}")
                    m3u8_url = await extract_gujan_m3u8(session, src)
                    if m3u8_url:
                        logger.info(f"[✅] Gujan'dan M3U8 başarıyla alındı!")
                        break


        if not m3u8_url:
            logger.info("[*] Gujan bulunamadı, Playhouse sistemi deneniyor...")


            iframe_selectors = [
                'iframe[title="playhouse"]',
                'iframe[src*="playhouse.premiumvideo.click"]',
                'iframe[src*="premiumvideo.click/player"]'
            ]

            playhouse_url = None
            file_id = None


            for selector in iframe_selectors:
                iframe_element = soup.select_one(selector)
                if iframe_element:
                    src = iframe_element.get("src")
                    if src and "playhouse.premiumvideo.click" in src:
                        if src.startswith("//"):
                            src = "https:" + src
                        playhouse_url = src
                        logger.info(f"[+] Playhouse iframe bulundu: {playhouse_url}")
                        break


            if not playhouse_url:
                scripts = soup.find_all('script')
                for script in scripts:
                    script_content = script.get_text() or ""

                    hex_pattern = re.compile(r'hexToString\w*\("([a-fA-F0-9]+)"\)')
                    hex_matches = hex_pattern.findall(script_content)

                    if hex_matches:
                        logger.info(f"[+] Script içinde {len(hex_matches)} hex URL bulundu.")
                        for hex_value in hex_matches:
                            try:
                                decoded_url = bytes.fromhex(hex_value).decode('utf-8')
                                if decoded_url and "playhouse.premiumvideo.click" in decoded_url:
                                    playhouse_url = decoded_url
                                    if playhouse_url.startswith("//"):
                                        playhouse_url = "https:" + playhouse_url
                                    logger.info(f"[+] Hex'ten çözülen playhouse URL: {playhouse_url}")
                                    break
                            except Exception as e:
                                logger.error(f"[!] Hex çözme hatası: {e}")

                        if playhouse_url:
                            break


            if playhouse_url:
                playhouse_match = re.search(r'playhouse\.premiumvideo\.click/player/([a-zA-Z0-9]+)', playhouse_url)
                if playhouse_match:
                    file_id = playhouse_match.group(1)
                    logger.info(f"[+] Playhouse File ID bulundu: {file_id}")

                    working_domain, m3u8_url = await get_correct_domain_from_playhouse(session, file_id)
                    logger.info(f"[+] Bulunan domain: {working_domain}, M3U8: {m3u8_url}")


            if not m3u8_url:
                logger.info("[*] Playhouse bulunamadı, eski sistem ile deneniyor...")

                iframe_selectors_fallback = [
                    "iframe#londonIframe",
                    "iframe[src*=premiumvideo]",
                    "iframe[data-src*=premiumvideo]",
                    "iframe[src*=player]",
                    "iframe"
                ]

                for selector in iframe_selectors_fallback:
                    iframe_element = soup.select_one(selector)
                    if iframe_element:
                        src = iframe_element.get("src")
                        if not src or src == "about:blank":
                            src = iframe_element.get("data-src")

                        if src and src != "about:blank":
                            iframe_url = fix_url(src)
                            logger.info(f"[+] Fallback iframe URL: {iframe_url}")


                            premium_video_match = re.search(r'premiumvideo\.click/player\.php\?file_id=([a-zA-Z0-9]+)', iframe_url)
                            if premium_video_match:
                                file_id = premium_video_match.group(1)
                                logger.info(f"[+] Fallback File ID: {file_id}")

                                working_domain, m3u8_url = await find_working_domain_fallback(session, file_id)
                                break

    except Exception as e:
        logger.error(f"[!] Bölüm işleme genel hatası: {e}")
        return episode_name, episode_num, None


    if m3u8_url:
        m3u8_url = create_proxy_url(m3u8_url)

    return episode_name, episode_num, m3u8_url

async def process_series(all_series_links, output_filename="Blutv.m3u"):
    """Tüm dizileri tek bir dosyaya yazar"""
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=10)) as session:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")

            for series_url in all_series_links:
                try:
                    title, logo_url = await get_series_metadata(session, series_url)
                    logger.info(f"\n[+] İşleniyor: {title}")

                    normalized_episodes = await get_episode_links(session, series_url)

                    semaphore = asyncio.Semaphore(5)

                    async def process_episode(ep_url, season_num, episode_num):
                        async with semaphore:
                            return await extract_m3u8_from_episode(session, ep_url, season_num, episode_num)

                    tasks = [process_episode(ep_url, season_num, episode_num) for ep_url, season_num, episode_num in normalized_episodes]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            logger.error(f"[!] Bölüm işleme hatası: {result}")
                            continue

                        episode_name, episode_num, m3u8_url = result
                        if not m3u8_url:
                            logger.warning(f"[!] m3u8 URL bulunamadı: {normalized_episodes[i][0]}")
                            continue

                        season_num = normalized_episodes[i][1]
                        normalized_episode_num = normalized_episodes[i][2]
                        display_name = f"{title} Sezon {season_num} Bölüm {normalized_episode_num}"
                        tvg_id = sanitize_id(f"{title}_{season_num}_{normalized_episode_num}")

                        f.write(
                            f'#EXTINF:-1 tvg-name="{display_name}" '
                            f'tvg-language="Turkish" tvg-country="TR" '
                            f'tvg-id="{tvg_id}" '
                            f'tvg-logo="{logo_url}" '
                            f'group-title="{title}",{display_name}\n'
                        )
                        f.write(m3u8_url.strip() + "\n")
                        logger.info(f"[✓] {display_name} eklendi.")

                except Exception as e:
                    logger.error(f"[!] Dizi işleme hatası: {e}")
                    continue

    logger.info(f"\n[✓] {output_filename} dosyası oluşturuldu.")

async def main():
    start_time = time.time()

    series_urls = await get_series_from_homepage()
    if not series_urls:
        logger.error("[!] Dizi listesi boş, seçicileri kontrol et.")
        return

    await process_series(series_urls)

    end_time = time.time()
    logger.info(f"\n[✓] Tüm işlemler tamamlandı. Süre: {end_time - start_time:.2f} saniye")

if __name__ == "__main__":
    asyncio.run(main())
