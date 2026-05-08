#!/usr/bin/env python3
"""Met à jour AUTOMATIQUEMENT tous les titres du podcast (horoscope, flash-info, emission).

Pour chaque type de contenu :
- HOROSCOPE : Extrait les signes et leurs thèmes astro, crée des corrélations entre 2 signes
- FLASH-INFO : Extrait les mots-clés de l'actualité, crée un titre accrocheur
- EMISSION : Extrait les thèmes culturels du texte, crée un titre poétique

Usage: python3 update_all_podcast_titles.py --update
"""

import re
import json
from pathlib import Path
import random
import xml.etree.ElementTree as ET

# ============================================================
# CONFIGURATION
# ============================================================

SIGNE_EMOJIS = {
    "Bélier": "♈", "Taureau": "♉", "Gémeaux": "♊", "Cancer": "♋",
    "Lion": "♌", "Vierge": "♍", "Balance": "♎", "Scorpion": "♏",
    "Sagittaire": "♐", "Capricorne": "♑", "Verseau": "♒", "Poissons": "♓"
}

# Mots-clés pour chaque type de contenu
HOROSCOPE_KEYWORDS = {
    'avocatier', 'vanille', 'vaniy', 'awokasié', 'manyòk', 'colibri',
    'gommier', 'palétuvier', 'balisier', 'malomé', 'corossol', 'manguier',
    'piment', 'roucou', 'woucou', 'cacao', 'pain', 'cassave', 'banane', 'goyave',
    'bœuf', 'crabbe', 'zandoli', 'fwou-fwou', 'foufou', 'igwann', 'karet',
    'kabrit', 'ouassou', 'wasou', 'gwo', 'tortue', 'touloulou',
    'Soufrière', 'mangrove', 'marée', 'océan', 'morne', 'plage',
    'rivière', 'montagne', 'cascade', 'source', 'rocher',
    'arc-en-ciel', 'éclair', 'tonnerre', 'rosée', 'brume', 'nuage',
    'saveur', 'bouillon', 'tambour', 'gwoka', 'ancêtres', 'sage',
    'germe', 'dachine', 'alpinia', 'sucrier', 'marakoudja',
    'pirogue', 'kalbasi', 'malakié', 'mangouste', 'scarabée', 'Hercule', 'crabier',
    'savane', 'forêt', 'chute', 'Carbet', 'conque', 'kokoye',
    'chadon', 'beni', 'koko', 'matoutou', 'ongée',
    'ti flambeau', 'kokotié', 'sève', 'foumi manyok', 'sitwèl', 'papillon',
    'Manman dlo', 'Touloulou', 'Bèf a Bos', 'Hèrkil'
}

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

# Correlations templates
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

FLASH_INFO_TEMPLATES = [
    "🌴 {} : l’actualité du {}, dans votre Flash Info de ce {}",
    "🌴 {} : ce qu’il faut retenir, dans votre Flash Info de ce {} du {}",
    "🌴 {} : le point sur la situation, dans votre Flash Info de ce {} du {}",
    "🌴 {} : ce qui change en Guadeloupe, dans votre Flash Info de ce {} du {}",
    "🌴 {} : tension et actualités, dans votre Flash Info de ce {} du {}",
    "🌴 {} : l’info qui compte, dans votre Flash Info de ce {} du {}",
    "🌊 {} : l’actualité chaude, dans votre Flash Info de ce {} du {}",
    "🌴 Guadeloupe : {}, dans votre Flash Info de ce {} du {}"
]

EMISSION_TEMPLATES = [
    "{} : {}, trésors de la Guadeloupe",
    "{} — {}, racines et rêves",
    "{} : voyage au cœur de {}",
    "{} : l’histoire de {} en Guadeloupe",
    "{} et {} : découverte de la Guadeloupe",
    "{} : la culture guadeloupéenne en lumière",
    "{} — {}, mémoire et identité",
    "{} : exploration des richesses de {}"
]

# ============================================================
# FONCTIONS COMMUNES
# ============================================================

