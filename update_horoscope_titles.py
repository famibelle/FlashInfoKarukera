#!/usr/bin/env python3
"""Met à jour AUTOMATIQUEMENT les titres d'HOROSCOPE dans podcast.xml.

Lit les fichiers archives/horoscope/*.txt, extrait les signes et leurs thèmes,
puis génère des titres uniques avec corrélations inattendues.

Usage: python3 update_horoscope_titles.py --update
"""

import re
from pathlib import Path
import random
import xml.etree.ElementTree as ET

# Symboles du zodiaque
SIGNE_EMOJIS = {
    "Bélier": "♈", "Taureau": "♉", "Gémeaux": "♊", "Cancer": "♋",
    "Lion": "♌", "Vierge": "♍", "Balance": "♎", "Scorpion": "♏",
    "Sagittaire": "♐", "Capricorne": "♑", "Verseau": "♒", "Poissons": "♓"
}

# Mots-clés astrologiques
ASTRO_KEYWORDS = {
    'avocatier', 'vanille', 'vaniy', 'awokasié', 'manyòk', 'colibri',
    'gommier', 'palétuvier', 'balisier', 'malomé', 'corossol', 'manguier',
    'piment', 'roucou', 'woucou', 'cacao', 'pain', 'cassave', 'banane', 'goyave',
    'ananas', 'noix', 'coco', 'citron', 'orange', 'pomdó',
    'bœuf', 'crabbe', 'zandoli', 'fwou-fwou', 'foufou', 'igwann', 'karet',
    'kabrit', 'ouassou', 'wasou', 'gwo', 'tortue', 'touloulou',
    'Soufrière', 'mangrove', 'marée', 'océan', 'morne', 'plage',
    'rivière', 'montagne', 'cascade', 'source', 'rocher',
    'arc-en-ciel', 'éclair', 'tonnerre', 'rosée', 'brume', 'nuage',
    'brouillard', 'pluie', 'saveur', 'bouillon', 'tambour', 'gwoka',
    'ancêtres', 'sage', 'germe', 'dachine', 'alpinia', 'sucrier', 'marakoudja',
    'pirogue', 'kalbasi', 'malakié', 'mangouste', 'scarabée', 'Hercule', 'crabier',
    'savane', 'forêt', 'chute', 'Carbet', 'conque', 'kokoye',
    'chadon', 'beni', 'koko', 'matoutou', 'ongée',
    'ti flambeau', 'kokotié', 'sève', 'foumi manyok', 'sitwèl', 'papillon',
    'Manman dlo', 'Touloulou', 'Bèf a Bos', 'Hèrkil'
}

# Templates de corrélation
CORRELATION_TEMPLATES = [
    "Quand {} rencontre {}",
    "Entre {} et {}",
    "L’alliance de {} et {}",
    "Quand {} croise {}",
    "{} et {}, une rencontre inattendue",
    "Le dialogue entre {} et {}",
    "Quand {} répond à {}",
    "{} et {} s’entrelacent",
    "La rencontre de {} et {}",
    "Ce que {} murmure à {}",
    "Ce que {} dit à {}",
    "{} et {} en harmonie",
    "L’histoire de {} et {}",
    "Quand {} danse avec {}"
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
    'où', 'si', 'quelle', 'quel', 'quels', 'quelles',
    'respirer', 'respire', 'attendre', 'attendez', 'attend', 'mûrir', 'mûrit'
}


def extract_keywords(text: str, max_keywords: int = 8) -> list:
    """Extraire les mots-clés d'un texte."""
    themes = []
    seen = set()
    
    words = re.findall(r'\b[a-zA-ZàâäéèêëïîôùûüÿæœçÀÂÄÉÈÊËÏÎÔÙÛÜŸÆŒÇ-]{3,}\b', text.lower())
    
    for word in words:
        if (word not in STOP_WORDS and 
            word in ASTRO_KEYWORDS and 
            word not in seen and 
            len(word) >= 3):
            themes.append(word)
            seen.add(word)
            if len(themes) >= max_keywords:
                break
    
    return themes


def get_month_name(month: str) -> str:
    """Convertir numéro de mois en nom."""
    months = {
        '01': 'janvier', '02': 'février', '03': 'mars', '04': 'avril',
        '05': 'mai', '06': 'juin', '07': 'juillet', '08': 'août',
        '09': 'septembre', '10': 'octobre', '11': 'novembre', '12': 'décembre'
    }
    return months.get(month, month)


