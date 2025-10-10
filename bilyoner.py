#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import os

def aktif_domain_bul():
    """
    1️⃣ 1..199 arası aktif domaini bulur.
    """
    for i in range(1, 200):
        domain = f"https://bilyonersport{i}.com/"
        try:
            r = requests.get(domain, timeout=3)
            if r.status_code == 200 and "channel-list" in r.text:
                print(f"✅ Aktif domain bulundu: {domain}")
                return domain
        except:
            pass
    print("❌ Aktif domain bulunamadı.")
    return None

def kanallari_cek(domain):
    """
    2️⃣ Kanal isimleri ve M3U8 linklerini çeker.
    """
    print("🔍 Kanal listesi çekiliyor...")
    try:
        r = requests.get(domain, timeout=5)
        html = r.text
    except Exception as e:
        print("⚠️ Sayfa çekilemedi:", e)
        return []

    # Esnek regex - domain sabit değil
    hrefs = re.findall(r'href="([^"]+index\.m3u8[^"]*)"', html)
    names = re.findall(r'<div class="channel-name">(.*?)</div>', html)

    if not hrefs or not names:
        print("⚠️ Kanal listesi bulunamadı.")
        return []

    kanallar = []
    for name, link in zip(names, hrefs):
        kanallar.append((name.strip(), link.strip()))
    return kanallar

def m3u_olustur(kanallar, referer):
    """
    3️⃣ M3U dosyasını oluşturur ve /sdcard/ içine kaydeder.
    """
    path = os.path.join("/sdcard", "bilyoner_kanallar.m3u")
    print(f"💾 M3U dosyası oluşturuluyor: {path}")

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for name, url in kanallar:
                f.write(f'#EXTINF:-1 tvg-name="{name}" group-title="BilyonerSport",{name}\n')
                f.write(f'#EXTVLCOPT:http-referrer={referer}\n')
                f.write(f"{url}\n\n")
        print(f"✅ {len(kanallar)} kanal eklendi!")
        print(f"📁 Dosya kaydedildi: {path}")
    except Exception as e:
        print("❌ M3U dosyası oluşturulamadı:", e)

def main():
    aktif = aktif_domain_bul()
    if aktif:
        kanallar = kanallari_cek(aktif)
        if kanallar:
            m3u_olustur(kanallar, aktif)
        else:
            print("⚠️ Kanal bulunamadı.")
    else:
        print("⚠️ Aktif domain bulunamadı.")

if __name__ == "__main__":
    main()
