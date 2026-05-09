#!/usr/bin/env python3
"""
Génère des titres accrocheurs pour podcast.xml via Mistral LLM.

Sources :
  - Horoscope  : archives/horoscope/horoscope-YYYYMMDD-{matin|soir}.txt
  - Flash info : archives/flash-info/flash-info-YYYYMMDD-{matin|midi|soir}.txt
  - Émission   : docs/audio/Emissions/emission-YYYY-MM-DD.json

Usage :
    python update_podcast_titles.py           # dry-run (aperçu sans sauvegarder)
    python update_podcast_titles.py --update  # applique les changements
    python update_podcast_titles.py --type horoscope   # un seul type
    python update_podcast_titles.py --type flash-info
    python update_podcast_titles.py --type emission
"""

import json
import os
import random
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Config ───────────────────────────────────────────────────────────────────

API_KEY  = os.getenv("MISTRAL_API_KEY_BOTIRAN")
MODEL    = "mistral-small-latest"
CHAT_URL = "https://api.mistral.ai/v1/chat/completions"

PODCAST_PATH  = Path("docs/podcast.xml")
HOROSCOPE_DIR = Path("archives/horoscope")
FLASH_DIR     = Path("archives/flash-info")
EMISSION_DIR  = Path("docs/audio/Emissions")

MONTH_NAMES = {
    "01": "janvier", "02": "février", "03": "mars",    "04": "avril",
    "05": "mai",     "06": "juin",    "07": "juillet",  "08": "août",
    "09": "septembre", "10": "octobre", "11": "novembre", "12": "décembre",
}

SIGN_EMOJIS = {
    "Bélier": "♈", "Taureau": "♉", "Gémeaux": "♊", "Cancer": "♋",
    "Lion": "♌",   "Vierge": "♍",  "Balance": "♎", "Scorpion": "♏",
    "Sagittaire": "♐", "Capricorne": "♑", "Verseau": "♒", "Poissons": "♓",
}

# ── Mistral ──────────────────────────────────────────────────────────────────

