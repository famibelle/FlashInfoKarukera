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
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PLAYLIST_ID_FILE = Path("playlists/playlist_24h_id.txt")
PODCAST_XML = Path("docs/podcast.xml")
OUTPUT      = Path("docs/radio_sequence.json")
BROWSER_JSON = Path("browser.json")

_verbose: bool = False

TRACKS_PER_LINER   = 6   # pistes entre deux liners
TRACKS_PER_CAPSULE = 6   # pistes entre deux capsules culturelles
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


# ── YouTube Music Integration ───────────────────────────────────────────────


def _get_playlist_id() -> str | None:
    """Récupère l'ID de la playlist 24h depuis fichier ou environnement."""
    if PLAYLIST_ID_FILE.exists():
        return PLAYLIST_ID_FILE.read_text().strip()
    return os.getenv("YTMUSIC_PLAYLIST_24H_ID")


def _fetch_youtube_playlist(playlist_id: str) -> list[dict] | None:
    """Récupère les pistes depuis la playlist YouTube Music."""
    if not BROWSER_JSON.exists():
        print(f"   ⚠️  browser.json introuvable — impossible de fetch la playlist YouTube", file=sys.stderr)
        return None
    
    try:
        from ytmusicapi import YTMusic
        yt = YTMusic(str(BROWSER_JSON))
        playlist = yt.get_playlist(playlist_id, limit=500)
        return playlist.get("tracks", [])
    except Exception as e:
        print(f"   ⚠️  Erreur fetch playlist YouTube : {e}", file=sys.stderr)
        return None


# ── Nettoyage des fichiers audio anciens ─────────────────────────────────────

def _cleanup_old_audio(max_age_h: int = 48) -> int:
    """Supprime liners et capsules plus vieux que max_age_h heures.

    Utilise la date encodée dans le nom de fichier (pas le mtime, instable en CI).
    Liners  : liner-{bloc}-{YYYY}-W{WW}-*.mp3
    Capsules: capsule-{YYYY}-{MM}-{DD}-*.mp3
    """
    cutoff     = datetime.now(timezone.utc) - timedelta(hours=max_age_h)
    deleted    = 0
    liner_re   = re.compile(r'liner-\w+-(\d{4})-W(\d+)-')
    capsule_re = re.compile(r'capsule-(\d{4})-(\d{2})-(\d{2})-')

    for f in Path("docs/liners").glob("*.mp3") if Path("docs/liners").exists() else []:
        m = liner_re.match(f.name)
        if not m:
            continue
        try:
            # Utilise le dimanche (fin de semaine) pour éviter de supprimer
            # des liners générés en cours de semaine dont le lundi est > 48h
            week_end = datetime.fromisocalendar(int(m.group(1)), int(m.group(2)), 7).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if week_end < cutoff:
            f.unlink()
            deleted += 1

    for f in Path("docs/capsules").glob("*.mp3") if Path("docs/capsules").exists() else []:
        m = capsule_re.match(f.name)
        if not m:
            continue
        try:
            cap_dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
        except ValueError:
            continue
        if cap_dt < cutoff:
            f.unlink()
            deleted += 1

    return deleted


# ── Pool musical ──────────────────────────────────────────────────────────────

def load_pool(shuffle: bool = True) -> list[dict]:
    """
    Charge le pool musical directement depuis la playlist YouTube.
    Chaque piste contient : videoId, title, artist, duration, genre (vide si non disponible).
    """
    playlist_id = _get_playlist_id()
    if not playlist_id:
        print("   ❌ Impossible de récupérer l'ID de la playlist YouTube", file=sys.stderr)
        return []
    
    yt_tracks = _fetch_youtube_playlist(playlist_id)
    if not yt_tracks:
        print("   ❌ Impossible de récupérer la playlist YouTube", file=sys.stderr)
        return []
    
    pool = []
    for track in yt_tracks:
        if not track:
            continue
        video_id = track.get("videoId")
        if not video_id:
            continue
        
        title = track.get("title", "")
        artists = track.get("artists", [{"name": ""}])
        artist = ", ".join(a.get("name", "") for a in artists if a.get("name"))
        duration = track.get("duration_seconds") or track.get("duration", 0)
        
        pool.append({
            "videoId": video_id,
            "duration": duration,
            "genre": "",  # Genre non disponible via YouTube API, non utilisé par radio.html
            "name": title,
            "artist": artist,
        })
    
    print(f"   ✅ Pool chargé depuis YouTube : {len(pool)} pistes")
    if shuffle:
        random.shuffle(pool)
    return pool


