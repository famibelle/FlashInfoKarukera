#!/usr/bin/env python3
"""Met à jour AUTOMATIQUEMENT les titres de FLASH-INFO dans podcast.xml.

Lit les fichiers archives/flash-info/*.txt, extrait les mots-clés de l'actualité,
puis génère des titres uniques et accrocheurs.

Usage: python3 update_flash_info_titles.py --update
"""

import re
from pathlib import Path
import random
import xml.etree.ElementTree as ET

# Mots-clés pour flash-info
FLASH_INFO_KEYWORDS = {
    # Météo
    'pluie', 'soleil', 'nuage', 'alizé', 'vent', 'température', 'ondée', 'canicule',
    'cyclone', 'ouragan', 'tempête', 'brume', 'brouillard',
    # Politique/Société
    'manifestation', 'grève', 'préfet', 'mairie', 'école', 'éducation', 'santé',
    'eau', 'assainissement', 'sécurité', 'police', 'justice', 'tribunal',
    'économie', 'vie chère', 'prix', 'inflation', 'commerce', 'marché',
    # Sport
    'course', 'grand prix', 'victoire', 'compétition', 'athlète', 'stade', 'match',
    'football', 'basket', 'tennis', 'natation', 'cyclisme',
    # Culture
    'théâtre', 'concert', 'spectacle', 'exposition', 'musée', 'festival', 'artiste',
    'musique', 'danse', 'chant', 'gwoka', 'tambour', 'carnaval',
    # International
    'Gaza', 'Israël', 'guerre', 'paix', 'négociation', 'ONU', 'UE', 'France',
    'États-Unis', 'Chine', 'Russie', 'Afrique', 'Amérique',
    # Local Guadeloupe
    'Pointe-à-Pitre', 'Basse-Terre', 'Sainte-Anne', 'Petit-Canal', 'Le Moule',
    'Les Abymes', 'Baie-Mahault', 'Capesterre', 'Port-Louis', 'Saint-François',
    'Lamentin', 'Gourbeyre', 'Petit-Bourg', 'Deshaies', 'Grand Cul-de-Sac',
    # Divers
    'accident', 'incendie', 'vol', 'arrestation', 'enquête', 'procès',
    'santé', 'hôpital', 'médecin', 'vacation', 'tourisme', 'plage'
}

# Templates de titres
FLASH_INFO_TEMPLATES = [
    "🌴 {} : l’actualité du {}, dans votre Flash Info de ce {}",
    "🌴 {} en Guadeloupe : ce qu’il faut retenir, dans votre Flash Info de ce {}",
    "🌴 {} : le point sur la situation, dans votre Flash Info de ce {}",
    "🌴 {} : ce qui change en Guadeloupe, dans votre Flash Info de ce {}",
    "🌴 {} : tension et actualités, dans votre Flash Info de ce {}",
    "🌴 {} : l’info qui compte, dans votre Flash Info de ce {}",
    "🌊 {} : l’actualité chaude, dans votre Flash Info de ce {}",
    "🌴 Guadeloupe : {}, dans votre Flash Info de ce {}"
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
            word in FLASH_INFO_KEYWORDS and 
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


def generate_flash_info_title(filepath: Path, edition: str, date_str: str) -> str:
    """Génère un titre de flash-info basé sur le contenu du fichier."""
    content = filepath.read_text(encoding='utf-8')
    
    # Extraire les mots-clés
    keywords = extract_keywords(content, max_keywords=10)
    
    # Extraire date
    day = date_str[6:8]
    month = date_str[4:6]
    month_name = get_month_name(month)
    date_str_formatted = f"{day} {month_name}"
    
    if not keywords:
        # Fallback
        return f"🌴 Flash Guadeloupe : l’actualité du {date_str_formatted}"
    
    # Trouver le thème principal (le plus long)
    main_keyword = max(keywords, key=len) if keywords else "Actualité"
    main_keyword_cap = main_keyword.capitalize()
    
    # Choix du template
    template = random.choice(FLASH_INFO_TEMPLATES)
    
    # Générer le titre
    titre = template.format(main_keyword_cap, date_str_formatted, edition)
    
    return titre


def update_flash_info_titles():
    """Met à jour les titres de flash-info dans podcast.xml."""
    podcast_path = Path('docs/podcast.xml')
    archives_dir = Path('archives/flash-info')
    
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
        if not guid_text or 'flash-info-' not in guid_text:
            continue
        
        # Extraire date et édition
        m = re.search(r'flash-info-(\d{8})-(\w+)', guid_text)
        if not m:
            continue
        
        date_str = m.group(1)
        edition = m.group(2)
        
        # Trouver le fichier source
        archive_file = archives_dir / f'flash-info-{date_str}-{edition}.txt'
        
        if not archive_file.exists():
            print(f"⚠️ Fichier introuvable: {archive_file.name}")
            continue
        
        # Générer un titre unique
        max_attempts = 50
        titre = None
        for _ in range(max_attempts):
            titre = generate_flash_info_title(archive_file, edition, date_str)
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
        print(f"\n💾 {updated} titres de flash-info mis à jour dans podcast.xml")
    else:
        print("\n⚠️ Aucun titre de flash-info mis à jour")


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--update':
        update_flash_info_titles()
    else:
        print("Utilisation: python3 update_flash_info_titles.py --update")
        print("\nMet à jour automatiquement les titres de flash-info à partir des fichiers archives/flash-info/*.txt")