def call_mistral(system: str, user: str, *, temperature: float = 0.85, max_tokens: int = 120) -> str:
    if not API_KEY:
        raise RuntimeError("MISTRAL_API_KEY_BOTIRAN manquant dans .env")

    payload = {
        "model": MODEL,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    }
    req = urllib.request.Request(
        CHAT_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                wait = 15 * 2 ** attempt
                print(f"   ⏳ Mistral {e.code} — retry dans {wait}s…", flush=True)
                time.sleep(wait)
            else:
                raise
        except (TimeoutError, OSError):
            if attempt < 3:
                time.sleep(15 * 2 ** attempt)
            else:
                raise


def _clean(raw: str) -> str:
    """Retire guillemets, astérisques, sauts de ligne produits par le LLM."""
    title = re.sub(r'[\[\]\*\`\"\'\n\r]', '', raw)
    title = re.sub(r'\s+', ' ', title).strip().rstrip('.')
    return title


# ── Parseur horoscope ────────────────────────────────────────────────────────

def _normalize_sign(raw: str) -> str | None:
    """'TAUREAU' → 'Taureau', vérifie que c'est un signe connu."""
    candidate = raw.strip().title()
    return candidate if candidate in SIGN_EMOJIS else None


def parse_sign_texts(horoscope_text: str) -> dict[str, str]:
    """Retourne {nom_signe: texte_brut} pour chaque signe trouvé."""
    signs: dict[str, list[str]] = {}
    current: str | None = None

    SKIP_PREFIXES = (
        'HOROSCOPE KARUKERA', 'Signes :', 'Nous sommes le', 'Que la ', 'Que les ',
        'Allez,', '====', 'Bèl bonjou',
    )

    for line in horoscope_text.splitlines():
        stripped = line.strip()

        m = re.match(r'=== ([A-ZÀÂÄÉÈÊËÏÎÔÙÛÜŸ]+) ===', stripped)
        if m:
            current = _normalize_sign(m.group(1))
            if current and current not in signs:
                signs[current] = []
            continue

        if current and stripped and len(stripped) > 20:
            if not any(stripped.startswith(p) for p in SKIP_PREFIXES):
                signs[current].append(stripped)

    return {k: ' '.join(v) for k, v in signs.items() if v}


def parse_sign_list(horoscope_text: str) -> list[str]:
    """Extrait la liste ordonnée depuis la ligne 'Signes : ...'"""
    for line in horoscope_text.splitlines():
        if line.startswith('Signes :'):
            found = []
            for part in line.split(':', 1)[1].split(','):
                name = part.strip().replace('&', '').replace('*', '').strip()
                if name in SIGN_EMOJIS:
                    found.append(name)
            return found
    return []


# ── Générateurs de titres ────────────────────────────────────────────────────

def _date_fr(date_compact: str) -> tuple[str, str]:
    """'20260509' → ('9', 'mai')"""
    return str(int(date_compact[6:8])), MONTH_NAMES.get(date_compact[4:6], '?')


def generate_horoscope_title(filepath: Path, edition: str, date_compact: str) -> str | None:
    text = filepath.read_text(encoding='utf-8')

    sign_texts = parse_sign_texts(text)
    sign_list  = parse_sign_list(text)

    # Sélectionner parmi les signes qui ont du texte, dans l'ordre du fichier
    available = [s for s in sign_list if s in sign_texts and len(sign_texts[s]) > 80]
    if len(available) < 2:
        available = [s for s in sign_texts if len(sign_texts[s]) > 80]
    if len(available) < 2:
        return None

    signe1, signe2 = random.sample(available, 2)
    excerpt1 = sign_texts[signe1][:700]
    excerpt2 = sign_texts[signe2][:700]

    system = (
        "Tu es un rédacteur créatif pour Radio Karukera, une radio de la diaspora guadeloupéenne au Luxembourg. "
        "Tu génères des titres d'horoscopes courts, poétiques, percutants, avec une touche créole et caraïbéenne."
    )
    user = (
        f"Voici des extraits de l'horoscope pour deux signes :\n\n"
        f"{signe1.upper()} :\n{excerpt1}\n\n"
        f"{signe2.upper()} :\n{excerpt2}\n\n"
        "Identifie les images, symboles ou sensations dominants dans chaque texte "
        "(plantes, animaux, éléments, tensions…). "
        "Crée une corrélation inattendue et poétique entre ces deux univers — "
        "quelque chose de surprenant qui donne envie d'écouter.\n"
        "Retourne UNIQUEMENT une phrase courte (max 55 caractères).\n"
        "Pas de guillemets, pas de ponctuation finale."
    )

    raw = call_mistral(system, user, temperature=0.88, max_tokens=80)
    correlation = _clean(raw)
    if not correlation:
        return None

    e1 = SIGN_EMOJIS.get(signe1, '✨')
    e2 = SIGN_EMOJIS.get(signe2, '✨')
    day, month = _date_fr(date_compact)

    return f"{signe1} {e1} & {signe2} {e2} : {correlation}, dans votre horoscope de ce {edition} du {day} {month}"


def generate_flash_title(filepath: Path, edition: str, date_compact: str) -> str | None:
    text = filepath.read_text(encoding='utf-8')[:2000]

    day, month = _date_fr(date_compact)

    system = (
        "Tu es un rédacteur accrocheur pour Radio Karukera, une radio de la diaspora guadeloupéenne. "
        "Tu écris des titres de flash info courts qui donnent envie d'écouter sans tout révéler — "
        "comme un teaser."
    )
    user = (
        f"Voici le texte d'un flash info guadeloupéen — édition du {edition} du {day} {month} :\n\n"
        f"{text}\n\n"
        "Choisis l'info la plus marquante et génère UN SEUL titre accrocheur (max 70 caractères) "
        "qui donne envie d'écouter sans tout révéler, comme un teaser radio. "
        "Une seule phrase, pas de liste, pas de numérotation, pas de guillemets, pas de ponctuation finale."
    )

    raw = call_mistral(system, user, temperature=0.80, max_tokens=100)
    return _clean(raw) or None


def generate_emission_title(filepath: Path) -> str | None:
    try:
        data  = json.loads(filepath.read_text(encoding='utf-8'))
        text  = data.get('text', '')[:2000]
    except Exception:
        return None

    if not text:
        return None

    system = (
        "Tu es un rédacteur poétique pour Radio Karukera, une radio de la diaspora guadeloupéenne. "
        "Tu crées des titres d'émissions culturelles évocateurs, qui inspirent et donnent envie d'écouter."
    )
    user = (
        f"Voici le texte d'une émission culturelle sur la Guadeloupe :\n\n"
        f"{text}\n\n"
        "Génère un titre poétique et évocateur (max 60 caractères) qui capture l'essence de cette émission. "
        "Pas de guillemets, pas de ponctuation finale."
    )

    raw = call_mistral(system, user, temperature=0.85, max_tokens=80)
    return _clean(raw) or None


# ── Résolution guid / fichier source ─────────────────────────────────────────

def parse_guid(guid: str) -> tuple[str, str, str]:
    """Retourne (date_compact, edition, content_type) depuis un guid RSS."""
    m = re.search(r'horoscope-(\d{8})-(\w+)', guid)
    if m:
        return m.group(1), m.group(2), 'horoscope'

    m = re.search(r'flash-info-(\d{8})-(\w+)', guid)
    if m:
        return m.group(1), m.group(2), 'flash-info'

    m = re.search(r'emission-(\d{4})-(\d{2})-(\d{2})', guid)
    if m:
        return f"{m.group(1)}{m.group(2)}{m.group(3)}", '', 'emission'

    m = re.search(r'emission-(\d{8})', guid)
    if m:
        return m.group(1), '', 'emission'

    return '', '', ''


def resolve_source(content_type: str, date_compact: str, edition: str) -> Path | None:
    if content_type == 'horoscope':
        p = HOROSCOPE_DIR / f"horoscope-{date_compact}-{edition}.txt"
        return p if p.exists() else None

    if content_type == 'flash-info':
        p = FLASH_DIR / f"flash-info-{date_compact}-{edition}.txt"
        return p if p.exists() else None

    if content_type == 'emission':
        date_iso = f"{date_compact[:4]}-{date_compact[4:6]}-{date_compact[6:8]}"
        for stem in (f"emission-{date_iso}", f"emission-{date_compact}"):
            p = EMISSION_DIR / f"{stem}.json"
            if p.exists():
                return p

    return None


# ── Main ──────────────────────────────────────────────────────────────────────

def update_titles(*, apply: bool = False, only_type: str | None = None) -> None:
    if not PODCAST_PATH.exists():
        print(f"❌ {PODCAST_PATH} introuvable")
        return
    if not API_KEY:
        print("❌ MISTRAL_API_KEY_BOTIRAN manquant dans .env")
        return

    tree  = ET.parse(PODCAST_PATH)
    root  = tree.getroot()
    items = root.findall('.//item')

    changed = 0
    skipped = 0
    errors  = 0

    for item in items:
        guid_el  = item.find('guid')
        title_el = item.find('title')
        if guid_el is None or title_el is None:
            continue

        guid = guid_el.text or ''
        date_compact, edition, content_type = parse_guid(guid)

        if not date_compact or not content_type:
            continue
        if only_type and content_type != only_type:
            continue

        source = resolve_source(content_type, date_compact, edition)
        if source is None:
            print(f"  ⚠️  source introuvable — {guid}")
            skipped += 1
            continue

        print(f"  🔄 {guid}…", flush=True)
        try:
            if content_type == 'horoscope':
                title = generate_horoscope_title(source, edition, date_compact)
            elif content_type == 'flash-info':
                title = generate_flash_title(source, edition, date_compact)
            elif content_type == 'emission':
                title = generate_emission_title(source)
            else:
                continue
        except Exception as e:
            print(f"  ❌ erreur — {guid}: {e}")
            errors += 1
            continue

        if not title:
            print(f"  ⚠️  titre vide — {guid}")
            skipped += 1
            continue

        old = title_el.text or ''
        print(f"     ancien : {old}")
        print(f"     nouveau: {title}")
        print()

        if apply:
            title_el.text = title
        changed += 1

    print("─" * 60)
    if apply and changed > 0:
        ET.register_namespace('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
        tree.write(PODCAST_PATH, encoding='utf-8', xml_declaration=True)
        import subprocess
        subprocess.run(['sed', '-i', 's/<ns0:/<itunes:/g;s/<\\/ns0:/<\\/itunes:/g;s/ ns0:/ itunes:/g;s/xmlns:ns0=/xmlns:itunes=/g', str(PODCAST_PATH)], check=True)
        print(f"💾 {changed} titres mis à jour dans {PODCAST_PATH}")
    elif not apply:
        print(f"[dry-run] {changed} titre(s) générés. Relancez avec --update pour sauvegarder.")
    else:
        print("Aucun changement.")

    if skipped:
        print(f"⚠️  {skipped} item(s) ignorés (source introuvable ou titre vide).")
    if errors:
        print(f"❌ {errors} erreur(s) lors des appels LLM.")


if __name__ == '__main__':
    args      = sys.argv[1:]
    apply     = '--update' in args
    only_type = None

    if '--type' in args:
        idx = args.index('--type')
        if idx + 1 < len(args):
            only_type = args[idx + 1]

    update_titles(apply=apply, only_type=only_type)
