#!/usr/bin/env python3
"""
Spotify Radio Playlist Engine — Free Account Version

Stratégie :
  1. Construit la playlist à partir de la DB caribéenne (noms + artistes)
  2. Cherche les vrais URIs via l'API Spotify Search
  3. Met à jour la playlist Spotify si l'API le permet
  4. Sinon (app owner sans Premium → 403), exporte en JSON + texte + liens Spotify

Variables d'environnement requises :
  SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REFRESH_TOKEN
  SPOTIFY_PLAYLIST_ID  (optionnel — si absent, export seulement)
"""

import os
import sys
import json
import random
import logging
import urllib.parse
from datetime import datetime
from typing import List, Dict, Set
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from caribbean_db import get_tracks_by_mode

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# RADIO MODE CONFIGURATION
# ============================================================================

class RadioMode:
    MORNING = "morning"
    MIDDAY  = "midday"
    EVENING = "evening"


RADIO_CONFIG = {
    RadioMode.MORNING: {
        "time_range": "06:00-11:59",
        "description": "🌅 Ambiance matinale - Zouk doux & musique classique caribéenne",
    },
    RadioMode.MIDDAY: {
        "time_range": "12:00-17:59",
        "description": "☀️ Ambiance midi - Kompa & Zouk festif radio",
    },
    RadioMode.EVENING: {
        "time_range": "18:00-05:59",
        "description": "🌙 Ambiance soirée - Gwoka, Léwoz & vibes relaxantes",
    },
}


def get_radio_mode(hour: int = None) -> str:
    if hour is None:
        hour = datetime.now().hour
    if 6 <= hour < 12:
        return RadioMode.MORNING
    elif 12 <= hour < 18:
        return RadioMode.MIDDAY
    else:
        return RadioMode.EVENING


# ============================================================================
# SPOTIFY AUTH
# ============================================================================

def init_spotify() -> spotipy.Spotify:
    client_id     = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    refresh_token = os.getenv("SPOTIPY_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        logger.error("Variables manquantes : SPOTIPY_CLIENT_ID / CLIENT_SECRET / REFRESH_TOKEN")
        sys.exit(1)

    oauth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://127.0.0.1:8888/callback",
        scope="playlist-modify-public playlist-modify-private",
    )
    token_info = oauth.refresh_access_token(refresh_token)
    return spotipy.Spotify(auth=token_info["access_token"])


# ============================================================================
# SEARCH
# ============================================================================

def search_track(sp: spotipy.Spotify, name: str, artist: str) -> Dict | None:
    """Cherche un morceau sur Spotify. Retourne None si bloqué ou introuvable."""
    query = f'track:"{name}" artist:"{artist}"'
    try:
        results = sp.search(q=query, type="track", limit=1)
        items = results.get("tracks", {}).get("items", [])
        if items:
            item = items[0]
            return {
                "name": item["name"],
                "artists": [a["name"] for a in item["artists"]],
                "uri": item["uri"],
                "url": item["external_urls"].get("spotify", ""),
                "id": item["id"],
            }
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 403:
            raise  # remonter le 403 pour déclencher le fallback
        logger.warning(f"Erreur recherche '{name}': {e}")
    return None


# ============================================================================
# PLAYLIST BUILDING
# ============================================================================

def build_playlist(sp: spotipy.Spotify, mode: str, target_size: int = 20) -> List[Dict]:
    """
    Résout les morceaux de la DB via l'API Search.
    Retourne une liste de dicts avec uri, url, name, artists.
    Lève SpotifyException (403) si l'API est bloquée.
    """
    config = RADIO_CONFIG[mode]
    logger.info(f"Construction playlist — mode : {mode} ({config['description']})")

    db_tracks = get_tracks_by_mode(mode)
    random.shuffle(db_tracks)

    resolved: List[Dict] = []
    used_ids: Set[str] = set()

    for db_track in db_tracks:
        if len(resolved) >= target_size:
            break
        name   = db_track["name"]
        artist = db_track["artists"][0] if db_track["artists"] else ""
        track  = search_track(sp, name, artist)
        if track and track["id"] not in used_ids:
            resolved.append(track)
            used_ids.add(track["id"])
            logger.info(f"  ✓ {track['name']} — {', '.join(track['artists'])}")
        else:
            logger.warning(f"  ✗ Non trouvé : {name} — {artist}")

    logger.info(f"Playlist : {len(resolved)}/{len(db_tracks)} morceaux résolus")
    return resolved


