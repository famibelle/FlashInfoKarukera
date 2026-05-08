#!/usr/bin/env python3
import xml.etree.ElementTree as ET
from pathlib import Path
import json
import sys
sys.path.insert(0, '.')
from generate_emission import generate_catchy_title

podcast_path = Path('docs/podcast.xml')
tree = ET.parse(podcast_path)
root = tree.getroot()

# Trouver tous les items avec guid emission-
for item in root.findall('.//item'):
    guid = item.find('guid')
    if guid is not None and guid.text and 'emission-' in guid.text:
        # Extraire la date du guid
        date_str = guid.text.replace('emission-', '')
        json_path = Path(f'docs/audio/Emissions/emission-{date_str}.json')
        
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            elements = data.get('elements', {})
            text = data.get('text', '')
            new_title = generate_catchy_title(elements, text)
            
            # Mettre à jour le titre
            title_elem = item.find('title')
            if title_elem is not None:
                title_elem.text = new_title
                print(f'✅ {date_str}: {new_title}')
        else:
            print(f'⚠️ JSON introuvable: {json_path}')

# Sauvegarder le fichier modifié
tree.write(podcast_path, encoding='utf-8', xml_declaration=True)
print(f'\n💾 podcast.xml mis à jour')
