#!/usr/bin/env python3
"""
YouTube Music Dynamic Radio Playlist Engine
Generates and updates a "Radio des Îles" playlist based on time of day.
Uses ytmusicapi — auth via browser.json (cookie-based, no API key needed).
"""

import os
import sys
import json
import random
import logging
from datetime import datetime
from typing import List, Dict, Set
from dotenv import load_dotenv
from ytmusicapi import YTMusic
from caribbean_db import get_tracks_by_mode
from youtube_uploader import (
    get_or_upload_episode, get_or_upload_horoscope,
    get_or_create_youtube_playlist, update_youtube_playlist, get_youtube_client,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BROWSER_JSON = os.getenv("YTMUSIC_BROWSER_JSON_PATH", "browser.json")


# ============================================================================
# RADIO MODE CONFIGURATION
# ============================================================================

class RadioMode:
    NIGHT   = "night"
    MORNING = "morning"
    MIDDAY  = "midday"
    EVENING = "evening"


RADIO_CONFIG = {
    RadioMode.NIGHT: {
        "time_range": "00:00-05:59",
        "description": "🌙 Ambiance nuit - Zouk rétro, Gwoka & Bouillon",
        "fallback_artists": ["Edith Lefel", "Patrick Saint-Eloi", "Gérald Thalius", "Ti Paris", "Dédé Saint-Prix"],
        "has_flash": False,
    },
    RadioMode.MORNING: {
        "time_range": "06:00-11:59",
        "description": "🌅 Ambiance matinale - Zouk & Gwoka",
        "fallback_artists": ["Kassav", "Zouk Machine", "Edith Lefel", "Tanya Saint-Val", "Gérald Thalius", "Valérie Dhorasoo"],
        "has_flash": True,
    },
    RadioMode.MIDDAY: {
        "time_range": "12:00-17:59",
        "description": "☀️ Ambiance midi - Kompa & Zouk festif",
        "fallback_artists": ["T-Vice", "Tabou Combo", "Carimi", "Harmonik", "Kassav", "Zouk Machine"],
        "has_flash": True,
    },
    RadioMode.EVENING: {
        "time_range": "18:00-23:59",
        "description": "🌆 Ambiance soirée - Gwoka, Zouk & Kompa",
        "fallback_artists": ["Gérald Thalius", "Valérie Dhorasoo", "Kassav", "Edith Lefel", "T-Vice", "Nu-Look"],
        "has_flash": True,
    },
}


# ============================================================================
# RADIO MODE DETECTION
# ============================================================================

def get_radio_mode(hour: int = None) -> str:
    if hour is None:
        hour = datetime.now().hour
    if 0 <= hour < 6:
        return RadioMode.NIGHT
    elif 6 <= hour < 12:
        return RadioMode.MORNING
    elif 12 <= hour < 18:
        return RadioMode.MIDDAY
    else:
        return RadioMode.EVENING


# ============================================================================
# YOUTUBE MUSIC AUTH
# ============================================================================

def init_ytmusic() -> YTMusic:
    """Initialize YTMusic via browser.json (cookie-based auth)."""
    if not os.path.exists(BROWSER_JSON):
        logger.error(f"Auth file not found: {BROWSER_JSON}")
        logger.error("Run: python3 ytmusic_setup.py")
        sys.exit(1)
    return YTMusic(BROWSER_JSON)


# ============================================================================
# SEARCH HELPERS
# ============================================================================

def _artist_matches(search_artist: str, result_artist: str) -> bool:
    """Loose artist match — handles 'Bob Marley' vs 'Bob Marley & The Wailers'."""
    a = search_artist.lower()
    b = result_artist.lower()
    return a in b or b in a or any(w in b for w in a.split() if len(w) > 3)


def _result_artists(result: dict) -> str:
    """Extract a single artist string from a ytmusicapi result."""
    artists = result.get("artists") or []
    return ", ".join(a["name"] for a in artists if "name" in a)


def search_track(yt: YTMusic, name: str, artist: str) -> str | None:
    """
    Search YouTube Music for a specific track.
    Returns the videoId if a confident match is found, else None.
    """
    for query in [f"{name} {artist}", name]:
        try:
            results = yt.search(query, filter="songs", limit=10)
            for r in results:
                result_artist = _result_artists(r)
                if _artist_matches(artist, result_artist):
                    return r["videoId"]
        except Exception as e:
            logger.warning(f"  Search error for '{name}': {e}")
            break
    return None


def search_artist_top_tracks(yt: YTMusic, artist: str, limit: int = 5) -> List[str]:
    """Search top tracks for an artist. Returns a list of videoIds."""
    try:
        results = yt.search(artist, filter="songs", limit=limit * 2)
        ids = []
        for r in results:
            if len(ids) >= limit:
                break
            if _artist_matches(artist, _result_artists(r)):
                ids.append(r["videoId"])
        return ids
    except Exception as e:
        logger.warning(f"  Artist search error for '{artist}': {e}")
        return []


# ============================================================================
# PLAYLIST BUILDING
# ============================================================================

def build_playlist(yt: YTMusic, mode: str, target_size: int = 20) -> List[str]:
    """
    Build a playlist for the given mode.
    1. Search each curated DB track on YouTube Music
    2. Fill remaining slots with artist-based fallback searches
    Returns a list of YouTube videoIds.
    """
    config = RADIO_CONFIG[mode]
    logger.info(f"Building playlist for mode: {mode} ({config['description']})")

    db_tracks = get_tracks_by_mode(mode)
    random.shuffle(db_tracks)

    video_ids: List[str] = []
    used_ids: Set[str] = set()

    # Step 1 — curated DB tracks
    for db_track in db_tracks:
        if len(video_ids) >= target_size:
            break
        name   = db_track["name"]
        artist = db_track["artists"][0] if db_track["artists"] else ""
        vid = search_track(yt, name, artist)
        if vid and vid not in used_ids:
            video_ids.append(vid)
            used_ids.add(vid)
            logger.info(f"  ✓ {name} — {artist}")
        else:
            logger.warning(f"  ✗ Not found: {name} — {artist}")

    logger.info(f"Curated tracks: {len(video_ids)}/{len(db_tracks)}")

    # Step 2 — fallback: fill via artist search
    if len(video_ids) < target_size:
        logger.info(f"Filling {target_size - len(video_ids)} slots via artist search...")
        for artist in config.get("fallback_artists", []):
            if len(video_ids) >= target_size:
                break
            for vid in search_artist_top_tracks(yt, artist, limit=5):
                if len(video_ids) >= target_size:
                    break
                if vid not in used_ids:
                    video_ids.append(vid)
                    used_ids.add(vid)
                    logger.info(f"  + fallback: {artist}")

    logger.info(f"Playlist built: {len(video_ids)} tracks")
    return video_ids


PLAYLIST_TITLE = "Botiran News: La radio de la diaspora Guadeloupéenne au Luxembourg"


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

def run_playlist_engine():
    """
    Détecte le mode horaire → recherche YouTube Music → met à jour la playlist YouTube.
    Recherche : ytmusicapi (browser.json)
    Playlist   : YouTube Data API (youtube_token.json) — lisible par tous
    """
    yt = init_ytmusic()

    now    = datetime.now()
    mode   = get_radio_mode(now.hour)
    config = RADIO_CONFIG[mode]

    logger.info(f"Current time: {now.strftime('%H:%M:%S')}")
    logger.info(f"Radio mode: {mode} ({config['description']})")

    video_ids = build_playlist(yt, mode, target_size=20)

    if not video_ids:
        logger.error("No tracks found")
        sys.exit(1)

    # Prépend Flash Info + Horoscope (sauf mode nuit)
    prepend = []
    if config.get("has_flash"):
        for label, fn in [("Flash Info", get_or_upload_episode), ("Horoscope", get_or_upload_horoscope)]:
            try:
                vid = fn(mode)
                if vid:
                    prepend.append(vid)
                    logger.info(f"{label} prepended: https://youtu.be/{vid}")
            except Exception as e:
                logger.warning(f"{label} upload skipped: {e}")

    video_ids = prepend + video_ids

    playlist_id = get_or_create_youtube_playlist(PLAYLIST_TITLE)
    logger.info(f"Mise à jour playlist {playlist_id} ({len(video_ids)} items)...")
    update_youtube_playlist(playlist_id, video_ids)

    logger.info("✅ Playlist updated successfully!")
    logger.info(f"   https://www.youtube.com/playlist?list={playlist_id}")


def show_playlist(playlist_id: str = None):
    """Affiche le contenu de la playlist YouTube et son URL."""
    from pathlib import Path as _Path
    id_file = _Path("playlists/youtube_playlist_id.txt")
    playlist_id = playlist_id or os.getenv("YOUTUBE_PLAYLIST_ID") or (
        id_file.read_text().strip() if id_file.exists() else None
    )
    if not playlist_id:
        print("YOUTUBE_PLAYLIST_ID non défini")
        sys.exit(1)

    yt = get_youtube_client()

    pl_resp = yt.playlists().list(part="snippet", id=playlist_id).execute()
    title = pl_resp["items"][0]["snippet"]["title"] if pl_resp.get("items") else playlist_id

    items, next_page = [], None
    while True:
        resp = yt.playlistItems().list(
            part="snippet", playlistId=playlist_id,
            maxResults=50, pageToken=next_page
        ).execute()
        items.extend(resp.get("items", []))
        next_page = resp.get("nextPageToken")
        if not next_page:
            break

    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    print(f"\n{title}")
    print(f"{url}\n")
    for i, item in enumerate(items, 1):
        s = item.get("snippet", {})
        print(f"  {i:2d}. {s.get('title', '—')} — {s.get('videoOwnerChannelTitle', '')}")
    print(f"\n{len(items)} piste(s)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Botiran News — moteur de playlist")
    parser.add_argument("--show", action="store_true", help="Affiche la playlist sans la mettre à jour")
    args = parser.parse_args()

    if args.show:
        show_playlist()
    else:
        run_playlist_engine()
