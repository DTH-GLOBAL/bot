import requests
from bs4 import BeautifulSoup
import re
import concurrent.futures
import time

# --- AYARLAR ---
BASE_URL = "https://www.hdfilmizle.life"
OUTPUT_FILE = "hdfilmizle.m3u"

# Kaçıncı sayfadan kaçıncı sayfaya kadar çekilecek?
# Tamamını çekmek için: DIZI: 50, FILM: 975 yapın.
# Test için 1-2 yaptım.
DIZI_BASLANGIC_SAYFASI = 1
DIZI_BITIS_SAYFASI = 2  # Burayı 50 yap

FILM_BASLANGIC_SAYFASI = 1
FILM_BITIS_SAYFASI = 2  # Burayı 975 yap

# Paralel işlem sayısı (Hızlandırmak için)
WORKER_COUNT = 5

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": BASE_URL
}

def get_soup(url):
    """Verilen URL'e gider ve BeautifulSoup objesi döner."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        print(f"Hata (Bağlantı): {url} - {e}")
    return None

def extract_vidrame_m3u8(page_url):
    """Bir izleme sayfasındaki vidrame ID'sini bulur ve m3u8 linkini döner."""
    soup = get_soup(page_url)
    if not soup:
        return None

    # Iframe içindeki vidrame linkini arıyoruz
    iframe = soup.find("iframe", class_="vpx")
    if iframe:
        src = iframe.get("data-src") or iframe.get("src")
        if src and "vidrame.pro" in src:
            # ID'yi regex ile çekelim (örn: 76de1824)
            match = re.search(r"vidrame\.pro/vr/([a-zA-Z0-9]+)", src)
            if match:
                vid_id = match.group(1)
                return f"https://vidrame.pro/vr/get/{vid_id}/master.m3u8"
    return None

def process_episode(dizi_adi, poster_url, bolum_url, bolum_basligi):
    """Tek bir bölümü işler ve M3U formatında string döner."""
    full_bolum_url = BASE_URL + bolum_url if not bolum_url.startswith("http") else bolum_url
    
    m3u8_link = extract_vidrame_m3u8(full_bolum_url)
    
    if m3u8_link:
        # Örn: TR:The Irrational 1. Sezon 1. Bölüm
        tvg_name = f"TR:{dizi_adi} {bolum_basligi}"
        
        entry = (
            f'#EXTINF:-1 tvg-id="" tvg-name="{tvg_name}" '
            f'tvg-logo="{poster_url}" group-title="Dizi-Panel-2",{tvg_name}\n'
            f'{m3u8_link}\n'
        )
        print(f"[+] Dizi Eklendi: {tvg_name}")
        return entry
    else:
        print(f"[-] Video Bulunamadı: {full_bolum_url}")
        return None

def process_movie(movie_card):
    """Tek bir filmi işler ve M3U formatında string döner."""
    try:
        # Film Başlığı
        title_tag = movie_card.find("h2", class_="title")
        title = title_tag.text.strip() if title_tag else "Bilinmeyen Film"
        
        # Poster URL (data-src genelde lazyload içindir)
        img_tag = movie_card.find("img", class_="lazyload")
        poster_path = ""
        if img_tag:
            poster_path = img_tag.get("data-src") or img_tag.get("src")
        
        if poster_path and not poster_path.startswith("http"):
            poster_url = BASE_URL + poster_path
        else:
            poster_url = poster_path

        # Film Linki
        link_tag = movie_card
        href = link_tag.get("href")
        full_movie_url = BASE_URL + href if href else ""

        if full_movie_url:
            m3u8_link = extract_vidrame_m3u8(full_movie_url)
            if m3u8_link:
                tvg_name = f"TR:{title}"
                entry = (
                    f'#EXTINF:-1 tvg-id="" tvg-name="{tvg_name}" '
                    f'tvg-logo="{poster_url}" group-title="Film-Panel-2",{tvg_name}\n'
                    f'{m3u8_link}\n'
                )
                print(f"[+] Film Eklendi: {title}")
                return entry
            else:
                print(f"[-] Film Videosu Yok: {title}")
    except Exception as e:
        print(f"Hata (Film İşleme): {e}")
    return None