# ── Transitions depuis le podcast RSS ────────────────────────────────────────

def load_transitions() -> dict[str, list[dict]]:
    """
    Retourne { "flash_matin": {...}, "horoscope_matin": {...},
               "flash_midi": {...},
               "flash_soir": {...}, "horoscope_soir": {...} }
    En cas d'épisodes multiples pour un slot, garde le plus récent.
    
    Priorité :
    1. Fichiers locaux dans docs/audio/ (plus fiable, indépendant du podcast.xml)
    2. Podcast RSS (podcast.xml) comme fallback
    """
    from datetime import datetime
    slots: dict[str, dict] = {}
    
    # 1. D'abord, essayer de charger depuis les fichiers locaux (plus récent)
    audio_dir = Path("docs/audio")
    today = datetime.utcnow().strftime("%Y-%m-%d")
    today_compact = today.replace("-", "")  # 2026-05-07 -> 20260507
    
    # Flash Info
    for edition in ["matin", "midi", "soir"]:
        flash_path = audio_dir / "flash-info" / today[:7]
        if flash_path.exists():
            # Essayer plusieurs patterns (avec/sans tirets dans la date)
            patterns = [
                f"flash-info-{today_compact}-{edition}.mp3",
                f"flash-info-{today}-{edition}.mp3",
            ]
            for pattern in patterns:
                files = list(flash_path.glob(pattern))
                if files:
                    f = files[0]
                    url = f"https://famibelle.github.io/FlashInfoKarukera/audio/flash-info/{today[:7]}/{f.name}"
                    label = f"Flash Info Guadeloupe — {today}, édition du {edition}"
                    slot_name = f"flash_{edition}"
                    if slot_name not in slots:
                        slots[slot_name] = {
                            "type": "transition", 
                            "subtype": "flash_info",
                            "url": url, 
                            "label": label, 
                            "icon": "📰"
                        }
                    break
    
    # Horoscopes
    for edition in ["matin", "soir"]:
        horo_path = audio_dir / "horoscope" / today[:7]
        if horo_path.exists():
            # Essayer plusieurs patterns (avec/sans tirets dans la date)
            patterns = [
                f"horoscope-{today_compact}-{edition}.mp3",
                f"horoscope-{today}-{edition}.mp3",
            ]
            for pattern in patterns:
                files = list(horo_path.glob(pattern))
                if files:
                    f = files[0]
                    url = f"https://famibelle.github.io/FlashInfoKarukera/audio/horoscope/{today[:7]}/{f.name}"
                    label = f"Horoscope {edition} — {today}"
                    slot_name = f"horoscope_{edition}"
                    if slot_name not in slots:
                        slots[slot_name] = {
                            "type": "transition",
                            "subtype": "horoscope", 
                            "url": url,
                            "label": label, 
                            "icon": "✨"
                        }
                    break
    
    # 2. Fallback : charger depuis le podcast RSS si fichiers locaux non trouvés
    if not PODCAST_XML.exists():
        return slots

    xml   = PODCAST_XML.read_text(encoding="utf-8")
    items = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)

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

    # 3. Pré-remplir les slots attendus du jour non encore générés.
    # On remplace aussi les slots RSS qui pointent vers un jour précédent.
    def _is_today(slot_url: str) -> bool:
        return today in slot_url or today_compact in slot_url

    for edition in ["matin", "midi", "soir"]:
        slot_name = f"flash_{edition}"
        if slot_name not in slots or not _is_today(slots[slot_name]["url"]):
            url = (f"https://famibelle.github.io/FlashInfoKarukera/audio/flash-info"
                   f"/{today[:7]}/flash-info-{today_compact}-{edition}.mp3")
            slots[slot_name] = {
                "type": "transition", "subtype": "flash_info",
                "url": url,
                "label": f"Flash Info Guadeloupe — {today}, édition du {edition}",
                "icon": "📰", "pending": True,
            }
    for edition in ["matin", "soir"]:
        slot_name = f"horoscope_{edition}"
        if slot_name not in slots or not _is_today(slots[slot_name]["url"]):
            url = (f"https://famibelle.github.io/FlashInfoKarukera/audio/horoscope"
                   f"/{today[:7]}/horoscope-{today_compact}-{edition}.mp3")
            slots[slot_name] = {
                "type": "transition", "subtype": "horoscope",
                "url": url,
                "label": f"Horoscope {edition} — {today}",
                "icon": "✨", "pending": True,
            }

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
        from generate_liner import get_capsule_mp3_url
        url = get_capsule_mp3_url(f"{bloc}-{position}")
        if url:
            return {"type": "capsule", "url": url, "label": "Capsule culturelle Guadeloupe", "icon": "🌺"}
    except Exception as e:
        print(f"   ⚠️  Capsule {bloc}-{position} ignorée : {e}", file=sys.stderr)
    return None


