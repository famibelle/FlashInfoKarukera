#!/usr/bin/env python3
"""
Génère docs/radio_sequence.json à partir du pool musical et du podcast RSS.
Appelé par botiran-radio-daily.yml après la mise à jour de la playlist.
"""

import json
import random
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

POOL_CACHE   = Path("playlists/music_pool_cache.json")
PODCAST_XML  = Path("docs/podcast.xml")
OUTPUT       = Path("docs/radio_sequence.json")

TRACKS_PER_BLOCK = 6   # pistes musicales entre deux transitions


def load_pool() -> list[dict]:
    if not POOL_CACHE.exists():
        return []
    data = json.loads(POOL_CACHE.read_text())
    tracks = data.get("tracks", [])
    random.shuffle(tracks)
    return tracks


def load_transitions() -> list[dict]:
    """Extrait les transitions depuis le podcast RSS (flash info + horoscope)."""
    if not PODCAST_XML.exists():
        return []

    xml = PODCAST_XML.read_text(encoding="utf-8")
    items = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)

    transitions = []
    seen_guids  = set()

    for item in items:
        guid  = (re.search(r"<guid[^>]*>(.*?)</guid>", item) or ["", ""])[0]
        guid  = re.search(r"<guid[^>]*>(.*?)</guid>", item)
        guid  = guid.group(1).strip() if guid else ""
        if guid in seen_guids:
            continue
        seen_guids.add(guid)

        title = re.search(r"<title>(.*?)</title>", item)
        title = title.group(1).strip() if title else ""

        url = re.search(r'<enclosure url="([^"]+)"', item)
        url = url.group(1).strip() if url else ""

        if not url:
            continue

        if "flash-info" in guid:
            subtype = "flash_info"
            icon    = "📰"
            label   = _clean_title(title)
        elif "horoscope" in guid:
            subtype = "horoscope"
            icon    = "✨"
            label   = _clean_title(title)
        else:
            continue

        transitions.append({"type": "transition", "subtype": subtype,
                             "url": url, "label": label, "icon": icon})

    return transitions


def _clean_title(t: str) -> str:
    return t.replace("🌅", "").replace("🌙", "").strip()


def build_sequence(pool: list[dict], transitions: list[dict]) -> list[dict]:
    """Intercale les transitions toutes les TRACKS_PER_BLOCK pistes."""
    seq = []
    track_idx = 0
    trans_idx = 0

    # Démarrer par la première transition si disponible
    if transitions:
        seq.append(transitions[trans_idx % len(transitions)])
        trans_idx += 1

    while track_idx < len(pool):
        # Bloc de musique
        for _ in range(TRACKS_PER_BLOCK):
            if track_idx >= len(pool):
                break
            t = pool[track_idx]
            seq.append({
                "type":    "music",
                "videoId": t["videoId"],
                "title":   t.get("name", ""),
                "artist":  t.get("artist", ""),
                "genre":   t.get("genre", ""),
            })
            track_idx += 1

        # Transition suivante
        if transitions and track_idx < len(pool):
            seq.append(transitions[trans_idx % len(transitions)])
            trans_idx += 1

    return seq


def main():
    pool        = load_pool()
    transitions = load_transitions()

    if not pool:
        print("⚠️  Pool musical vide — radio_sequence.json non mis à jour.", file=sys.stderr)
        sys.exit(1)

    seq = build_sequence(pool, transitions)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps({
            "generated": datetime.now(timezone.utc).isoformat(),
            "tracks":    len([s for s in seq if s["type"] == "music"]),
            "transitions": len([s for s in seq if s["type"] == "transition"]),
            "sequence":  seq,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"✅ radio_sequence.json — {len(seq)} éléments "
          f"({len(pool)} pistes, {len(transitions)} transitions)")


if __name__ == "__main__":
    main()
