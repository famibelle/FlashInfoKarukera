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
import re
import subprocess
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

from title_generator import (
    generate_flash_title,
    generate_horoscope_title,
    _load_recent_horoscope_titles,
)

# ── Config ────────────────────────────────────────────────────────────────────

API_KEY      = os.getenv("MISTRAL_API_KEY_BOTIRAN")
PODCAST_PATH = Path("docs/podcast.xml")
HOROSCOPE_DIR = Path("archives/horoscope")
FLASH_DIR     = Path("archives/flash-info")
EMISSION_DIR  = Path("docs/audio/Emissions")

MONTH_NAMES = {
    "01": "janvier", "02": "février", "03": "mars",    "04": "avril",
    "05": "mai",     "06": "juin",    "07": "juillet",  "08": "août",
    "09": "septembre", "10": "octobre", "11": "novembre", "12": "décembre",
}

# ── Mistral (pour les émissions, non couvert par title_generator) ─────────────

MODEL    = "mistral-small-latest"
CHAT_URL = "https://api.mistral.ai/v1/chat/completions"


def _call_mistral_local(system: str, user: str, temperature: float = 0.85, max_tokens: int = 120) -> str:
    if not API_KEY:
        raise RuntimeError("MISTRAL_API_KEY_BOTIRAN manquant dans .env")
    payload = {
        "model": MODEL, "temperature": temperature, "max_tokens": max_tokens,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    req = urllib.request.Request(
        CHAT_URL, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
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
    return ""


def _clean(raw: str) -> str:
    title = re.sub(r'[\[\]\*\`\"\n\r]', "", raw)
    title = title.strip("'")  # guillemets entourants seulement
    title = re.sub(r"\s+", " ", title).strip().rstrip(".")
    return title


# ── Générateur émission ───────────────────────────────────────────────────────

def generate_emission_title(filepath: Path) -> str | None:
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
        text = data.get("text", "")
    except Exception:
        return None
    if not text:
        return None

    inspiration = data.get("inspiration") or {}
    track_title  = inspiration.get("title", "")
    track_artist = inspiration.get("artist", "")
    music_ban = ""
    if track_title or track_artist:
        music_ban = (
            f"\nIMPORTANT : n'utilise PAS le titre de chanson « {track_title} », "
            f"ni le nom de l'artiste « {track_artist} », ni aucune référence musicale dans le titre."
        )

    system = (
        "Tu es un rédacteur poétique pour Radio Karukera, une radio de la diaspora guadeloupéenne. "
        "Tu crées des titres d'émissions culturelles évocateurs, qui inspirent et donnent envie d'écouter."
    )
    user = (
        f"Voici le texte d'une émission culturelle sur la Guadeloupe :\n\n{text}\n\n"
        "Génère un titre poétique et évocateur (max 60 caractères) qui capture l'essence culturelle "
        "de cette émission — faune, flore, histoire ou mémoire guadeloupéenne. "
        f"Pas de guillemets, pas de ponctuation finale.{music_ban}"
    )
    raw = _call_mistral_local(system, user, temperature=0.85, max_tokens=80)
    return _clean(raw) or None


# ── Résolution guid / fichier source ─────────────────────────────────────────

def parse_guid(guid: str) -> tuple[str, str, str]:
    m = re.search(r"horoscope-(\d{8})-(\w+)", guid)
    if m:
        return m.group(1), m.group(2), "horoscope"
    m = re.search(r"flash-info-(\d{8})-(\w+)", guid)
    if m:
        return m.group(1), m.group(2), "flash-info"
    # Émission avec édition : emission-2026-05-09-matin
    m = re.search(r"emission-(\d{4})-(\d{2})-(\d{2})-(matin|soir)", guid)
    if m:
        return f"{m.group(1)}{m.group(2)}{m.group(3)}", m.group(4), "emission"
    # Émission sans édition (ancien format) : emission-2026-05-09
    m = re.search(r"emission-(\d{4})-(\d{2})-(\d{2})", guid)
    if m:
        return f"{m.group(1)}{m.group(2)}{m.group(3)}", "", "emission"
    m = re.search(r"emission-(\d{8})", guid)
    if m:
        return m.group(1), "", "emission"
    return "", "", ""


def resolve_source(content_type: str, date_compact: str, edition: str) -> Path | None:
    if content_type == "horoscope":
        p = HOROSCOPE_DIR / f"horoscope-{date_compact}-{edition}.txt"
        return p if p.exists() else None
    if content_type == "flash-info":
        p = FLASH_DIR / f"flash-info-{date_compact}-{edition}.txt"
        return p if p.exists() else None
    if content_type == "emission":
        date_iso = f"{date_compact[:4]}-{date_compact[4:6]}-{date_compact[6:8]}"
        # Chercher avec édition en priorité, puis sans (rétrocompatibilité)
        candidates = []
        if edition:
            candidates += [
                f"emission-{date_iso}-{edition}",
                f"emission-{date_compact}-{edition}",
            ]
        candidates += [f"emission-{date_iso}", f"emission-{date_compact}"]
        for stem in candidates:
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
    items = root.findall(".//item")

    changed = 0
    skipped = 0
    errors  = 0

    # Pré-alimenter avec les titres horoscope existants pour éviter les répétitions dès le premier appel
    recent_horoscope_titles: list[str] = []
    for item in items:
        guid_el  = item.find("guid")
        title_el = item.find("title")
        if guid_el is None or title_el is None:
            continue
        _, _, ctype = parse_guid(guid_el.text or "")
        if ctype == "horoscope" and title_el.text:
            recent_horoscope_titles.append(title_el.text)

    for item in items:
        guid_el  = item.find("guid")
        title_el = item.find("title")
        if guid_el is None or title_el is None:
            continue

        guid = guid_el.text or ""
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
            if content_type == "horoscope":
                title = generate_horoscope_title(
                    source, edition, date_compact,
                    api_key=API_KEY,
                    recent_titles=recent_horoscope_titles,
                )
                if title:
                    recent_horoscope_titles.append(title)
            elif content_type == "flash-info":
                title = generate_flash_title(source, edition, date_compact, api_key=API_KEY)
            elif content_type == "emission":
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

        old = title_el.text or ""
        print(f"     ancien : {old}")
        print(f"     nouveau: {title}")
        print()

        if apply:
            title_el.text = title
        changed += 1

    print("─" * 60)
    if apply and changed > 0:
        ET.register_namespace("itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
        tree.write(PODCAST_PATH, encoding="utf-8", xml_declaration=True)
        subprocess.run(
            ["sed", "-i",
             "s/<ns0:/<itunes:/g;s/<\\/ns0:/<\\/itunes:/g;s/ ns0:/ itunes:/g;s/xmlns:ns0=/xmlns:itunes=/g",
             str(PODCAST_PATH)],
            check=True,
        )
        print(f"💾 {changed} titres mis à jour dans {PODCAST_PATH}")
    elif not apply:
        print(f"[dry-run] {changed} titre(s) générés. Relancez avec --update pour sauvegarder.")
    else:
        print("Aucun changement.")

    if skipped:
        print(f"⚠️  {skipped} item(s) ignorés (source introuvable ou titre vide).")
    if errors:
        print(f"❌ {errors} erreur(s) lors des appels LLM.")


if __name__ == "__main__":
    args      = sys.argv[1:]
    apply     = "--update" in args
    only_type = None
    if "--type" in args:
        idx = args.index("--type")
        if idx + 1 < len(args):
            only_type = args[idx + 1]
    update_titles(apply=apply, only_type=only_type)