def get_liner(artists: list[str], bloc: str, voice: str = "corinne") -> dict | None:
    """
    Génère ou récupère le liner MP3 pour ce groupe d'artistes.
    Retourne { type:"liner", url, label } ou None si non disponible.
    
    Args:
        artists: Liste des artistes à annoncer
        bloc: Moment de la journée (matin/midi/soir)
        voice: "solitude" ou "corinne" (défaut: corinne)
    """
    if not artists:
        return None
    try:
        from generate_liner import get_announcement_mp3_url
        url, label = get_announcement_mp3_url(bloc, artists[:5], voice=voice, verbose=_verbose)
        if url and label:
            return {"type": "liner", "url": url, "label": label, "icon": "🎙️"}
        elif url:
            # Fallback si label vide (cache ancien sans JSON)
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
        group       = tracks[i : i + TRACKS_PER_LINER]
        tracks_done = i + len(group)
        artists     = list(dict.fromkeys(t.get("artist", "") for t in group if t.get("artist")))
        print(f"    🎙️  Liner {bloc} [{i+1}-{tracks_done}] — {', '.join(artists[:3])}", flush=True)
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
        if tracks_done % TRACKS_PER_CAPSULE == 0:
            print(f"    🌺 Capsule {bloc}-{tracks_done} (après {tracks_done} pistes)", flush=True)
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
        print(f"\n── Bloc {bloc} ({size} pistes) ──────────────────────────────", flush=True)
        if bloc in ("matin", "soir"):
            flash_key = f"flash_{bloc}"
            if flash_key in slots:
                print(f"  📰 Flash info {bloc}", flush=True)
                seq.append(slots[flash_key])

            first_group   = pool[pos : pos + HOROSCOPE_AFTER]
            first_artists = list(dict.fromkeys(t.get("artist", "") for t in first_group if t.get("artist")))
            print(f"  🎙️  Liner {bloc} [1-{HOROSCOPE_AFTER}] — {', '.join(first_artists[:3])}", flush=True)
            liner = get_liner(first_artists[:5], bloc)
            if liner:
                seq.append(liner)
            seq += _raw_music(first_group)
            pos += HOROSCOPE_AFTER
            print(f"  🌺 Capsule {bloc}-pre (après {HOROSCOPE_AFTER} pistes)", flush=True)
            capsule = get_capsule(bloc, 0)
            if capsule:
                seq.append(capsule)

            horo_key = f"horoscope_{bloc}"
            if horo_key in slots:
                print(f"  ✨ Horoscope {bloc}", flush=True)
                seq.append(slots[horo_key])

            remaining = size - HOROSCOPE_AFTER
            print(f"  🎵 {remaining} pistes avec liners/capsules…", flush=True)
            seq += _music_with_liners(pool[pos : pos + remaining], bloc)
            pos += remaining

        elif bloc == "midi":
            if "flash_midi" in slots:
                print(f"  📰 Flash info midi", flush=True)
                seq.append(slots["flash_midi"])
                # Insert interview after flash info midi
                interview_path = Path("docs/audio/Emissions") / f"interview-resistance-creole-{date.today().isoformat()}.mp3"
                if interview_path.exists():
                    gh_url = f"https://famibelle.github.io/FlashInfoKarukera/audio/Emissions/{interview_path.name}"
                    seq.append({
                        "type": "transition", "subtype": "interview",
                        "url": gh_url,
                        "label": f"Interview — Creole Resistance Symbols — {date.today().isoformat()}",
                        "icon": "🎙️"
                    })
                    print(f"  🎙️  Interview insérée après flash info midi", flush=True)
                
                # Insert emission after interview (or after flash info if no interview)
                emission_date = date.today().isoformat()
                emission_path = Path("docs/audio/Emissions") / f"emission-{emission_date}.mp3"
                gh_url = f"https://famibelle.github.io/FlashInfoKarukera/audio/Emissions/emission-{emission_date}.mp3"
                seq.append({
                    "type": "transition", "subtype": "emission",
                    "url": gh_url,
                    "label": f"Émission culturelle — Découverte de la Guadeloupe — {emission_date}",
                    "icon": "🎤",
                    **({"pending": True} if not emission_path.exists() else {}),
                })
                if emission_path.exists():
                    print(f"  🎤  Émission insérée après flash info midi", flush=True)
                else:
                    print(f"  🎤  Émission pré-réservée (pas encore générée)", flush=True)
            print(f"  🎵 {size} pistes avec liners/capsules…", flush=True)
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
    parser.add_argument("--test-liner",   metavar="ARTISTES",
                        help="Teste la génération d'un liner (artistes séparés par des virgules)")
    parser.add_argument("--test-capsule", action="store_true",
                        help="Teste la génération et la lecture d'une capsule culturelle")
    parser.add_argument("--slot",         default="test-0",
                        help="Identifiant de slot pour --test-capsule (défaut : test-0)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Affiche le prompt envoyé au LLM et le texte généré")
    parser.add_argument("--bloc",         choices=["matin", "midi", "soir"], default="matin",
                        help="Bloc pour --test-liner (défaut : matin)")
    parser.add_argument("--skip-liners", action="store_true",
                        help="Construit la séquence sans générer de liners (rapide)")
    parser.add_argument("--dry-run",     action="store_true",
                        help="Affiche la séquence sans écrire radio_sequence.json")
    parser.add_argument("--programme",   action="store_true",
                        help="Affiche le programme détaillé de la journée avec horaires estimés")
    parser.add_argument("--generate-liners-only", action="store_true",
                        help="Génère uniquement les liners pour la journée (matin/midi/soir)")
    parser.add_argument("--generate-capsules-only", action="store_true",
                        help="Génère uniquement les capsules culturelles pour la journée")
    args = parser.parse_args()

    global _verbose
    _verbose = bool(args.verbose)

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

    # ── --test-capsule ────────────────────────────────────────────────────────
    if args.test_capsule:
        import subprocess
        slot_id = args.slot
        print(f"Test capsule — slot : {slot_id}")
        print("  Appel get_capsule_mp3_url…")
        from datetime import date
        from generate_liner import get_capsule_mp3_url, load_cache
        url = get_capsule_mp3_url(slot_id, verbose=args.verbose)
        if not url:
            print("⚠️  Capsule non générée (voir les erreurs ci-dessus)")
            return
        cache     = load_cache()
        cache_key = f"capsule_{date.today().isoformat()}_{slot_id}"
        text      = cache.get(cache_key + "_text", "")
        print(f"✅ Capsule générée")
        print(f"   URL     : {url}")
        if text:
            print(f"\n   Texte généré :\n")
            for line in text.strip().splitlines():
                print(f"     {line}")
            print()
        local = Path("docs/capsules") / url.rsplit("/", 1)[-1]
        if local.exists():
            size_kb = local.stat().st_size // 1024
            print(f"   Fichier : {local} ({size_kb} Ko)")
        else:
            print(f"   ⚠️  Fichier local introuvable : {local}")
            return
        for player in ("mpg123", "mpg321", "ffplay", "aplay"):
            if subprocess.run(["which", player], capture_output=True).returncode == 0:
                print(f"\n▶ Lecture avec {player} :")
                subprocess.run([player, str(local)])
                break
        else:
            print("⚠️  Aucun lecteur audio trouvé (mpg123, mpg321, ffplay, aplay)")
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

    # ── --generate-liners-only ────────────────────────────────────────────
    if args.generate_liners_only:
        print("🎙️  Génération des liners pour tous les blocs...")
        # Charger le pool SANS shuffle pour une répartition déterministe
        pool = load_pool(shuffle=False)
        if not pool:
            print("  ⚠️  Pool vide — impossible de générer les liners")
            return
        
        # Répartir les pistes par bloc selon BLOCK_SIZES (27, 27, 26)
        # Sans shuffle, l'ordre est déterministe
        offsets = {"matin": 0, "midi": BLOCK_SIZES["matin"], "soir": BLOCK_SIZES["matin"] + BLOCK_SIZES["midi"]}
        
        for bloc in ["matin", "midi", "soir"]:
            start = offsets[bloc]
            end = start + BLOCK_SIZES[bloc]
            bloc_tracks = pool[start:end]
            
            # Extraire les artistes uniques de ce bloc
            artists = list(dict.fromkeys(
                t.get("artist", "") for t in bloc_tracks if t.get("artist")
            ))[:10]  # Max 10 artistes par liner
            
            print(f"\n  Bloc : {bloc} ({len(bloc_tracks)} pistes, {len(artists)} artistes)")
            if artists:
                liner = get_liner(artists, bloc)
                if liner:
                    print(f"  ✅ Liner généré : {liner['label']}")
                    print(f"     URL : {liner['url']}")
                else:
                    print(f"  ⚠️  Liner non généré pour {bloc}")
            else:
                print(f"  ⚠️  Aucun artiste trouvé pour {bloc}")
        return

    # ── --generate-capsules-only ───────────────────────────────────────────
    if args.generate_capsules_only:
        print("🌺 Génération des capsules culturelles pour tous les slots...")
        # Slots typiques : matin-0, matin-6, matin-12, matin-18, midi-0, midi-6, midi-12, midi-18, midi-24, soir-0, soir-6, soir-12, soir-18
        slots = [
            ("matin", 0), ("matin", 6), ("matin", 12), ("matin", 18),
            ("midi", 0), ("midi", 6), ("midi", 12), ("midi", 18), ("midi", 24),
            ("soir", 0), ("soir", 6), ("soir", 12), ("soir", 18)
        ]
        for bloc, position in slots:
            slot_id = f"{bloc}-{position}"
            print(f"\n  Slot : {slot_id}")
            capsule = get_capsule(bloc, position)
            if capsule:
                print(f"  ✅ Capsule générée : {capsule['label']}")
                print(f"     URL : {capsule['url']}")
            else:
                print(f"  ⚠️  Capsule non générée pour {slot_id}")
        return

    # ── Génération complète ───────────────────────────────────────────────────
    deleted = _cleanup_old_audio()
    if deleted:
        print(f"🧹 {deleted} fichier(s) audio supprimé(s) (> 48h)", flush=True)

    pool  = load_pool()
    slots = load_transitions()

    if not pool:
        print("⚠️  Pool musical vide — radio_sequence.json non mis à jour.", file=sys.stderr)
        sys.exit(1)
    if not slots:
        print("⚠️  Aucune transition trouvée dans podcast.xml", file=sys.stderr)

    # Neutraliser get_liner si --skip-liners
    if args.skip_liners:
        # Redéfinir la fonction pour qu'elle retourne None sans appeler Mistral/TTS
        def get_liner(artists, bloc):
            return None

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