def get_month_name(month: str) -> str:
    months = {
        '01': 'janvier', '02': 'février', '03': 'mars', '04': 'avril',
        '05': 'mai', '06': 'juin', '07': 'juillet', '08': 'août',
        '09': 'septembre', '10': 'octobre', '11': 'novembre', '12': 'décembre'
    }
    return months.get(month, month)


def extract_keywords(text: str, keywords_set: set, max_keywords: int = 8) -> list:
    """Extraire les mots-clés d'un texte."""
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
        'où', 'si', 'quelle', 'quel', 'quels', 'quelles', 'me', 'moi', 'toi',
        'nous', 'ils', 'elles', 'mon', 'ton', 'notre', 'votre', 'leur'
    }
    
    words = re.findall(r'\b[a-zA-ZàâäéèêëïîôùûüÿæœçÀÂÄÉÈÊËÏÎÔÙÛÜŸÆŒÇ-]{3,}\b', text.lower())
    keywords = []
    seen = set()
    
    for word in words:
        if (word not in STOP_WORDS and 
            word in keywords_set and 
            word not in seen and 
            len(word) >= 3):
            keywords.append(word)
            seen.add(word)
            if len(keywords) >= max_keywords:
                break
    
    return keywords


def get_edition_date_from_guid(guid: str) -> tuple:
    """Extraire date et édition d'un guid."""
    # Horoscope: horoscope-20260508-matin
    m = re.search(r'horoscope-(\d{8})-(\w+)', guid)
    if m:
        return m.group(1), m.group(2), 'horoscope'
    
    # Flash-info: flash-info-20260508-matin
    m = re.search(r'flash-info-(\d{8})-(\w+)', guid)
    if m:
        return m.group(1), m.group(2), 'flash-info'
    
    # Emission: emission-2026-05-08
    m = re.search(r'emission-(\d{4})-(\d{2})-(\d{2})', guid)
    if m:
        return f"{m.group(1)}{m.group(2)}{m.group(3)}", "", 'emission'
    
    # Emission: emission-20260508
    m = re.search(r'emission-(\d{8})', guid)
    if m:
        return m.group(1), "", 'emission'
    
    return "", "", "unknown"


# ============================================================
# GÉNÉRATEURS SPÉCIFIQUES PAR TYPE
# ============================================================

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
    texte1 = signes_data.get(signe1, [])
    texte2 = signes_data.get(signe2, [])
    
    text1_str = ' '.join(texte1)
    text2_str = ' '.join(texte2)
    
    themes1 = extract_keywords(text1_str, HOROSCOPE_KEYWORDS)
    themes2 = extract_keywords(text2_str, HOROSCOPE_KEYWORDS)
    
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
        # Fallback
        correlation = random.choice(CORRELATION_TEMPLATES).format(signe1, signe2)
    
    emoji1 = SIGNE_EMOJIS.get(signe1, "✨")
    emoji2 = SIGNE_EMOJIS.get(signe2, "✨")
    
    day = date_str[6:8]
    month = date_str[4:6]
    month_name = get_month_name(month)
    
    return f"{signe1} {emoji1} et {signe2} {emoji2} : {correlation}, dans votre horoscope de ce {edition} du {day} {month_name}"


def generate_flash_info_title(filepath: Path, edition: str, date_str: str) -> str:
    """Génère un titre de flash-info basé sur le contenu du fichier."""
    content = filepath.read_text(encoding='utf-8')
    
    # Extraire les mots-clés
    keywords = extract_keywords(content, FLASH_INFO_KEYWORDS, max_keywords=10)
    
    # Extraire date
    day = date_str[6:8]
    month = date_str[4:6]
    month_name = get_month_name(month)
    date_str_formatted = f"{day} {month_name}"
    
    # Déterminer le moment (matin, midi, soir)
    moment = edition
    
    if not keywords:
        # Fallback
        return f"🌴 Flash Guadeloupe : l’actualité du {date_str_formatted}"
    
    # Trouver le thème principal (le plus long)
    main_keyword = max(keywords, key=len) if keywords else "Actualité"
    main_keyword_cap = main_keyword.capitalize()
    
    # Choix du template
    template = random.choice(FLASH_INFO_TEMPLATES)
    
    # Tous les templates ont 3 placeholders : {thème}, {moment}, {date}
    titre = template.format(main_keyword_cap, moment, date_str_formatted)
    
    return titre


