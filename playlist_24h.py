#!/usr/bin/env python3
"""
Playlist 24h — Botiran News Radio
Construit une playlist ~24h avec flash info et horoscopes positionnés à 6h, 12h, 18h.
Le pool musical est mis en cache une fois par jour pour éviter 200+ recherches à chaque run.
"""

import os
import sys
import json
import time
import random
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from ytmusicapi import YTMusic
from caribbean_db import CARIBBEAN_TRACKS
from youtube_uploader import get_or_upload_episode, get_or_upload_horoscope, get_or_upload_announcement

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BROWSER_JSON     = os.getenv("YTMUSIC_BROWSER_JSON_PATH", "browser.json")
POOL_CACHE_FILE  = Path("playlists/music_pool_cache.json")
PLAYLIST_ID_FILE = Path("playlists/playlist_24h_id.txt")

AVG_DURATION = 210  # secondes — fallback si duration_seconds absent

# 100 pistes max (limite YouTube Music API)
# 5 slots spéciaux (flash ×3 + horoscope ×2) → 95 pistes musicales
TRACKS_MORNING  = 31   # [4–34]  après flash matin + horoscope matin + annonce
TRACKS_MIDDAY   = 31   # [37–67] après flash midi + annonce
TRACKS_EVENING  = 30   # [71–100] après flash soir + horoscope soir + annonce

# Genres par bloc pour varier l'ambiance
BLOCK_GENRES = {
    "morning":   ["zouk", "zouk_retro", "gwoka", "chatta"],
    "midday":    ["kompa", "zouk", "chatta"],
    "evening":   ["gwoka", "bouillon", "zouk_retro", "kompa"],
}


# ── Auth ──────────────────────────────────────────────────────────────────────

def init_ytmusic() -> YTMusic:
    if not os.path.exists(BROWSER_JSON):
        logger.error(f"Auth file not found: {BROWSER_JSON}")
        sys.exit(1)
    return YTMusic(BROWSER_JSON)


# ── Pool musical ──────────────────────────────────────────────────────────────

def _search(yt: YTMusic, name: str, artist: str):
    """Retourne (videoId, duration_seconds) ou (None, 0)."""
    for query in [f"{name} {artist}", name]:
        try:
            results = yt.search(query, filter="songs", limit=10)
            for r in results:
                r_artists = ", ".join(a["name"] for a in (r.get("artists") or []))
                a = artist.lower()
                b = r_artists.lower()
                if a in b or b in a or any(w in b for w in a.split() if len(w) > 3):
                    dur = r.get("duration_seconds") or AVG_DURATION
                    return r["videoId"], dur
        except Exception as e:
            logger.warning(f"  Erreur recherche '{name}': {e}")
            break
    return None, 0


