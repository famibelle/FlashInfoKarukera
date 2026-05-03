#!/usr/bin/env python3
"""
Génère docs/radio_sequence.json.

Structure 24h :
  [Flash Info matin] [Horoscope matin]
  [Liner] [×15 pistes] [Liner] [×12 pistes]
  [Flash Info midi]
  [Liner] [×15 pistes] [Liner] [×12 pistes]
  [Flash Info soir] [Horoscope soir]
  [Liner] [×15 pistes] [Liner] [×11 pistes]

Les liners annoncent les artistes du bloc suivant.
Ils sont des vidéos YouTube (cache youtube_cache.json) ou générés à la volée.
"""

import json
import os
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

POOL_CACHE  = Path("playlists/music_pool_cache.json")
PODCAST_XML = Path("docs/podcast.xml")
OUTPUT      = Path("docs/radio_sequence.json")

TRACKS_PER_LINER = 15   # pistes entre deux liners

# Répartition des blocs (doit correspondre à playlist_24h.py)
BLOCK_SIZES = {
    "matin": 27,
    "midi":  27,
    "soir":  26,
}

BLOCK_LABELS = {
    "matin": "ce matin",
    "midi":  "cet après-midi",
    "soir":  "ce soir",
}


# ── Pool musical ──────────────────────────────────────────────────────────────

def load_pool() -> list[dict]:
    if not POOL_CACHE.exists():
        return []
    data = json.loads(POOL_CACHE.read_text())
    tracks = data.get("tracks", [])
    random.shuffle(tracks)
    return tracks


# ── Transitions depuis le podcast RSS ────────────────────────────────────────

def load_transitions() -> dict[str, list[dict]]:
    """
    Retourne { "flash_matin": {...}, "horoscope_matin": {...},
               "flash_midi": {...},
               "flash_soir": {...}, "horoscope_soir": {...} }
    En cas d'épisodes multiples pour un slot, garde le plus récent.
    """
    if not PODCAST_XML.exists():
        return {}

    xml   = PODCAST_XML.read_text(encoding="utf-8")
    items = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)
    slots: dict[str, dict] = {}

    for item in items:
        guid  = re.search(r"<guid[^>]*>(.*?)</guid>", item)
        guid  = guid.group(1).strip() if guid else ""
        title = re.search(r"<title>(.*?)</title>", item)
        title = title.group(1).strip() if title else ""
        url   = re.search(r'<enclosure url="([^"]+\.mp3)"', item)
        url   = url.group(1).strip() if url else ""
        if not url or not guid:
            continue

        title = re.sub(r"[🌅🌙✨]", "", title).strip()

        if "flash-info" in guid:
            subtype, icon = "flash_info", "📰"
            if "matin"  in guid: slot = "flash_matin"
            elif "midi" in guid: slot = "flash_midi"
            elif "soir" in guid: slot = "flash_soir"
            else: continue
        elif "horoscope" in guid:
            subtype, icon = "horoscope", "✨"
            if "matin" in guid: slot = "horoscope_matin"
            elif "soir" in guid: slot = "horoscope_soir"
            else: continue
        else:
            continue

        if slot not in slots:  # premier = plus récent (ordre RSS)
            slots[slot] = {"type": "transition", "subtype": subtype,
                           "url": url, "label": title, "icon": icon}

    return slots


# ── Liners ────────────────────────────────────────────────────────────────────


def get_liner(artists: list[str], bloc: str) -> dict | None:
    """
    Génère ou récupère le liner MP3 pour ce groupe d'artistes.
    Retourne { type:"liner", url, label } ou None si non disponible.
    """
    if not artists:
        return None
    try:
        from youtube_uploader import get_announcement_mp3_url
        url = get_announcement_mp3_url(bloc, artists[:5])
        if url:
            label = f"Dans un moment : {', '.join(artists[:3])}"
            return {"type": "liner", "url": url, "label": label, "icon": "🎙️"}
    except Exception as e:
        print(f"   ⚠️  Liner {bloc} ignoré : {e}", file=sys.stderr)
    return None


# ── Construction de la séquence ───────────────────────────────────────────────

def _music_with_liners(tracks: list[dict], bloc: str) -> list[dict]:
    """Intercale un liner toutes les TRACKS_PER_LINER pistes."""
    result = []
    for i in range(0, len(tracks), TRACKS_PER_LINER):
        group   = tracks[i : i + TRACKS_PER_LINER]
        artists = list(dict.fromkeys(t.get("artist", "") for t in group if t.get("artist")))
        liner   = get_liner(artists[:5], bloc)
        if liner:
            result.append(liner)
        for t in group:
            result.append({
                "type":    "music",
                "videoId": t["videoId"],
                "title":   t.get("name",   ""),
                "artist":  t.get("artist", ""),
                "genre":   t.get("genre",  ""),
            })
    return result


def build_sequence(pool: list[dict], slots: dict[str, dict]) -> list[dict]:
    seq = []
    pos = 0

    for bloc, size in BLOCK_SIZES.items():
        # Transitions éditoriales du bloc
        if bloc == "matin":
            for key in ("flash_matin", "horoscope_matin"):
                if key in slots:
                    seq.append(slots[key])
        elif bloc == "midi":
            if "flash_midi" in slots:
                seq.append(slots["flash_midi"])
        elif bloc == "soir":
            for key in ("flash_soir", "horoscope_soir"):
                if key in slots:
                    seq.append(slots[key])

        # Bloc musical avec liners intégrés
        block_tracks = pool[pos : pos + size]
        seq += _music_with_liners(block_tracks, bloc)
        pos += size

    return seq


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    pool  = load_pool()
    slots = load_transitions()

    if not pool:
        print("⚠️  Pool musical vide — radio_sequence.json non mis à jour.", file=sys.stderr)
        sys.exit(1)

    if not slots:
        print("⚠️  Aucune transition trouvée dans podcast.xml", file=sys.stderr)

    seq = build_sequence(pool, slots)

    n_music   = sum(1 for s in seq if s["type"] == "music")
    n_liners  = sum(1 for s in seq if s["type"] == "liner")
    n_transit = sum(1 for s in seq if s["type"] == "transition")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps({
            "generated":   datetime.now(timezone.utc).isoformat(),
            "music":       n_music,
            "liners":      n_liners,
            "transitions": n_transit,
            "sequence":    seq,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"✅ radio_sequence.json — {len(seq)} éléments "
          f"({n_music} pistes · {n_liners} liners · {n_transit} transitions)")


if __name__ == "__main__":
    main()