def get_series_from_page(page_num):
    """Dizi listeleme sayfasındaki dizileri bulur, detayına girer ve bölümleri toplar."""
    url = f"{BASE_URL}/yabanci-dizi-izle-2/page/{page_num}/"
    soup = get_soup(url)
    entries = []
    
    if not soup:
        return []

    # Dizi listesi (Yabancı Dizi izle başlığının altı)
    container = soup.find("div", id="moviesListResult")
    if not container:
        return []

    dizi_cards = container.find_all("a", class_="poster")
    
    for card in dizi_cards:
        # Dizi detaylarını al
        dizi_href = card.get("href")
        dizi_full_url = dizi_href if dizi_href.startswith("http") else BASE_URL + dizi_href
        
        # Poster
        img_tag = card.find("img", class_="lazyload")
        poster_path = img_tag.get("data-src") or img_tag.get("src") if img_tag else ""
        poster_url = BASE_URL + poster_path if poster_path and not poster_path.startswith("http") else poster_path
        
        # Başlık
        title_tag = card.find("h2", class_="title")
        dizi_adi = title_tag.text.strip() if title_tag else "Bilinmeyen Dizi"

        # Dizi detay sayfasına git (Sezon/Bölümleri bulmak için)
        detail_soup = get_soup(dizi_full_url)
        if detail_soup:
            # Sezon ve bölümleri çek
            episode_links = detail_soup.find_all("a", href=re.compile(r"/sezon-\d+/bolum-\d+/"))
            
            # Aynı bölüm linklerini tekrar çekmemek için set kullanalım (bazen mobilde vs duplicate olabilir)
            processed_urls = set()
            
            for ep_link in episode_links:
                ep_href = ep_link.get("href")
                if ep_href in processed_urls:
                    continue
                processed_urls.add(ep_href)

                # Bölüm Başlığı (örn: 1. Sezon 1. Bölüm)
                ep_title_tag = ep_link.find("h3") # Yapıya göre h3 içinde yazıyor
                ep_title = ep_title_tag.text.strip() if ep_title_tag else "Bölüm X"
                
                # Bölümü işle (İçeri girip vidrame linkini al)
                entry = process_episode(dizi_adi, poster_url, ep_href, ep_title)
                if entry:
                    entries.append(entry)
                    
    return entries

def get_movies_from_page(page_num):
    """Film listeleme sayfasındaki filmleri bulur ve işler."""
    url = f"{BASE_URL}/page/{page_num}/" if page_num > 1 else f"{BASE_URL}/" # Ana sayfa page 1 olmayabilir bazen ama sitede /page/1 de çalışıyor
    if page_num == 1: url = f"{BASE_URL}/page/1/" 

    soup = get_soup(url)
    entries = []
    
    if not soup:
        return []

    container = soup.find("div", id="moviesListResult")
    if not container:
        return []

    movie_cards = container.find_all("a", class_="poster")
    
    # Her filmi işle
    for card in movie_cards:
        entry = process_movie(card)
        if entry:
            entries.append(entry)
            
    return entries

def main():
    print("Bot başlatılıyor...")
    
    # Dosyayı oluştur ve başlığı yaz
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

    # --- DİZİLERİ ÇEK ---
    print("\n--- DİZİLER ÇEKİLİYOR ---")
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKER_COUNT) as executor:
        # Sayfaları sıraya koyuyoruz
        future_to_page = {executor.submit(get_series_from_page, i): i for i in range(DIZI_BASLANGIC_SAYFASI, DIZI_BITIS_SAYFASI + 1)}
        
        for future in concurrent.futures.as_completed(future_to_page):
            page_num = future_to_page[future]
            try:
                data = future.result()
                if data:
                    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                        for item in data:
                            f.write(item)
                    print(f"Sayfa {page_num} (Dizi) tamamlandı.")
            except Exception as exc:
                print(f"Sayfa {page_num} bir hata oluşturdu: {exc}")

    # --- FİLMLERİ ÇEK ---
    print("\n--- FİLMLER ÇEKİLİYOR ---")
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKER_COUNT) as executor:
        future_to_page = {executor.submit(get_movies_from_page, i): i for i in range(FILM_BASLANGIC_SAYFASI, FILM_BITIS_SAYFASI + 1)}
        
        for future in concurrent.futures.as_completed(future_to_page):
            page_num = future_to_page[future]
            try:
                data = future.result()
                if data:
                    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                        for item in data:
                            f.write(item)
                    print(f"Sayfa {page_num} (Film) tamamlandı.")
            except Exception as exc:
                print(f"Sayfa {page_num} bir hata oluşturdu: {exc}")

    print(f"\nİşlem bitti! Tüm veriler '{OUTPUT_FILE}' dosyasına kaydedildi.")

if __name__ == "__main__":
    main()
