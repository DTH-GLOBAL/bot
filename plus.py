import requests
import re
import json
from urllib.parse import urljoin
import time
import os
from datetime import datetime

class DizipalMasterExtractor:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://dizipal24.plus/'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.found_series = {}

    def get_all_series_from_page(self, page_url):
        """Bir sayfadaki tüm dizi linklerini al"""
        try:
            print(f"Sayfa çekiliyor: {page_url}")
            response = self.session.get(page_url)
            response.raise_for_status()

            # Daha esnek pattern - tüm block no-underline linkleri al
            series_pattern = r'<a\s+class="[^"]*block no-underline[^"]*"\s+href="([^"]+)"'
            series_links = re.findall(series_pattern, response.text)

            # Benzersiz linkleri al ve sadece dizi linklerini filtrele
            unique_links = []
            for link in set(series_links):
                if '/dizi/' in link:
                    if link.startswith('/'):
                        full_url = urljoin('https://dizipal24.plus', link)
                    elif link.startswith('https://dizipal24.plus/dizi/'):
                        full_url = link
                    else:
                        continue
                    unique_links.append(full_url)

            print(f"📺 Sayfada {len(unique_links)} dizi bulundu")
            
            return unique_links

        except Exception as e:
            print(f"Sayfa çekilirken hata: {e}")
            return []

    def get_series_info(self, series_url):
        """Dizi bilgilerini ve bölüm listesini al"""
        try:
            print(f"  Dizi sayfası çekiliyor: {series_url}")
            response = self.session.get(series_url)
            response.raise_for_status()

            # Dizi ismini bul
            title_patterns = [
                r'<title>([^<]+)',
                r'<h1[^>]*>([^<]+)</h1>',
                r'meta[^>]*property="og:title"[^>]*content="([^"]+)"'
            ]
            
            series_title = "Bilinmeyen Dizi"
            for pattern in title_patterns:
                match = re.search(pattern, response.text)
                if match:
                    series_title = match.group(1).strip()
                    # Temizleme
                    series_title = re.sub(r'\|.*$', '', series_title).strip()
                    break

            print(f"  📝 Dizi adı: {series_title}")

            # Poster resmini bul
            poster_patterns = [
                r'<img[^>]*src=["\']([^"\']*series[^"\']*\.(webp|jpg|png))["\'][^>]*>',
                r'poster["\']\s*:\s*["\']([^"\']+)["\']',
                r'cover["\']\s*:\s*["\']([^"\']+)["\']',
                r'meta[^>]*property="og:image"[^>]*content=["\']([^"\']+)["\']'
            ]

            poster_url = None
            for pattern in poster_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                if matches:
                    poster_url = matches[0][0] if isinstance(matches[0], tuple) else matches[0]
                    if not poster_url.startswith('http'):
                        poster_url = urljoin(series_url, poster_url)
                    break

            if not poster_url:
                # Alternatif arama - series klasöründeki resimler
                img_pattern = r'src="(https://dizipal24\.plus/uploads/series/[^"]+\.(webp|jpg|png))"'
                img_matches = re.findall(img_pattern, response.text)
                if img_matches:
                    poster_url = img_matches[0][0]

            print(f"  📸 Poster: {poster_url}")

            # Bölüm linklerini bul - <a class="block truncate " href= pattern'i ile
            episode_pattern = r'<a\s+class="[^"]*block truncate[^"]*"\s+href="([^"]*sezon-(\d+)/bolum-(\d+)[^"]*)"[^>]*>([^<]*)</a>'
            episodes = re.findall(episode_pattern, response.text)

            # Dizi yapısını oluştur
            series_structure = {}
            for episode_url, season_num, episode_num, episode_title in episodes:
                if not episode_url.startswith('http'):
                    episode_url = urljoin(series_url, episode_url)
                
                season_num = int(season_num)
                episode_num = int(episode_num)
                episode_title = episode_title.strip()

                if season_num not in series_structure:
                    series_structure[season_num] = {}

                series_structure[season_num][episode_num] = {
                    'url': episode_url,
                    'title': episode_title
                }

            episode_count = sum(len(seasons) for seasons in series_structure.values())
            print(f"  📊 {episode_count} bölüm bulundu")

            return {
                'title': series_title,
                'poster': poster_url,
                'episodes': series_structure,
                'url': series_url
            }

        except Exception as e:
            print(f"  ❌ Dizi bilgisi alınırken hata: {e}")
            return None

    def get_m3u8_from_episode(self, episode_url):
        """Bölüm sayfasından m3u8 linkini al"""
        try:
            response = self.session.get(episode_url)
            
            # Iframe URL'sini bul
            iframe_pattern = r'<iframe[^>]*src=["\']([^"\']+)["\'][^>]*>'
            iframes = re.findall(iframe_pattern, response.text)
            
            for iframe_url in iframes:
                if 'embed' in iframe_url:
                    print(f"    Iframe bulundu: {iframe_url}")
                    m3u8 = self.extract_m3u8_from_iframe(iframe_url)
                    if m3u8:
                        # Token'ı temizle
                        clean_m3u8 = m3u8.split('?')[0]
                        return clean_m3u8
            return None

        except Exception as e:
            print(f"    ❌ Bölüm m3u8 alınırken hata: {e}")
            return None

    def extract_m3u8_from_iframe(self, iframe_url):
        """Iframe içinden m3u8 çıkar"""
        try:
            response = self.session.get(iframe_url)
            
            # M3U8 pattern'leri
            m3u8_patterns = [
                r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
                r'source\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
                r'file\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            ]
            
            for pattern in m3u8_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                if matches:
                    return matches[0]
            
            return None

        except Exception as e:
            print(f"    ❌ Iframe m3u8 alınırken hata: {e}")
            return None

    def scan_all_pages(self, start_page=1, end_page=108):
        """Tüm sayfalardaki dizileri tarar"""
        print(f"🔍 {start_page}. sayfadan {end_page}. sayfaya kadar taranıyor...")
        
        for page_num in range(start_page, end_page + 1):
            page_url = f"https://dizipal24.plus/diziler/{page_num}"
            print(f"\n{'='*60}")
            print(f"📄 Sayfa {page_num} işleniyor...")
            print(f"{'='*60}")
            
            series_links = self.get_all_series_from_page(page_url)
            
            if not series_links:
                print("  ❌ Bu sayfada dizi bulunamadı")
                continue
            
            for series_url in series_links:
                # Daha önce işlenmiş mi kontrol et
                if series_url in self.found_series:
                    print(f"  ⏩ Önceden işlenmiş, atlanıyor")
                    continue
                    
                print(f"\n🎬 Dizi işleniyor: {series_url}")
                series_info = self.get_series_info(series_url)
                
                if series_info and series_info['episodes']:
                    self.found_series[series_url] = series_info
                    episode_count = sum(len(seasons) for seasons in series_info['episodes'].values())
                    print(f"  ✅ '{series_info['title']}' - {episode_count} bölüm eklendi")
                else:
                    print(f"  ❌ Dizi bilgileri alınamadı veya bölüm bulunamadı")
                
                # Kısa bekleme
                time.sleep(1)
            
            # Sayfa arası bekleme
            time.sleep(2)

    def generate_complete_iptv_playlist(self):
        """Tüm diziler için IPTV playlist'i oluştur"""
        if not self.found_series:
            print("❌ İşlenecek dizi bulunamadı")
            return "", 0
            
        print(f"\n🎯 IPTV Playlist oluşturuluyor...")
        print(f"📊 Toplam {len(self.found_series)} dizi bulundu")
        
        playlist = "#EXTM3U\n"
        total_episodes = 0

        for series_url, series_info in self.found_series.items():
            series_title = series_info['title']
            poster_url = series_info['poster']
            
            print(f"\n📀 {series_title} işleniyor...")
            
            episode_added = 0
            for season in sorted(series_info['episodes'].keys()):
                for episode in sorted(series_info['episodes'][season].keys()):
                    episode_data = series_info['episodes'][season][episode]
                    episode_url = episode_data['url']
                    episode_title = episode_data['title']
                    
                    print(f"  🎬 S{season:02d}E{episode:02d}: {episode_title}")
                    
                    m3u8_url = self.get_m3u8_from_episode(episode_url)
                    
                    if m3u8_url:
                        # IPTV formatında entry oluştur - group-title="tum-diziler"
                        clean_series_title = re.sub(r'[^\w\s-]', '', series_title)
                        playlist += f'#EXTINF:-1 tvg-id="" tvg-name="{clean_series_title} S{season:02d}E{episode:02d}" tvg-logo="{poster_url}" group-title="tum-diziler",{clean_series_title} S{season:02d}E{episode:02d} - {episode_title}\n'
                        playlist += f"{m3u8_url}\n"
                        total_episodes += 1
                        episode_added += 1
                        print(f"    ✅ M3U8 eklendi")
                    else:
                        print(f"    ❌ M3U8 bulunamadı")
                    
                    # Kısa bekleme
                    time.sleep(0.5)
            
            print(f"  📈 {episode_added} bölüm eklendi")

        return playlist, total_episodes

    def save_to_github(self, playlist_content):
        """Playlist'i dosyaya kaydet (GitHub için)"""
        try:
            filename = "plus-diziler.m3u"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(playlist_content)
            
            # İstatistik bilgisi ekle
            stats = f"\n# 🎬 Oluşturulma Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            stats += f"# 📊 Toplam Dizi: {len(self.found_series)}\n"
            stats += f"# 📺 Toplam Bölüm: {sum(len(seasons) for series in self.found_series.values() for seasons in series['episodes'].values())}\n"
            
            with open(filename, "a", encoding="utf-8") as f:
                f.write(stats)
            
            print(f"💾 Playlist '{filename}' dosyasına kaydedildi")
            return True
        except Exception as e:
            print(f"❌ Dosya kaydedilirken hata: {e}")
            return False

def main():
    print("🚀 Dizipal24 Plus IPTV Playlist Oluşturucu")
    print("=" * 60)
    print(f"⏰ Başlangıç: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    extractor = DizipalMasterExtractor()
    
    # Tüm sayfaları tara
    start_page = 1
    end_page = 10  # Tüm sayfalar
    
    extractor.scan_all_pages(start_page, end_page)
    
    # IPTV playlist oluştur
    playlist, total_episodes = extractor.generate_complete_iptv_playlist()
    
    if playlist and total_episodes > 0:
        # Dosyaya kaydet
        success = extractor.save_to_github(playlist)
        
        if success:
            print(f"\n{'='*60}")
            print("🎉 TÜM DİZİLER İÇİN IPTV PLAYLIST OLUŞTURULDU!")
            print(f"📊 Toplam {len(extractor.found_series)} dizi")
            print(f"📺 Toplam {total_episodes} bölüm")
            print(f"💾 Kaydedildi: plus-diziler.m3u")
            print(f"⏰ Bitiş: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
        else:
            print("\n❌ Playlist dosyaya kaydedilemedi")
    else:
        print("\n❌ Playlist oluşturulamadı veya bölüm bulunamadı")

if __name__ == "__main__":
    main()
