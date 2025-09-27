import re
import requests

# Entry site
entry_url = "https://www.selcuksportshd78.is/"

try:
    entry_source = requests.get(entry_url, timeout=10).text
except Exception:
    print("Entry site alınamadı!")
    exit()

# Aktif site bul
match = re.search(r'url=(https://[^"]+)', entry_source, re.I)
if not match:
    print("Aktif site bulunamadı!")
    exit()

active_site = match.group(1)
print("Aktif site:", active_site, "\n")

# Aktif site kaynak
try:
    source = requests.get(active_site, timeout=10).text
except Exception:
    print("Site kaynak kodu alınamadı!")
    exit()

# Iframe URL bul
iframe_match = re.search(r'https://[^"]+/index\.php\?id=selcukbeinsports1', source)
if not iframe_match:
    print("Iframe URL'si bulunamadı!")
    exit()

base_url = iframe_match.group(0).replace("selcukbeinsports1", "")

# Kanal ID'leri
channels = [
    "selcukbeinsports1", "selcukbeinsports2", "selcukbeinsports3",
    "selcukbeinsports4", "selcukbeinsports5", "selcukbeinsportsmax1",
    "selcukbeinsportsmax2", "selcukssport", "selcukssport2",
    "selcuksmartspor", "selcuksmartspor2", "selcuktivibuspor1",
    "selcuktivibuspor2", "selcuktivibuspor3", "selcuktivibuspor4",
    "sssplus1", "sssplus2", "selcukobs1"
]

output_lines = []
output_lines.append("Kanal Player Linkleri:")
output_lines.append("---------------------\n")

for cid in channels:
    player_url = base_url + cid
    channel_name = "TR:" + cid.replace("selcuk", "").upper()
    line = f"{channel_name} HD: {player_url}\n"
    output_lines.append(line)

# Ekrana yaz
print("\n".join(output_lines))

# Dosyaya kaydet (repo için)
with open("tgbot.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print("\ntgbot.txt güncellendi ✅")
