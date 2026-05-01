#!/usr/bin/env python3
"""
Playlist 24h — Botiran News Radio
Construit une playlist ~24h avec flash info et horoscopes positionnés à 6h, 12h, 18h.
Le pool musical est mis en cache une fois par jour pour éviter 200+ recherches à chaque run.
"""

import os
import sys
import json
import random
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from ytmusicapi import YTMusic
from caribbean_db import CARIBBEAN_TRACKS
from youtube_uploader import get_or_upload_episode, get_or_upload_horoscope

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BROWSER_JSON     = os.getenv("YTMUSIC_BROWSER_JSON_PATH", "browser.json")
POOL_CACHE_FILE  = Path("playlists/music_pool_cache.json")
PLAYLIST_ID_FILE = Path("playlists/playlist_24h_id.txt")

AVG_DURATION  = 210        # secondes — fallback si duration_seconds absent
BLOCK_SECONDS = 6 * 3600   # 6h par bloc

# Genres privilégiés par bloc horaire pour varier l'ambiance au fil de la journée
BLOCK_GENRES = {
    "night":      ["gwoka", "bouillon", "zouk_retro"],
    "morning":    ["zouk", "zouk_retro", "gwoka", "chatta"],
    "afternoon":  ["kompa", "zouk", "chatta"],
    "evening":    ["gwoka", "bouillon", "zouk_retro", "kompa"],
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
    Résultat : [{"videoId": ..., "duration": ..., "genre": ...}]
    Cache valide pour la journée (clé = date du jour).
    """
    today = datetime.now().strftime("%Y-%m-%d")

    if POOL_CACHE_FILE.exists():
        cached = json.loads(POOL_CACHE_FILE.read_text(encoding="utf-8"))
        if cached.get("date") == today:
            logger.info(f"Pool musical depuis cache ({len(cached['tracks'])} pistes, {today})")
            return cached["tracks"]

    logger.info("Résolution du pool musical (200+ recherches YTMusic)...")
    pool = []
    seen = set()

    for genre, tracks in CARIBBEAN_TRACKS.items():
        for track in tracks:
            name   = track["name"]
            artist = track["artists"][0] if track["artists"] else ""
            vid, dur = _search(yt, name, artist)
            if vid and vid not in seen:
                pool.append({"videoId": vid, "duration": dur, "genre": genre})
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

def fill_block(pool: list, genres: list, target_seconds: int) -> List[str]:
    """
    Remplit un bloc temporel avec des pistes du pool filtrées par genre.
    Répète le sous-pool (shufflé) jusqu'à atteindre target_seconds.
    """
    sub = [t for t in pool if t["genre"] in genres]
    if not sub:
        sub = pool  # fallback sur le pool complet

    result = []
    total  = 0
    while total < target_seconds:
        random.shuffle(sub)
        for track in sub:
            if total >= target_seconds:
                break
            result.append(track["videoId"])
            total += track["duration"]

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

def build_24h_playlist(yt: YTMusic) -> List[str]:
    """
    Structure :
      00:00–06:00  musique nuit        (~103 pistes)
      06:00        Flash Info matin + Horoscope matin
      06:xx–12:00  musique matinée     (~103 pistes)
      12:00        Flash Info midi
      12:xx–18:00  musique après-midi  (~103 pistes)
      18:00        Flash Info soir + Horoscope soir
      18:xx–24:00  musique soirée      (~103 pistes)
    """
    pool = resolve_music_pool(yt)
    if not pool:
        logger.error("Pool vide — abandon")
        sys.exit(1)

    playlist = []

    logger.info("Bloc 00:00–06:00 (nuit)...")
    playlist += fill_block(pool, BLOCK_GENRES["night"], BLOCK_SECONDS)

    logger.info("Insertion 06:00 — Flash Info matin + Horoscope matin")
    _add_special(playlist, "Flash Info matin",  lambda: get_or_upload_episode("morning"))
    _add_special(playlist, "Horoscope matin",   lambda: get_or_upload_horoscope("morning"))

    logger.info("Bloc 06:00–12:00 (matinée)...")
    playlist += fill_block(pool, BLOCK_GENRES["morning"], BLOCK_SECONDS)

    logger.info("Insertion 12:00 — Flash Info midi")
    _add_special(playlist, "Flash Info midi",   lambda: get_or_upload_episode("midday"))

    logger.info("Bloc 12:00–18:00 (après-midi)...")
    playlist += fill_block(pool, BLOCK_GENRES["afternoon"], BLOCK_SECONDS)

    logger.info("Insertion 18:00 — Flash Info soir + Horoscope soir")
    _add_special(playlist, "Flash Info soir",   lambda: get_or_upload_episode("evening"))
    _add_special(playlist, "Horoscope soir",    lambda: get_or_upload_horoscope("evening"))

    logger.info("Bloc 18:00–24:00 (soirée)...")
    playlist += fill_block(pool, BLOCK_GENRES["evening"], BLOCK_SECONDS)

    music_count = len(playlist) - 5  # 3 flash + 2 horoscopes
    logger.info(f"Playlist 24h : {len(playlist)} items ({music_count} pistes musicales)")
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


def update_playlist(yt: YTMusic, playlist_id: str, video_ids: List[str]):
    """Vide la playlist et la remplit par batches de 100."""
    logger.info(f"Mise à jour playlist {playlist_id} ({len(video_ids)} items)...")

    try:
        existing = yt.get_playlist(playlist_id, limit=500).get("tracks", [])
        removable = [t for t in existing if t.get("setVideoId")]
        if removable:
            yt.remove_playlist_items(playlist_id, removable)
            logger.info(f"  Supprimé {len(removable)} pistes existantes")
    except Exception as e:
        logger.warning(f"  Impossible de vider la playlist : {e}")

    for i in range(0, len(video_ids), 100):
        batch = video_ids[i:i + 100]
        yt.add_playlist_items(playlist_id, batch)
        logger.info(f"  Ajouté {min(i + 100, len(video_ids))}/{len(video_ids)}")


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