def generate_horoscope_title(filepath: Path, edition: str, date_str: str) -> str:
    """Génère un titre d'horoscope basé sur le contenu du fichier."""
    content = filepath.read_text(encoding='utf-8')
    
    # Trouver les signes
    signes = []
    for line in content.split('\n'):
        if 'Signes' in line and ':' in line:
            signes_str = line.split(':')[-1].strip()
            tous_les_signes = ['Bélier', 'Taureau', 'Gémeaux', 'Cancer', 'Lion', 'Vierge',
                              'Balance', 'Scorpion', 'Sagittaire', 'Capricorne', 'Verseau', 'Poissons']
            for s in signes_str.split(','):
                s = s.strip().replace('&', '').replace('*', '').replace(' ', '')
                for signe_valide in tous_les_signes:
                    if s.startswith(signe_valide):
                        signes.append(signe_valide)
                        break
            break
    
    if len(signes) < 2:
        return None
    
    # Sélectionner 2 signes aléatoires
    signe1, signe2 = random.sample(signes, 2)
    
    # Extraire le texte pour chaque signe
    signes_data = {s: [] for s in signes}
    current_sign = None
    
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('==='):
            m = re.match(r'=== ([A-Za-zÉéèê]+) ===', line)
            if m:
                signe_name = m.group(1).strip()
                name_mapping = {'Taurus': 'Taureau', 'Virgo': 'Vierge'}
                signe_name = name_mapping.get(signe_name, signe_name)
                if signe_name in signes_data:
                    current_sign = signe_name
                else:
                    current_sign = None
            continue
        
        if current_sign and line and not line.startswith('==='):
            skip_lines = ['Nous sommes le', 'Que la', 'Que les', 'Allez', 'respirez',
                         'Que les ancêtres', 'Allez, respirez', 'Signes', 'HOROSCOPE']
            if not any(line.startswith(s) for s in skip_lines) and len(line) > 20:
                signes_data[current_sign].append(line)
    
    # Extraire les thèmes
    texte1 = ' '.join(signes_data.get(signe1, []))
    texte2 = ' '.join(signes_data.get(signe2, []))
    
    themes1 = extract_keywords(texte1)
    themes2 = extract_keywords(texte2)
    
    if themes1 and themes2:
        theme1 = random.choice(themes1)
        theme2 = random.choice(themes2)
        
        if theme1 == theme2 and len(themes2) > 1:
            theme2 = random.choice([t for t in themes2 if t != theme1])
        elif theme1 == theme2 and len(themes1) > 1:
            theme1 = random.choice([t for t in themes1 if t != theme2])
        
        theme1_cap = theme1.capitalize()
        theme2_cap = theme2.capitalize()
        correlation = random.choice(CORRELATION_TEMPLATES).format(theme1_cap, theme2_cap)
    else:
        # Fallback aux noms des signes
        correlation = random.choice(CORRELATION_TEMPLATES).format(signe1, signe2)
    
    emoji1 = SIGNE_EMOJIS.get(signe1, "✨")
    emoji2 = SIGNE_EMOJIS.get(signe2, "✨")
    
    day = date_str[6:8]
    month = date_str[4:6]
    month_name = get_month_name(month)
    
    return f"{signe1} {emoji1} et {signe2} {emoji2} : {correlation}, dans votre horoscope de ce {edition} du {day} {month_name}"


def update_horoscope_titles():
    """Met à jour les titres d'horoscope dans podcast.xml."""
    podcast_path = Path('docs/podcast.xml')
    archives_dir = Path('archives/horoscope')
    
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
        if not guid_text or 'horoscope-' not in guid_text:
            continue
        
        # Extraire date et édition
        m = re.search(r'horoscope-(\d{8})-(\w+)', guid_text)
        if not m:
            continue
        
        date_str = m.group(1)
        edition = m.group(2)
        
        # Trouver le fichier source
        archive_file = archives_dir / f'horoscope-{date_str}-{edition}.txt'
        
        if not archive_file.exists():
            print(f"⚠️ Fichier introuvable: {archive_file.name}")
            continue
        
        # Générer un titre unique
        max_attempts = 50
        titre = None
        for _ in range(max_attempts):
            titre = generate_horoscope_title(archive_file, edition, date_str)
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
        print(f"\n💾 {updated} titres d'horoscope mis à jour dans podcast.xml")
    else:
        print("\n⚠️ Aucun titre d'horoscope mis à jour")


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--update':
        update_horoscope_titles()
    else:
        print("Utilisation: python3 update_horoscope_titles.py --update")
        print("\nMet à jour automatiquement les titres d'horoscope à partir des fichiers archives/horoscope/*.txt")
