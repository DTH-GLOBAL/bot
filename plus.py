import requests
import re
import json
from urllib.parse import urljoin
import time
import os
from datetime import datetime
import concurrent.futures
import threading

class DizipalMasterExtractor:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://dizipal24.plus/'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.found_series = {}
        self.failed_episodes = []
        self.lock = threading.Lock()
        self.processed_count = 0
        self.current_operation = "Başlatılıyor..."

    def update_status(self, message):
        """Anlık durumu güncelle"""
        self.current_operation = message
        print(f"🔄 {message}")

    def get_all_series_from_page(self, page_url):
        """Bir sayfadaki tüm dizi linklerini al"""
        try:
            page_num = page_url.split('/')[-1]
            self.update_status(f"Sayfa {page_num} çekiliyor...")
            
            response = self.session.get(page_url, timeout=5)
            response.raise_for_status()

            series_pattern = r'<a\s+class="[^"]*block no-underline[^"]*"\s+href="([^"]+)"'
            series_links = re.findall(series_pattern, response.text)

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

            self.update_status(f"Sayfa {page_num} tamamlandı - {len(unique_links)} dizi")
            return unique_links

        except Exception as e:
            self.update_status(f"Sayfa {page_url.split('/')[-1]} hatası: {e}")
            return []

    def get_series_info_batch(self, series_urls_batch):
        """Toplu şekilde dizi bilgilerini al"""
        batch_results = []
        batch_num = hash(str(series_urls_batch)) % 1000
        
        self.update_status(f"Dizi batch #{batch_num} işleniyor ({len(series_urls_batch)} dizi)...")
        
        for i, series_url in enumerate(series_urls_batch):
            try:
                dizi_adi = series_url.split('/')[-1]
                self.update_status(f"Dizi: {dizi_adi} ({i+1}/{len(series_urls_batch)})")
                
                response = self.session.get(series_url, timeout=5)
                response.raise_for_status()

                # Dizi ismini bul
                title_match = re.search(r'<title>([^<]+)', response.text)
                series_title = "Bilinmeyen Dizi"
                if title_match:
                    series_title = title_match.group(1).strip()
                    series_title = re.sub(r'\|.*$', '', series_title).strip()

                # Poster bul
                poster_match = re.search(r'meta[^>]*property="og:image"[^>]*content="([^"]+)"', response.text)
                poster_url = poster_match.group(1) if poster_match else ""

                # Bölüm linklerini bul
                episode_pattern = r'<a\s+class="[^"]*block truncate[^"]*"\s+href="([^"]*sezon-(\d+)/bolum-(\d+)[^"]*)"[^>]*>([^<]*)</a>'
                episodes = re.findall(episode_pattern, response.text)

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
                
                if series_structure:
                    batch_results.append({
                        'url': series_url,
                        'title': series_title,
                        'poster': poster_url,
                        'episodes': series_structure
                    })
                    
                    self.update_status(f"✅ {series_title} - {episode_count} bölüm eklendi")

            except Exception as e:
                self.update_status(f"❌ Dizi hatası: {series_url.split('/')[-1]}")
                continue
        
        self.update_status(f"✅ Dizi batch #{batch_num} tamamlandı - {len(batch_results)} başarılı")
        return batch_results

    def extract_m3u8_from_episode(self, episode_data):
        """Tek bir bölümden m3u8 çıkar"""
        try:
            series_short = episode_data['series_title'][:20] + "..." if len(episode_data['series_title']) > 20 else episode_data['series_title']
            self.update_status(f"Bölüm: {series_short} S{episode_data['season']:02d}E{episode_data['episode']:02d}")
            
            response = self.session.get(episode_data['url'], timeout=5)
            
            # Iframe URL'sini bul
            iframe_match = re.search(r'<iframe[^>]*src="([^"]+)"', response.text)
            if not iframe_match:
                return None
                
            iframe_url = iframe_match.group(1)
            if 'embed' not in iframe_url:
                return None

            # Iframe içeriğini çek
            self.update_status(f"  Iframe çekiliyor: {series_short}...")
            iframe_response = self.session.get(iframe_url, timeout=5)
            
            # M3U8 pattern'leri
            m3u8_match = re.search(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', iframe_response.text)
            if m3u8_match:
                self.update_status(f"  ✅ M3U8 bulundu: {series_short}")
                return m3u8_match.group(1).split('?')[0]
            
            self.update_status(f"  ❌ M3U8 bulunamadı: {series_short}")
            return None

        except Exception as e:
            self.update_status(f"  ❌ Bölüm hatası: {series_short}")
            return None

    def process_episodes_batch(self, episodes_batch):
        """Bölüm batch'ini işle"""
        results = []
        batch_size = len(episodes_batch)
        
        self.update_status(f"🎬 Bölüm batch işleniyor ({batch_size} bölüm)...")
        
        for i, episode_data in enumerate(episodes_batch):
            m3u8_url = self.extract_m3u8_from_episode(episode_data)
            
            with self.lock:
                self.processed_count += 1
                progress_percent = (self.processed_count / self.total_episodes) * 100
                
                if self.processed_count % 10 == 0 or i == batch_size - 1:
                    self.update_status(f"📊 Progress: {self.processed_count}/{self.total_episodes} ({progress_percent:.1f}%)")
            
            if m3u8_url:
                results.append({
                    'series_title': episode_data['series_title'],
                    'poster_url': episode_data['poster_url'],
                    'season': episode_data['season'],
                    'episode': episode_data['episode'],
                    'title': episode_data['title'],
                    'm3u8_url': m3u8_url
                })
            else:
                self.failed_episodes.append(episode_data['url'])
        
        success_count = len(results)
        self.update_status(f"✅ Bölüm batch tamamlandı - {success_count}/{batch_size} başarılı")
        return results

    def scan_all_pages_ultra_fast(self, start_page=1, end_page=108):
        """Tüm sayfalardaki dizileri ultra hızlı tarar"""
        self.update_status(f"🔍 {start_page}. sayfadan {end_page}. sayfaya kadar ULTRA HIZLI taranıyor...")
        
        all_series_links = []
        
        # Tüm sayfaları paralel çek
        self.update_status("📄 Tüm sayfalar paralel çekiliyor...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            page_urls = [f"https://dizipal24.plus/diziler/{i}" for i in range(start_page, end_page + 1)]
            future_to_page = {executor.submit(self.get_all_series_from_page, url): i+1 for i, url in enumerate(page_urls)}
            
            completed_pages = 0
            for future in concurrent.futures.as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    series_links = future.result()
                    all_series_links.extend(series_links)
                    completed_pages += 1
                    progress = (completed_pages / len(page_urls)) * 100
                    self.update_status(f"📄 Sayfa {page_num} tamamlandı - {completed_pages}/{len(page_urls)} ({progress:.1f}%)")
                except Exception:
                    completed_pages += 1
                    self.update_status(f"❌ Sayfa {page_num} hatası")
        
        unique_series_links = list(set(all_series_links))
        self.update_status(f"📊 Toplam {len(unique_series_links)} benzersiz dizi bulundu")
        
        # Dizileri büyük batch'ler halinde işle
        self.update_status("🎬 Tüm diziler işleniyor...")
        batch_size = 50
        all_series_info = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            series_batches = [unique_series_links[i:i + batch_size] for i in range(0, len(unique_series_links), batch_size)]
            future_to_batch = {executor.submit(self.get_series_info_batch, batch): i+1 for i, batch in enumerate(series_batches)}
            
            completed_batches = 0
            for future in concurrent.futures.as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                try:
                    batch_results = future.result()
                    all_series_info.extend(batch_results)
                    completed_batches += 1
                    progress = (completed_batches / len(series_batches)) * 100
                    self.update_status(f"🎬 Dizi batch {batch_num} tamamlandı - {completed_batches}/{len(series_batches)} ({progress:.1f}%)")
                except Exception as e:
                    completed_batches += 1
                    self.update_status(f"❌ Dizi batch {batch_num} hatası")
        
        # Dizileri kaydet
        for series_info in all_series_info:
            self.found_series[series_info['url']] = {
                'title': series_info['title'],
                'poster': series_info['poster'],
                'episodes': series_info['episodes']
            }
        
        self.update_status(f"💾 Toplam {len(self.found_series)} dizi başarıyla işlendi")
        self.save_progress()

    def generate_complete_iptv_playlist_ultra_fast(self):
        """Tüm diziler için ultra hızlı IPTV playlist'i oluştur"""
        if not self.found_series:
            self.update_status("❌ İşlenecek dizi bulunamadı")
            return "", 0
            
        self.update_status(f"\n🎯 ULTRA HIZLI IPTV Playlist oluşturuluyor...")
        self.update_status(f"📊 Toplam {len(self.found_series)} dizi bulundu")
        
        # Tüm bölümleri topla
        self.update_status("📺 Tüm bölümler toplanıyor...")
        all_episodes = []
        for series_url, series_info in self.found_series.items():
            series_title = series_info['title']
            poster_url = series_info['poster'] or ""
            
            for season in sorted(series_info['episodes'].keys()):
                for episode in sorted(series_info['episodes'][season].keys()):
                    episode_data = series_info['episodes'][season][episode]
                    all_episodes.append({
                        'series_title': series_title,
                        'poster_url': poster_url,
                        'season': season,
                        'episode': episode,
                        'title': episode_data['title'],
                        'url': episode_data['url']
                    })
        
        self.total_episodes = len(all_episodes)
        self.update_status(f"📺 Toplam {self.total_episodes} bölüm işlenecek")
        
        playlist = "#EXTM3U\n"
        total_successful = 0
        
        # Bölümleri ÇOK BÜYÜK batch'ler halinde işle
        batch_size = 100
        all_results = []
        
        self.update_status("🚀 Bölümler ultra hızlı işleniyor...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            episode_batches = [all_episodes[i:i + batch_size] for i in range(0, len(all_episodes), batch_size)]
            future_to_batch = {executor.submit(self.process_episodes_batch, batch): i+1 for i, batch in enumerate(episode_batches)}
            
            completed_batches = 0
            for future in concurrent.futures.as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                try:
                    batch_results = future.result()
                    all_results.extend(batch_results)
                    completed_batches += 1
                    progress = (completed_batches / len(episode_batches)) * 100
                    self.update_status(f"🚀 Bölüm batch {batch_num} tamamlandı - {completed_batches}/{len(episode_batches)} ({progress:.1f}%)")
                except Exception:
                    completed_batches += 1
                    self.update_status(f"❌ Bölüm batch {batch_num} hatası")
        
        # Sonuçları playlist'e yaz
        self.update_status("💾 Playlist'e yazılıyor...")
        for result in all_results:
            clean_series_title = self.clean_text(result['series_title'])
            clean_episode_title = self.clean_text(result['title'])
            
            extinf_line = f'#EXTINF:-1 tvg-id="" tvg-name="{clean_series_title} S{result["season"]:02d}E{result["episode"]:02d}" tvg-logo="{result["poster_url"]}" group-title="tum-diziler",{clean_series_title} S{result["season"]:02d}E{result["episode"]:02d} - {clean_episode_title}'
            
            playlist += extinf_line + '\n'
            playlist += f"{result['m3u8_url']}\n"
            total_successful += 1
        
        self.update_status(f"⚠️ {len(self.failed_episodes)} bölümde M3U8 alınamadı")
        
        return playlist, total_successful

    def clean_text(self, text):
        """Metni temizle"""
        if not text:
            return ""
        clean = re.sub(r'[^\w\sğüşıöçĞÜŞİÖÇ]', '', text)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()

    def save_progress(self):
        """İlerlemeyi kaydet"""
        progress = {
            'found_series': self.found_series,
            'total_series': len(self.found_series)
        }
        with open('dizipal_progress.json', 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

    def load_progress(self):
        """Kaydedilmiş ilerlemeyi yükle"""
        try:
            with open('dizipal_progress.json', 'r', encoding='utf-8') as f:
                progress = json.load(f)
                self.found_series = progress['found_series']
                self.update_status(f"📁 Önceki ilerleme yüklendi: {len(self.found_series)} dizi")
        except FileNotFoundError:
            self.update_status("📁 Önceki ilerleme bulunamadı")

    def save_to_github(self, playlist_content):
        """Playlist'i dosyaya kaydet"""
        try:
            filename = "plus-diziler.m3u"
            self.update_status(f"💾 {filename} dosyasına kaydediliyor...")
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(playlist_content)
            
            stats = f"\n# 🎬 Oluşturulma Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            stats += f"# 📊 Toplam Dizi: {len(self.found_series)}\n"
            stats += f"# 📺 Toplam Bölüm: {self.total_episodes}\n"
            stats += f"# ✅ Başarılı Bölüm: {playlist_content.count('#EXTINF')}\n"
            stats += f"# ⚠️ Başarısız Bölüm: {len(self.failed_episodes)}\n"
            
            with open(filename, "a", encoding="utf-8") as f:
                f.write(stats)
            
            self.update_status("✅ Dosya başarıyla kaydedildi")
            return True
        except Exception as e:
            self.update_status(f"❌ Dosya kaydedilirken hata: {e}")
            return False

def main():
    print("🚀 Dizipal24 Plus ULTRA HIZLI IPTV Playlist Oluşturucu")
    print("=" * 60)
    start_time = datetime.now()
    print(f"⏰ Başlangıç: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    extractor = DizipalMasterExtractor()
    extractor.load_progress()
    
    # ULTRA HIZLI tarama - TÜM 108 SAYFA
    extractor.scan_all_pages_ultra_fast(1, 108)
    
    # ULTRA HIZLI playlist oluştur
    playlist, total_episodes = extractor.generate_complete_iptv_playlist_ultra_fast()
    
    if playlist and total_episodes > 0:
        success = extractor.save_to_github(playlist)
        
        if success:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() / 60
            print(f"\n{'='*60}")
            print("🎉 ULTRA HIZLI IPTV PLAYLIST OLUŞTURULDU!")
            print(f"📊 Toplam {len(extractor.found_series)} dizi")
            print(f"📺 Toplam {total_episodes} bölüm")
            print(f"⏱️  Süre: {duration:.1f} dakika")
            print(f"💾 Kaydedildi: plus-diziler.m3u")
            print(f"{'='*60}")
    else:
        print("\n❌ Playlist oluşturulamadı")

if __name__ == "__main__":
    main()
