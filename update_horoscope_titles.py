#!/usr/bin/env python3
import xml.etree.ElementTree as ET
from pathlib import Path

podcast_path = Path('docs/podcast.xml')
tree = ET.parse(podcast_path)
root = tree.getroot()

# Mapping des guids vers les nouveaux titres
# Basé sur les signes générés par le workflow du 8 mai
title_updates = {
    'horoscope-20260508-matin': '🌅 Taureau, Poissons & Gémeaux : l\'alliance des énergies, dans votre horoscope de ce matin du vendredi 8 mai',
    'horoscope-20260508-midi': '🌞 Bélier, Lion & Sagittaire : l\'alliance des énergies, dans votre horoscope de ce midi du vendredi 8 mai',
    'horoscope-20260508-soir': '🌙 Cancer, Scorpion & Balance : l\'alliance des énergies, dans votre horoscope de ce soir du vendredi 8 mai',
}

updated = False
for item in root.findall('.//item'):
    guid = item.find('guid')
    if guid is not None and guid.text in title_updates:
        title = item.find('title')
        if title is not None:
            title.text = title_updates[guid.text]
            print(f'✅ {guid.text}: {title.text}')
            updated = True

if updated:
    tree.write(podcast_path, encoding='utf-8', xml_declaration=True)
    print('💾 podcast.xml mis à jour')
else:
    print('⚠️ Aucun titre à mettre à jour')