def resolve_music_pool(yt: YTMusic) -> list:
    """
    Résout tous les titres de la DB en videoIds.
    Résultat : [{"videoId": ..., "duration": ..., "genre": ..., "name": ..., "artist": ...}]
    Cache valide pour la journée (clé = date du jour).
    """
    today = datetime.now().strftime("%Y-%m-%d")

    if POOL_CACHE_FILE.exists():
        cached = json.loads(POOL_CACHE_FILE.read_text(encoding="utf-8"))
        tracks = cached.get("tracks", [])
        cache_has_metadata = tracks and "name" in tracks[0]
        if cached.get("date") == today and cache_has_metadata:
            logger.info(f"Pool musical depuis cache ({len(tracks)} pistes, {today})")
            return tracks
        elif cached.get("date") == today:
            logger.info("Cache du jour présent mais sans métadonnées — résolution complète")

    logger.info("Résolution du pool musical (200+ recherches YTMusic)...")
    pool = []
    seen = set()

    for genre, tracks in CARIBBEAN_TRACKS.items():
        for track in tracks:
            name   = track["name"]
            artist = track["artists"][0] if track["artists"] else ""
            vid, dur = _search(yt, name, artist)
            if vid and vid not in seen:
                pool.append({"videoId": vid, "duration": dur, "genre": genre, "name": name, "artist": artist})
                seen.add(vid)
                logger.info(f"  ✓ [{genre}] {name} — {artist}")
            else:
                logger.warning(f"  ✗ [{genre}] {name} — {artist}")

    POOL_CACHE_FILE.parent.mkdir(exist_ok=True)
    POOL_CACHE_FILE.write_text(
        json.dumps({"date": today, "tracks": pool}, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    logger.info(f"Pool : {len(pool)} pistes résolues — cache sauvegardé")
    return pool


# ── Construction des blocs ────────────────────────────────────────────────────

def fill_block(pool: list, genres: list, n: int) -> list:
    """
    Retourne exactement n entrées {videoId, artist} du pool filtrées par genre.
    Répète le sous-pool (shufflé) si nécessaire.
    """
    sub = [t for t in pool if t["genre"] in genres]
    if not sub:
        sub = pool

    result = []
    while len(result) < n:
        random.shuffle(sub)
        for track in sub:
            if len(result) >= n:
                break
            result.append({"videoId": track["videoId"], "artist": track.get("artist", "")})

    return result


def _add_special(playlist: list, label: str, fn):
    """Appelle fn(), ajoute le videoId à la playlist si disponible."""
    try:
        vid = fn()
        if vid:
            playlist.append(vid)
            logger.info(f"  {label} → https://youtu.be/{vid}")
    except Exception as e:
        logger.warning(f"  {label} ignoré : {e}")


# ── Playlist 24h ──────────────────────────────────────────────────────────────

def _block_artists(block: list, n: int = 3) -> list[str]:
    """Extrait les n premiers artistes uniques d'un bloc fill_block."""
    seen = []
    for t in block:
        a = t.get("artist", "").strip()
        if a and a not in seen:
            seen.append(a)
        if len(seen) >= n:
            break
    return seen


def build_24h_playlist(yt: YTMusic) -> List[str]:
    """
    Structure (100 pistes max — limite YouTube Music API) :
      [1]      Flash Info matin
      [2]      Horoscope matin
      [3]      Annonce matin (Solitude)
      [4–34]   31 pistes  zouk + zouk_retro + gwoka + chatta
      [35]     Flash Info midi
      [36]     Annonce midi (Solitude)
      [37–67]  31 pistes  kompa + zouk + chatta
      [68]     Flash Info soir
      [69]     Horoscope soir
      [70]     Annonce soirée (Solitude)
      [71–100] 30 pistes  gwoka + bouillon + zouk_retro + kompa
    """
    pool = resolve_music_pool(yt)
    if not pool:
        logger.error("Pool vide — abandon")
        sys.exit(1)

    playlist = []

    # Slots 1-2 — Flash Info matin + Horoscope matin
    logger.info("Slots 1-2 — Flash Info matin + Horoscope matin")
    _add_special(playlist, "Flash Info matin", lambda: get_or_upload_episode("morning"))
    _add_special(playlist, "Horoscope matin",  lambda: get_or_upload_horoscope("morning"))

    # Bloc matin [4-34]
    logger.info(f"Bloc matin ({TRACKS_MORNING} pistes)...")
    block_morning = fill_block(pool, BLOCK_GENRES["morning"], TRACKS_MORNING)
    artists_morning = _block_artists(block_morning)
    _add_special(playlist, "Annonce matin",
                 lambda: get_or_upload_announcement("morning", artists_morning))
    playlist += [t["videoId"] for t in block_morning]

    # Slot 35 — Flash Info midi
    logger.info("Slot 35 — Flash Info midi")
    _add_special(playlist, "Flash Info midi", lambda: get_or_upload_episode("midday"))

    # Bloc après-midi [37-67]
    logger.info(f"Bloc après-midi ({TRACKS_MIDDAY} pistes)...")
    block_midday = fill_block(pool, BLOCK_GENRES["midday"], TRACKS_MIDDAY)
    artists_midday = _block_artists(block_midday)
    _add_special(playlist, "Annonce midi",
                 lambda: get_or_upload_announcement("midday", artists_midday))
    playlist += [t["videoId"] for t in block_midday]

    # Slots 68-69 — Flash Info soir + Horoscope soir
    logger.info("Slots 68-69 — Flash Info soir + Horoscope soir")
    _add_special(playlist, "Flash Info soir",  lambda: get_or_upload_episode("evening"))
    _add_special(playlist, "Horoscope soir",   lambda: get_or_upload_horoscope("evening"))

    # Bloc soirée [71-100]
    logger.info(f"Bloc soirée ({TRACKS_EVENING} pistes)...")
    block_evening = fill_block(pool, BLOCK_GENRES["evening"], TRACKS_EVENING)
    artists_evening = _block_artists(block_evening)
    _add_special(playlist, "Annonce soirée",
                 lambda: get_or_upload_announcement("evening", artists_evening))
    playlist += [t["videoId"] for t in block_evening]

    special_count = 8  # flash×3 + horoscope×2 + annonce×3
    music_count   = len(playlist) - special_count
    logger.info(f"Playlist : {len(playlist)} items ({music_count} pistes musicales, {special_count} slots spéciaux)")
    return playlist


# ── Gestion de la playlist YTMusic ───────────────────────────────────────────

def get_playlist_id(yt: YTMusic) -> str:
    """Retourne l'ID de la playlist 24h. La crée si elle n'existe pas encore."""
    if PLAYLIST_ID_FILE.exists():
        pid = PLAYLIST_ID_FILE.read_text().strip()
        if pid:
            return pid

    env_id = os.getenv("YTMUSIC_PLAYLIST_24H_ID")
    if env_id:
        PLAYLIST_ID_FILE.parent.mkdir(exist_ok=True)
        PLAYLIST_ID_FILE.write_text(env_id)
        return env_id

    logger.info("Création de la playlist 24h...")
    pid = yt.create_playlist(
        "Botiran News: La radio de la diaspora Guadeloupéenne au Luxembourg — 24h",
        "Playlist radio 24h — Flash Info, Horoscope & musique caribéenne",
        privacy_status="PUBLIC",
    )
    PLAYLIST_ID_FILE.parent.mkdir(exist_ok=True)
    PLAYLIST_ID_FILE.write_text(pid)
    logger.info(f"Playlist créée : {pid}")
    logger.info(f"→ Ajoute ce secret GitHub : YTMUSIC_PLAYLIST_24H_ID={pid}")
    return pid


def _get_removable(yt: YTMusic, playlist_id: str) -> list:
    try:
        tracks = yt.get_playlist(playlist_id, limit=200).get("tracks", [])
        return [t for t in tracks if t.get("setVideoId")]
    except Exception:
        return []


def _remove_all(yt: YTMusic, playlist_id: str, removable: list):
    if removable:
        yt.remove_playlist_items(playlist_id, removable)
        logger.info(f"  Supprimé {len(removable)} pistes")
        time.sleep(2)


def update_playlist(yt: YTMusic, playlist_id: str, video_ids: List[str]):
    """
    Règle YouTube Music : après remove(N), un seul add(M) fonctionne si M ≤ 2×N.
    Bootstrap depuis 0 → 1 → 25 → 50 → 100 si nécessaire.
    Run normal (playlist déjà à 100) : remove 100 → add 100 en un seul appel.
    """
    logger.info(f"Mise à jour playlist {playlist_id} ({len(video_ids)} items)...")

    removable = _get_removable(yt, playlist_id)
    current   = len(removable)
    target    = len(video_ids)

    if current >= target // 2:
        # Run normal : remove tout → add tout en un seul appel
        _remove_all(yt, playlist_id, removable)
        yt.add_playlist_items(playlist_id, video_ids)
        logger.info(f"  Ajouté {target}/{target}")
    else:
        # Bootstrap depuis zéro : remove tout → 1 → 25 → 50 → target
        # Chaque étape : add N, wait 6s (setVideoId propagation), remove N, wait 5s, add 2N
        logger.info(f"  Bootstrap nécessaire (état actuel : {current} pistes)...")
        _remove_all(yt, playlist_id, removable)
        time.sleep(3)

        for step in [1, 25, 50, target]:
            yt.add_playlist_items(playlist_id, video_ids[:step])
            logger.info(f"  Bootstrap add {step}...")
            time.sleep(6)
            if step < target:
                _remove_all(yt, playlist_id, _get_removable(yt, playlist_id))
                time.sleep(5)

        logger.info(f"  Bootstrap terminé → {target} pistes")


# ── Affichage ─────────────────────────────────────────────────────────────────

def show_playlist(yt: YTMusic, playlist_id: str):
    pl     = yt.get_playlist(playlist_id, limit=500)
    url    = f"https://music.youtube.com/playlist?list={playlist_id}"
    tracks = pl.get("tracks", [])
    print(f"\n{pl['title']}")
    print(f"{url}\n")
    for i, t in enumerate(tracks, 1):
        artists = ", ".join(a["name"] for a in (t.get("artists") or []))
        print(f"  {i:3d}. {t['title']} — {artists}")
    print(f"\n{len(tracks)} piste(s)")


# ── Point d'entrée ────────────────────────────────────────────────────────────

def run(show: bool = False):
    yt          = init_ytmusic()
    playlist_id = get_playlist_id(yt)

    if show:
        show_playlist(yt, playlist_id)
        return

    video_ids = build_24h_playlist(yt)
    update_playlist(yt, playlist_id, video_ids)

    logger.info("✅ Playlist 24h mise à jour !")
    logger.info(f"   https://music.youtube.com/playlist?list={playlist_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Botiran News — playlist 24h")
    parser.add_argument("--show", action="store_true", help="Affiche la playlist sans la mettre à jour")
    args = parser.parse_args()
    run(show=args.show)
