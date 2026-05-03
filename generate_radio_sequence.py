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

TRACKS_PER_LINER   = 6   # pistes entre deux liners
TRACKS_PER_CAPSULE = 12  # pistes entre deux capsules culturelles
HOROSCOPE_AFTER    = 6   # chansons entre flash info et horoscope

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


# ── Durées ────────────────────────────────────────────────────────────────────

def _duration_pool() -> dict[str, int]:
    """videoId → durée en secondes depuis le pool cache."""
    if not POOL_CACHE.exists():
        return {}
    data = json.loads(POOL_CACHE.read_text())
    return {t["videoId"]: t.get("duration", 0) for t in data.get("tracks", [])}


def _duration_transitions() -> dict[str, int]:
    """url → durée en secondes depuis les itunes:duration du podcast RSS."""
    if not PODCAST_XML.exists():
        return {}
    xml   = PODCAST_XML.read_text(encoding="utf-8")
    items = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)
    result: dict[str, int] = {}
    for item in items:
        url = re.search(r'<enclosure url="([^"]+\.mp3)"', item)
        dur = re.search(r"<itunes:duration>(\d+:\d+(?::\d+)?)</itunes:duration>", item)
        if url and dur:
            result[url.group(1)] = _parse_hms(dur.group(1))
    return result