def generate_emission_title(filepath: Path, edition: str, date_str: str) -> str:
    """Génère un titre d'émission basé sur le contenu du fichier JSON."""
    try:
        data = json.loads(filepath.read_text(encoding='utf-8'))
        text = data.get('text', '')
        existing_title = data.get('title', '')
    except:
        return None
    
    # Extraire les mots-clés du texte
    keywords = extract_keywords(text, EMISSION_KEYWORDS, max_keywords=10)
    
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
    suffixes = [
        "trésors de la Guadeloupe",
        "racines et rêves",
        "mémoire et identité",
        "voyage au cœur de la culture guadeloupéenne",
        "l’histoire de la Guadeloupe",
        "découverte de la Guadeloupe",
        "la culture guadeloupéenne en lumière",
        "exploration des richesses de la Guadeloupe"
    ]
    suffixe = random.choice(suffixes)
    
    # Choisir un séparateur approprié
    # Si title_part contient déjà "et", éviter " et " comme séparateur
    if " et " in title_part:
        separators = [" : ", " — ", ", "]
    else:
        separators = [" : ", " — ", " et ", ", "]
    separator = random.choice(separators)
    
    return f"{title_part}{separator}{suffixe}"


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def find_source_file(content_type: str, date_str: str, edition: str) -> Path:
    """Trouver le fichier source correspondant à un item."""
    base = Path('archives')
    
    if content_type == 'horoscope':
        filename = f'horoscope-{date_str}-{edition}.txt'
        return base / 'horoscope' / filename
    
    elif content_type == 'flash-info':
        filename = f'flash-info-{date_str}-{edition}.txt'
        return base / 'flash-info' / filename
    
    elif content_type == 'emission':
        # Essayer différents formats
        filenames = [
            f'emission-{date_str}.json',
            f'emission-{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}.json'
        ]
        for filename in filenames:
            candidate = Path('docs/audio/Emissions') / filename
            if candidate.exists():
                return candidate
        return None
    
    return None


def update_podcast_titles():
    """Met à jour tous les titres du podcast."""
    podcast_path = Path('docs/podcast.xml')
    
    if not podcast_path.exists():
        print(f"❌ Fichier introuvable: {podcast_path}")
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
        if not guid_text:
            continue
        
        date_str, edition, content_type = get_edition_date_from_guid(guid_text)
        
        if not date_str or content_type == 'unknown':
            continue
        
        # Trouver le fichier source
        source_file = find_source_file(content_type, date_str, edition)
        
        if not source_file or not source_file.exists():
            print(f"⚠️ Fichier source introuvable pour {guid_text}")
            continue
        
        # Générer le titre
        max_attempts = 50
        titre = None
        
        for _ in range(max_attempts):
            if content_type == 'horoscope':
                titre = generate_horoscope_title(source_file, edition, date_str)
            elif content_type == 'flash-info':
                titre = generate_flash_info_title(source_file, edition, date_str)
            elif content_type == 'emission':
                titre = generate_emission_title(source_file, edition, date_str)
            
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
        print(f"\n💾 {updated} titres mis à jour dans podcast.xml")
    else:
        print("\n⚠️ Aucun titre mis à jour")


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--update':
        update_podcast_titles()
    else:
        print("Utilisation: python3 update_all_podcast_titles.py --update")
        print("\nCe script met à jour automatiquement:")
        print("  - Les titres d'HOROSCOPE (à partir des fichiers archives/horoscope/*.txt)")
        print("  - Les titres de FLASH-INFO (à partir des fichiers archives/flash-info/*.txt)")
        print("  - Les titres d'ÉMISSION (à partir des fichiers docs/audio/Emissions/*.json)")