# ============================================================================
# SPOTIFY PLAYLIST UPDATE
# ============================================================================

def update_spotify_playlist(sp: spotipy.Spotify, playlist_id: str, tracks: List[Dict]):
    """Met à jour la playlist Spotify avec les URIs résolus."""
    uris = [t["uri"] for t in tracks]

    logger.info(f"Vidage de la playlist {playlist_id}...")
    while True:
        items = sp.playlist_tracks(playlist_id, limit=100).get("items", [])
        if not items:
            break
        ids = [i["track"]["id"] for i in items if i["track"]]
        if ids:
            sp.playlist_remove_all_occurrences_of_items(playlist_id, ids)

    for i in range(0, len(uris), 100):
        sp.playlist_add_items(playlist_id, uris[i:i + 100])

    logger.info(f"✅ {len(uris)} morceaux ajoutés à la playlist Spotify")


# ============================================================================
# FALLBACK EXPORT (quand l'API est bloquée)
# ============================================================================

def export_fallback(mode: str, tracks: List[Dict]):
    """
    Exporte la playlist en JSON + texte avec liens Spotify ouverts.
    Utilisé quand l'API Spotify est bloquée (app owner sans Premium).
    """
    os.makedirs("playlists", exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    # JSON
    json_path = f"playlists/spotify_{mode}_{stamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "mode": mode,
            "description": RADIO_CONFIG[mode]["description"],
            "tracks": tracks,
        }, f, indent=2, ensure_ascii=False)

    # Texte lisible
    txt_path = f"playlists/spotify_{mode}_{stamp}.txt"
    lines = [
        f"Radio des Îles — {RADIO_CONFIG[mode]['description']}",
        f"Générée le {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "",
    ]
    for i, t in enumerate(tracks, 1):
        artists = ", ".join(t["artists"])
        lines.append(f"{i:2d}. {t['name']} — {artists}")
        if t.get("url"):
            lines.append(f"    {t['url']}")
    lines += [
        "",
        "— Pour importer : copier les liens dans Spotify ou utiliser le JSON avec",
        "  un outil tiers (ex. https://www.spotlistr.com/)",
    ]
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Export JSON  : {json_path}")
    logger.info(f"Export texte : {txt_path}")
    return json_path, txt_path


# ============================================================================
# MAIN
# ============================================================================

def run_playlist_engine(playlist_id: str = None):
    playlist_id = playlist_id or os.getenv("SPOTIFY_PLAYLIST_ID")

    sp   = init_spotify()
    mode = get_radio_mode()
    logger.info(f"Heure : {datetime.now().strftime('%H:%M')} — Mode : {mode}")

    tracks = None
    try:
        tracks = build_playlist(sp, mode, target_size=20)

        if not tracks:
            logger.error("Aucun morceau trouvé")
            sys.exit(1)

        if playlist_id:
            update_spotify_playlist(sp, playlist_id, tracks)
        else:
            logger.info("SPOTIFY_PLAYLIST_ID absent — export uniquement")
            export_fallback(mode, tracks)

    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 403:
            logger.warning("API Spotify bloquée (403 — Premium requis pour le propriétaire de l'app)")
            logger.warning("Basculement sur l'export local...")
            if tracks is None:
                # 403 avant toute résolution — on exporte la DB brute avec liens de recherche
                tracks = [
                    {
                        "name": t["name"],
                        "artists": t["artists"],
                        "uri": "",
                        "url": "https://open.spotify.com/search/" + urllib.parse.quote(
                            f"{t['name']} {t['artists'][0]}"
                        ),
                    }
                    for t in get_tracks_by_mode(mode)
                ]
            export_fallback(mode, tracks)
        else:
            raise


if __name__ == "__main__":
    run_playlist_engine()
