#!/usr/bin/env python3
"""Met à jour AUTOMATIQUEMENT les titres d'ÉMISSION dans podcast.xml.

Lit les fichiers docs/audio/Emissions/*.json, extrait les thèmes culturels,
puis génère des titres uniques et poétiques.

Usage: python3 update_emission_titles.py --update
"""

import re
import json
from pathlib import Path
import random
import xml.etree.ElementTree as ET

# Mots-clés pour émissions
EMISSION_KEYWORDS = {
    # Culture créole
    'résistance', 'identité', 'tradition', 'créole', 'Kalinagos', 'Arawaks',
    'esclavage', 'colonisation', 'indépendance', 'décolonisation',
    # Nature
    'flore', 'faune', 'biodiversité', 'endémique', 'écosystème',
    'forêt', 'mangrove', 'océan', 'rivière', 'cascade',
    # Symboles
    'woucou', 'roucou', 'grenn-bwa', 'hylode', 'jiramòn', 'giraumon',
    'Cascade aux Écrevisses', 'Basse-Terre',
    # Histoire
    'histoire', 'mémoire', 'ancêtres', 'esclaves', 'libération', 'combattants',
    '1848', 'abolition', 'Victor Schœlcher',
    # Musique/Art
    'gwoka', 'tambour', 'chant', 'danse', 'Battery Cremil',
    'Kassav', 'Zouk', 'Biguine', 'Mazouk',
    # Spirituel
    'vaudou', 'Kongo', 'rituel', 'esprits', 'purification',
    # Alimentation
    'boucané', 'colombo', 'accras', 'blaff', 'domi', 'piment'
}

# Suffixe pour les titres
SUFFIXES = [
    "trésors de la Guadeloupe",
    "racines et rêves",
    "mémoire et identité",
    "voyage au cœur de la culture guadeloupéenne",
    "l’histoire de la Guadeloupe",
    "découverte de la Guadeloupe",
    "la culture guadeloupéenne en lumière",
    "exploration des richesses de la Guadeloupe"
]

STOP_WORDS = {
    'le', 'la', 'les', 'ce', 'cette', 'ces', 'qui', 'que', 'de', 'des', 'du',
    'un', 'une', 'dans', 'pour', 'avec', 'sans', 'sous', 'sur', 'par',
    'au', 'aux', 'en', 'et', 'ou', 'mais', 'car', 'donc', 'or', 'ni',
    'te', 'tu', 'vous', 'se', 'sa', 'son', 'ses', 'ce matin', 'ce soir',
    'ce jour', 'ce midi', 'est', 'il', 'elle', 'ont', 'à', 'y', 'là',
    'ici', 'là-bas', 'partout', 'quelque', 'chaque', 'tout', 'toute',
    'tous', 'toutes', 'plusieurs', 'certains', 'certaines', 'dautres',
    'autres', 'même', 'aussi', 'encore', 'déjà', 'ne', 'pas', 'jamais',
    'toujours', 'souvent', 'parfois', 'comment', 'pourquoi', 'quand',
    'où', 'si', 'quelle', 'quel', 'quels', 'quelles'
}


def extract_keywords(text: str, max_keywords: int = 10) -> list:
    """Extraire les mots-clés d'un texte."""
    themes = []
    seen = set()
    
    words = re.findall(r'\b[a-zA-ZàâäéèêëïîôùûüÿæœçÀÂÄÉÈÊËÏÎÔÙÛÜŸÆŒÇ-]{3,}\b', text.lower())
    
    for word in words:
        if (word not in STOP_WORDS and 
            word in EMISSION_KEYWORDS and 
            word not in seen and 
            len(word) >= 3):
            themes.append(word)
            seen.add(word)
            if len(themes) >= max_keywords:
                break
    
    return themes


def generate_emission_title(filepath: Path) -> str:
    """Génère un titre d'émission basé sur le contenu du fichier JSON."""
    try:
        data = json.loads(filepath.read_text(encoding='utf-8'))
        text = data.get('text', '')
        existing_title = data.get('title', '')
    except:
        return None
    
    # Extraire les mots-clés du texte
    keywords = extract_keywords(text, max_keywords=10)
    
    if not keywords:
        # Fallback: utiliser le titre existant
        return existing_title
    
    # Choisir 2-3 mots-clés uniques
    num_selected = random.randint(2, min(len(keywords), 3))
    selected = random.sample(keywords, num_selected)
    
    # Capitaliser
    selected_cap = [k.capitalize() for k in selected]
    
    # Formater selon le nombre de mots
    if len(selected_cap) == 1:
        title_part = selected_cap[0]
    elif len(selected_cap) == 2:
        title_part = f"{selected_cap[0]} et {selected_cap[1]}"
    else:
        title_part = f"{selected_cap[0]}, {selected_cap[1]} et {selected_cap[2]}"
    
    # Suffixe aléatoire
    suffixe = random.choice(SUFFIXES)
    
    # Choisir un séparateur approprié
    if " et " in title_part:
        separators = [" : ", " — ", ", "]
    else:
        separators = [" : ", " — ", " et ", ", "]
    separator = random.choice(separators)
    
    return f"{title_part}{separator}{suffixe}"


def update_emission_titles():
    """Met à jour les titres d'émission dans podcast.xml."""
    podcast_path = Path('docs/podcast.xml')
    archives_dir = Path('docs/audio/Emissions')
    
    if not podcast_path.exists():
        print(f"❌ Fichier introuvable: {podcast_path}")
        return
    
    if not archives_dir.exists():
        print(f"❌ Dossier introuvable: {archives_dir}")
        return
    
    tree = ET.parse(podcast_path)
    root = tree.getroot()
    
    items = root.findall('.//item')
    updated = 0
    used_titles = set()
    
    for item in items:
        guid_elem = item.find('guid')
        title_elem = item.find('title')
        
        if guid_elem is None or title_elem is None:
            continue
        
        guid_text = guid_elem.text
        if not guid_text or 'emission-' not in guid_text:
            continue
        
        # Extraire date du guid (format: emission-2026-05-08 ou emission-20260508)
        m = re.search(r'emission-(\d{4})-(\d{2})-(\d{2})', guid_text)
        if not m:
            m = re.search(r'emission-(\d{8})', guid_text)
            if not m:
                continue
            date_str = m.group(1)
        else:
            date_str = f"{m.group(1)}{m.group(2)}{m.group(3)}"
        
        # Trouver le fichier source JSON
        json_files = list(archives_dir.glob(f'emission-{date_str}.json')) + \
                    list(archives_dir.glob(f'emission-{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}.json'))
        
        if not json_files:
            print(f"⚠️ Fichier source introuvable pour {guid_text}")
            continue
        
        source_file = json_files[0]
        
        # Générer un titre unique
        max_attempts = 50
        titre = None
        for _ in range(max_attempts):
            titre = generate_emission_title(source_file)
            if titre and titre not in used_titles:
                used_titles.add(titre)
                break
        
        if titre and titre != title_elem.text:
            title_elem.text = titre
            updated += 1
            print(f"✅ {guid_text}")
            print(f"   {titre}")
            print()
        else:
            print(f"  {guid_text}: inchangé")
    
    if updated > 0:
        tree.write(podcast_path, encoding='utf-8', xml_declaration=True)
        print(f"\n💾 {updated} titres d'émission mis à jour dans podcast.xml")
    else:
        print("\n⚠️ Aucun titre d'émission mis à jour")


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--update':
        update_emission_titles()
    else:
        print("Utilisation: python3 update_emission_titles.py --update")
        print("\nMet à jour automatiquement les titres d'émission à partir des fichiers docs/audio/Emissions/*.json")