def _parse_hms(s: str) -> int:
    """'MM:SS' ou 'HH:MM:SS' → secondes."""
    parts = [int(x) for x in s.split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0


def _liner_duration(url: str) -> int:
    """Estime la durée d'un liner depuis la taille du fichier local (128 kbps)."""
    filename = url.rsplit("/", 1)[-1]
    local    = Path("docs/liners") / filename
    if local.exists():
        return max(5, int(local.stat().st_size * 8 // 128_000))
    return 25


def _fmt_clock(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h:02d}:{m:02d}"


def _fmt_dur(seconds: int) -> str:
    if seconds <= 0:
        return "?:??"
    if seconds < 3600:
        return f"{seconds // 60}:{seconds % 60:02d}"
    return f"{seconds // 3600}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


# ── Liners ────────────────────────────────────────────────────────────────────


def get_capsule(bloc: str, position: int) -> dict | None:
    """Génère ou récupère la capsule culturelle pour ce slot."""
    try:
        from youtube_uploader import get_capsule_mp3_url
        url = get_capsule_mp3_url(f"{bloc}-{position}")
        if url:
            return {"type": "capsule", "url": url, "label": "Capsule culturelle Guadeloupe", "icon": "🌺"}
    except Exception as e:
        print(f"   ⚠️  Capsule {bloc}-{position} ignorée : {e}", file=sys.stderr)
    return None


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
    """Intercale un liner toutes les TRACKS_PER_LINER pistes et une capsule toutes les TRACKS_PER_CAPSULE."""
    result = []
    for i in range(0, len(tracks), TRACKS_PER_LINER):
        group   = tracks[i : i + TRACKS_PER_LINER]
        artists = list(dict.fromkeys(t.get("artist", "") for t in group if t.get("artist")))
        liner   = get_liner(artists[:5], bloc)
        if liner:
            result.append(liner)
        for t in group:
            item: dict = {
                "type":    "music",
                "videoId": t["videoId"],
                "title":   t.get("name",   ""),
                "artist":  t.get("artist", ""),
                "genre":   t.get("genre",  ""),
            }
            if t.get("duration"):
                item["duration"] = t["duration"]
            result.append(item)
        tracks_done = i + len(group)
        if tracks_done % TRACKS_PER_CAPSULE == 0:
            capsule = get_capsule(bloc, tracks_done)
            if capsule:
                result.append(capsule)
    return result


def _raw_music(tracks: list[dict]) -> list[dict]:
    """Convertit des pistes du pool en items music sans liner."""
    result = []
    for t in tracks:
        item: dict = {
            "type":    "music",
            "videoId": t["videoId"],
            "title":   t.get("name",   ""),
            "artist":  t.get("artist", ""),
            "genre":   t.get("genre",  ""),
        }
        if t.get("duration"):
            item["duration"] = t["duration"]
        result.append(item)
    return result


def build_sequence(pool: list[dict], slots: dict[str, dict]) -> list[dict]:
    seq = []
    pos = 0

    for bloc, size in BLOCK_SIZES.items():
        if bloc in ("matin", "soir"):
            # Flash info
            flash_key = f"flash_{bloc}"
            if flash_key in slots:
                seq.append(slots[flash_key])

            # HOROSCOPE_AFTER chansons sans liner
            seq += _raw_music(pool[pos : pos + HOROSCOPE_AFTER])
            pos += HOROSCOPE_AFTER

            # Horoscope
            horo_key = f"horoscope_{bloc}"
            if horo_key in slots:
                seq.append(slots[horo_key])

            # Reste du bloc avec liners toutes les TRACKS_PER_LINER pistes
            remaining = size - HOROSCOPE_AFTER
            seq += _music_with_liners(pool[pos : pos + remaining], bloc)
            pos += remaining

        elif bloc == "midi":
            if "flash_midi" in slots:
                seq.append(slots["flash_midi"])
            seq += _music_with_liners(pool[pos : pos + size], bloc)
            pos += size

    return seq


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Génère la séquence radio 24h")
    parser.add_argument("--pool",        action="store_true",
                        help="Affiche le pool musical et quitte")
    parser.add_argument("--transitions", action="store_true",
                        help="Affiche les transitions du podcast RSS et quitte")
    parser.add_argument("--test-liner",  metavar="ARTISTES",
                        help="Teste la génération d'un liner (artistes séparés par des virgules)")
    parser.add_argument("--bloc",        choices=["matin", "midi", "soir"], default="matin",
                        help="Bloc pour --test-liner (défaut : matin)")
    parser.add_argument("--skip-liners", action="store_true",
                        help="Construit la séquence sans générer de liners (rapide)")
    parser.add_argument("--dry-run",     action="store_true",
                        help="Affiche la séquence sans écrire radio_sequence.json")
    parser.add_argument("--programme",   action="store_true",
                        help="Affiche le programme détaillé de la journée avec horaires estimés")
    args = parser.parse_args()

    # ── --pool ────────────────────────────────────────────────────────────────
    if args.pool:
        pool = load_pool()
        print(f"Pool musical : {len(pool)} pistes")
        genres: dict[str, int] = {}
        for t in pool:
            genres[t.get("genre", "?")] = genres.get(t.get("genre", "?"), 0) + 1
        for g, n in sorted(genres.items(), key=lambda x: -x[1]):
            print(f"  {g:<20} {n} pistes")
        return

    # ── --transitions ─────────────────────────────────────────────────────────
    if args.transitions:
        slots = load_transitions()
        if not slots:
            print("Aucune transition trouvée dans podcast.xml")
            return
        print(f"{len(slots)} transitions chargées :")
        for key, item in slots.items():
            print(f"  [{key}]  {item['icon']} {item['label'][:60]}")
            print(f"          {item['url']}")
        return

    # ── --test-liner ──────────────────────────────────────────────────────────
    if args.test_liner:
        artists = [a.strip() for a in args.test_liner.split(",") if a.strip()]
        print(f"Test liner — bloc: {args.bloc} — artistes: {artists}")
        liner = get_liner(artists, args.bloc)
        if liner:
            print(f"✅ Liner généré : {liner['label']}")
            print(f"   URL : {liner['url']}")
            local = Path("docs/liners") / liner["url"].rsplit("/", 1)[-1]
            if local.exists():
                print(f"   Fichier : {local} ({local.stat().st_size // 1024} Ko)")
        else:
            print("⚠️  Liner non généré (voir les erreurs ci-dessus)")
        return

    # ── --programme ───────────────────────────────────────────────────────────
    if args.programme:
        if not OUTPUT.exists():
            print("⚠️  radio_sequence.json introuvable — génère-la d'abord.", file=sys.stderr)
            sys.exit(1)
        data       = json.loads(OUTPUT.read_text())
        seq        = data["sequence"]
        dur_pool   = _duration_pool()
        dur_trans  = _duration_transitions()

        cursor      = 0
        total_music = 0
        n_music     = 0

        print(f"Programme du {data['generated'][:10]} "
              f"({data['music']} pistes · {data['liners']} liners · {data['transitions']} transitions)\n")

        for item in seq:
            t = item["type"]
            if t == "music":
                dur  = item.get("duration") or dur_pool.get(item.get("videoId", ""), 0)
                icon = "🎵"
                desc = f"{item['title']} — {item['artist']}"
                if item.get("genre"):
                    desc += f"  [{item['genre']}]"
                total_music += dur
                n_music     += 1
            elif t == "transition":
                dur  = dur_trans.get(item["url"], 0)
                icon = item.get("icon", "📻")
                desc = item["label"][:72]
            else:  # liner
                dur  = _liner_duration(item["url"])
                icon = "🎙️"
                desc = item["label"][:72]

            dur_str = f"  ({_fmt_dur(dur)})" if dur else ""
            print(f"  {_fmt_clock(cursor)}  {icon}  {desc}{dur_str}")
            cursor += dur

        print(f"\n  Durée totale estimée : {_fmt_dur(cursor)}")
        print(f"  Musique             : {_fmt_dur(total_music)}  ({n_music} pistes)")
        return

    # ── Génération complète ───────────────────────────────────────────────────
    pool  = load_pool()
    slots = load_transitions()

    if not pool:
        print("⚠️  Pool musical vide — radio_sequence.json non mis à jour.", file=sys.stderr)
        sys.exit(1)
    if not slots:
        print("⚠️  Aucune transition trouvée dans podcast.xml", file=sys.stderr)

    # Neutraliser get_liner si --skip-liners
    if args.skip_liners:
        import generate_radio_sequence as _self
        _self.get_liner = lambda artists, bloc: None

    seq = build_sequence(pool, slots)

    n_music    = sum(1 for s in seq if s["type"] == "music")
    n_liners   = sum(1 for s in seq if s["type"] == "liner")
    n_capsules = sum(1 for s in seq if s["type"] == "capsule")
    n_transit  = sum(1 for s in seq if s["type"] == "transition")

    print(f"Séquence : {len(seq)} éléments "
          f"({n_music} pistes · {n_liners} liners · {n_capsules} capsules · {n_transit} transitions)")

    if args.dry_run:
        for item in seq:
            if item["type"] == "music":
                print(f"  🎵 {item['title']} — {item['artist']}")
            elif item["type"] == "liner":
                print(f"  🎙️  [liner] {item['label']}")
            elif item["type"] == "capsule":
                print(f"  🌺 [capsule] {item['label']}")
            else:
                print(f"  {item['icon']} [{item['subtype']}] {item['label'][:60]}")
        return

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps({
            "generated":   datetime.now(timezone.utc).isoformat(),
            "music":       n_music,
            "liners":      n_liners,
            "capsules":    n_capsules,
            "transitions": n_transit,
            "sequence":    seq,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"✅ radio_sequence.json — {len(seq)} éléments "
          f"({n_music} pistes · {n_liners} liners · {n_capsules} capsules · {n_transit} transitions)")


if __name__ == "__main__":
    main()
