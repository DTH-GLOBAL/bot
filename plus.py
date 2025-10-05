import requests
import re
import json
from urllib.parse import urljoin
import time
import os
from datetime import datetime
import concurrent.futures

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

    def get_all_series_from_page(self, page_url):
        """Bir sayfadaki tüm dizi linklerini al"""
        try:
            response = self.session.get(page_url, timeout=10)
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

            print(f"📺 Sayfada {len(unique_links)} dizi bulundu")
            return unique_links

        except Exception as e:
            print(f"Sayfa çekilirken hata: {e}")
            return []

    def get_series_info(self, series_url):
        """Dizi bilgilerini ve bölüm listesini al"""
        try:
            response = self.session.get(series_url, timeout=10)
            response.raise_for_status()

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
                    series_title = re.sub(r'\|.*$', '', series_title).strip()
                    break

            poster_patterns = [
                r'<img[^>]*src=["\']([^"\']*series[^"\']*\.(webp|jpg|png))["\'][^>]*>',
                r'poster["\']\s*:\s*["\']([^"\']+)["\']',
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
                img_pattern = r'src="(https://dizipal24\.plus/uploads/series/[^"]+\.(webp|jpg|png))"'
                img_matches = re.findall(img_pattern, response.text)
                if img_matches:
                    poster_url = img_matches[0][0]

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
            print(f"  ✅ {series_title} - {episode_count} bölüm")

            return {
                'title': series_title,
                'poster': poster_url,
                'episodes': series_structure,
                'url': series_url
            }

        except Exception as e:
            print(f"  ❌ Dizi hatası: {e}")
            return None

    def get_m3u8_from_episode_batch(self, episode_batch):
        """Toplu şekilde m3u8 linklerini al"""
        results = []
        for episode_data in episode_batch:
            try:
                episode_url = episode_data['url']
                response = self.session.get(episode_url, timeout=10)
                
                iframe_pattern = r'<iframe[^>]*src=["\']([^"\']+)["\'][^>]*>'
                iframes = re.findall(iframe_pattern, response.text)
                
                m3u8_url = None
                for iframe_url in iframes:
                    if 'embed' in iframe_url:
                        m3u8_url = self.extract_m3u8_from_iframe(iframe_url)
                        if m3u8_url:
                            break
                
                results.append({
                    'series_title': episode_data['series_title'],
                    'poster_url': episode_data['poster_url'],
                    'season': episode_data['season'],
                    'episode': episode_data['episode'],
                    'title': episode_data['title'],
                    'm3u8_url': m3u8_url.split('?')[0] if m3u8_url else None
                })
                
            except Exception as e:
                results.append({
                    'series_title': episode_data['series_title'],
                    'poster_url': episode_data['poster_url'],
                    'season': episode_data['season'],
                    'episode': episode_data['episode'],
                    'title': episode_data['title'],
                    'm3u8_url': None
                })
                self.failed_episodes.append(episode_data['url'])
        
        return results

    def extract_m3u8_from_iframe(self, iframe_url):
        """Iframe içinden m3u8 çıkar"""
        try:
            response = self.session.get(iframe_url, timeout=10)
            
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
            return None

    def scan_all_pages_fast(self, start_page=1, end_page=108):
        """Tüm sayfalardaki dizileri hızlı şekilde tarar"""
        print(f"🔍 {start_page}. sayfadan {end_page}. sayfaya kadar hızlı taranıyor...")
        
        all_series_links = []
        
        # Önce tüm sayfalardaki linkleri topla
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            page_urls = [f"https://dizipal24.plus/diziler/{i}" for i in range(start_page, end_page + 1)]
            future_to_page = {executor.submit(self.get_all_series_from_page, url): url for url in page_urls}
            
            for future in concurrent.futures.as_completed(future_to_page):
                page_url = future_to_page[future]
                try:
                    series_links = future.result()
                    all_series_links.extend(series_links)
                    page_num = page_url.split('/')[-1]
                    print(f"✅ Sayfa {page_num} - {len(series_links)} dizi")
                except Exception as e:
                    print(f"❌ {page_url} - Hata: {e}")
        
        unique_series_links = list(set(all_series_links))
        print(f"\n📊 Toplam {len(unique_series_links)} benzersiz dizi bulundu")
        
        # Tüm dizileri paralel şekilde işle
        print("\n🎬 Diziler işleniyor...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            future_to_series = {executor.submit(self.get_series_info, url): url for url in unique_series_links}
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_series):
                series_url = future_to_series[future]
                completed += 1
                try:
                    series_info = future.result()
                    if series_info and series_info['episodes']:
                        self.found_series[series_url] = series_info
                    print(f"  📈 {completed}/{len(unique_series_links)} dizi işlendi")
                except Exception as e:
                    print(f"❌ {series_url} - İşleme hatası: {e}")
        
        print(f"\n💾 Toplam {len(self.found_series)} dizi başarıyla işlendi")
        self.save_progress()

    def generate_complete_iptv_playlist_fast(self):
        """Tüm diziler için hızlı IPTV playlist'i oluştur"""
        if not self.found_series:
            print("❌ İşlenecek dizi bulunamadı")
            return "", 0
            
        print(f"\n🎯 Hızlı IPTV Playlist oluşturuluyor...")
        print(f"📊 Toplam {len(self.found_series)} dizi bulundu")
        
        playlist = "#EXTM3U\n"
        total_episodes = 0
        
        # Tüm bölümleri topla
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
        
        print(f"📺 Toplam {len(all_episodes)} bölüm işlenecek")
        
        # Bölümleri batch'ler halinde işle
        batch_size = 15  # Daha büyük batch
        total_batches = (len(all_episodes) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(all_episodes))
            batch = all_episodes[start_idx:end_idx]
            
            print(f"🔧 Batch {batch_num + 1}/{total_batches} işleniyor ({len(batch)} bölüm)...")
            
            batch_results = self.get_m3u8_from_episode_batch(batch)
            
            successful_in_batch = 0
            for result in batch_results:
                if result['m3u8_url']:
                    clean_series_title = self.clean_text(result['series_title'])
                    clean_episode_title = self.clean_text(result['title'])
                    
                    extinf_line = f'#EXTINF:-1 tvg-id="" tvg-name="{clean_series_title} S{result["season"]:02d}E{result["episode"]:02d}" tvg-logo="{result["poster_url"]}" group-title="tum-diziler",{clean_series_title} S{result["season"]:02d}E{result["episode"]:02d} - {clean_episode_title}'
                    
                    playlist += extinf_line + '\n'
                    playlist += f"{result['m3u8_url']}\n"
                    total_episodes += 1
                    successful_in_batch += 1
            
            print(f"    ✅ Batch {batch_num + 1}: {successful_in_batch}/{len(batch)} başarılı")
            
            # Çok kısa bekleme
            if batch_num < total_batches - 1:
                time.sleep(0.02)  # Çok daha kısa bekleme
        
        if self.failed_episodes:
            print(f"⚠️ {len(self.failed_episodes)} bölümde M3U8 alınamadı")
        
        return playlist, total_episodes

    def clean_text(self, text):
        """Metni temizle ve güvenli hale getir"""
        if not text:
            return ""
        clean = re.sub(r'[^\w\sğüşıöçĞÜŞİÖÇâîûÂÎÛáéíóúÁÉÍÓÚàèìòùÀÈÌÒÙäëïöüÄËÏÖÜ]', '', text)
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
        print(f"💾 İlerleme kaydedildi: {len(self.found_series)} dizi")

    def load_progress(self):
        """Kaydedilmiş ilerlemeyi yükle"""
        try:
            with open('dizipal_progress.json', 'r', encoding='utf-8') as f:
                progress = json.load(f)
                self.found_series = progress['found_series']
                print(f"📁 Önceki ilerleme yüklendi: {len(self.found_series)} dizi")
        except FileNotFoundError:
            print("📁 Önceki ilerleme bulunamadı, sıfırdan başlanıyor")

    def save_to_github(self, playlist_content):
        """Playlist'i dosyaya kaydet"""
        try:
            filename = "plus-diziler.m3u"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(playlist_content)
            
            stats = f"\n# 🎬 Oluşturulma Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            stats += f"# 📊 Toplam Dizi: {len(self.found_series)}\n"
            
            total_eps = 0
            for series in self.found_series.values():
                for season in series['episodes'].values():
                    total_eps += len(season)
            
            stats += f"# 📺 Toplam Bölüm: {total_eps}\n"
            stats += f"# ✅ Başarılı Bölüm: {playlist_content.count('#EXTINF')}\n"
            stats += f"# ⚠️ Başarısız Bölüm: {len(self.failed_episodes)}\n"
            
            with open(filename, "a", encoding="utf-8") as f:
                f.write(stats)
            
            print(f"💾 Playlist '{filename}' dosyasına kaydedildi")
            return True
        except Exception as e:
            print(f"❌ Dosya kaydedilirken hata: {e}")
            return False

def main():
    print("🚀 Dizipal24 Plus HIZLI IPTV Playlist Oluşturucu")
    print("=" * 60)
    print(f"⏰ Başlangıç: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    extractor = DizipalMasterExtractor()
    
    extractor.load_progress()
    
    # TÜM 108 SAYFA
    start_page = 1
    end_page = 108
    
    extractor.scan_all_pages_fast(start_page, end_page)
    
    playlist, total_episodes = extractor.generate_complete_iptv_playlist_fast()
    
    if playlist and total_episodes > 0:
        success = extractor.save_to_github(playlist)
        
        if success:
            print(f"\n{'='*60}")
            print("🎉 HIZLI IPTV PLAYLIST OLUŞTURULDU!")
            print(f"📊 Toplam {len(extractor.found_series)} dizi")
            print(f"📺 Toplam {total_episodes} bölüm")
            print(f"💾 Kaydedildi: plus-diziler.m3u")
            print(f"⏰ Bitiş: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
        else:
            print("\n❌ Playlist dosyaya kaydedilemedi")
    else:
        print("\n❌ Playlist oluşturulamadı")

if __name__ == "__main__":
    main()
