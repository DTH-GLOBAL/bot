name: HD Film Bot Güncelleme

on:
  schedule:
    # Her gün Türkiye saatiyle sabah 06:00'da çalışır (UTC 03:00)
    - cron: '0 3 * * *'
  workflow_dispatch: # Elle tetiklemek için buton ekler

permissions:
  contents: write # Repoya dosya yükleyebilmesi için yazma izni şart

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Repoyu Çek (Checkout)
        uses: actions/checkout@v4

      - name: Python Kurulumu
        uses: actions/setup-python@v5
        with:
          python-version: '3.9'

      - name: Kütüphaneleri Yükle
        run: |
          python -m pip install --upgrade pip
          pip install requests beautifulsoup4

      - name: Botu Çalıştır
        run: python hdfilmizle.py

      - name: M3U Dosyasını Repoya Gönder (Commit & Push)
        run: |
          git config --global user.name 'GitHub Actions Bot'
          git config --global user.email 'actions@github.com'
          
          # Dosya var mı diye kontrol et ve ekle
          git add hdfilmizle.m3u
          
          # Değişiklik varsa commit at, yoksa hata verme devam et
          git commit -m "Otomatik M3U güncellemesi: $(date +'%Y-%m-%d')" || echo "Değişiklik yok"
          
          # Değişiklikleri repoya it
          git push
