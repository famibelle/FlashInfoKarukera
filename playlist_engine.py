#!/usr/bin/env python3
"""
Spotify Dynamic Radio Playlist Engine
Generates and updates a "Radio des Îles" playlist based on time of day
Using Spotify Web API with OAuth refresh token authentication
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Set
import logging
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# RADIO MODE CONFIGURATION
# ============================================================================

class RadioMode:
    """Enum for radio modes"""
    MORNING = "morning"
    MIDDAY = "midday"
    EVENING = "evening"


RADIO_CONFIG = {
    RadioMode.MORNING: {
        "time_range": "06:00-11:59",
        "genres": ["zouk", "classical", "calm", "ambient"],
        "queries": [
            "zouk doux",
            "musique classique caribéenne",
            "morning calm",
            "ambient guadeloupe",
            "classical caribbean"
        ],
        "energy_max": 0.6,
        "description": "🌅 Ambiance matinale - Zouk doux & musique classique caribéenne"
    },
    RadioMode.MIDDAY: {
        "time_range": "12:00-17:59",
        "genres": ["kompa", "zouk", "festive", "dance"],
        "queries": [
            "kompa",
            "zouk festif",
            "caribbean dance",
            "radio energy",
            "festival music"
        ],
        "energy_max": 0.85,
        "description": "☀️ Ambiance midi - Kompa & Zouk festif radio"
    },
    RadioMode.EVENING: {
        "time_range": "18:00-05:59",
        "genres": ["gwoka", "roots", "chill", "deep", "reggae"],
        "queries": [
            "gwoka",
            "léwoz",
            "roots caribbean",
            "chill evening",
            "deep relaxation"
        ],
        "energy_max": 0.65,
        "description": "🌙 Ambiance soirée - Gwoka, Léwoz & vibes relaxantes"
    }
}


# ============================================================================
# SPOTIFY AUTHENTICATION & INITIALIZATION
# ============================================================================

def init_spotify_client():
    """
    Initialize Spotify client with OAuth authentication.
    Requires environment variables:
    - SPOTIPY_CLIENT_ID
    - SPOTIPY_CLIENT_SECRET
    - SPOTIPY_REFRESH_TOKEN
    """
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    refresh_token = os.getenv("SPOTIPY_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        logger.error("Missing required Spotify credentials in environment variables")
        sys.exit(1)

    # Create OAuth manager
    oauth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://127.0.0.1:8888/callback",
        scope="playlist-modify-public playlist-modify-private"
    )

    # Get access token using refresh token
    token_info = oauth.refresh_access_token(refresh_token)
    access_token = token_info["access_token"]

    return spotipy.Spotify(auth=access_token)


# ============================================================================
# RADIO MODE DETECTION
# ============================================================================

def get_radio_mode(hour: int = None) -> str:
    """
    Determine radio mode based on current or provided hour.

    Args:
        hour: Optional hour (0-23). If None, uses current hour.

    Returns:
        RadioMode constant (MORNING, MIDDAY, or EVENING)
    """
    if hour is None:
        hour = datetime.now().hour

    if 6 <= hour < 12:
        return RadioMode.MORNING
    elif 12 <= hour < 18:
        return RadioMode.MIDDAY
    else:
        return RadioMode.EVENING


# ============================================================================
# SPOTIFY SEARCH & TRACK RETRIEVAL
# ============================================================================

def search_tracks(sp: spotipy.Spotify, query: str, limit: int = 20) -> List[Dict]:
    """
    Search for tracks on Spotify.

    Args:
        sp: Spotify client instance
        query: Search query string
        limit: Maximum number of results (max 50)

    Returns:
        List of track dictionaries with id, name, artist, etc.
    """
    try:
        results = sp.search(q=query, type="track", limit=min(limit, 50))
        tracks = []
        for item in results.get("tracks", {}).get("items", []):
            tracks.append({
                "id": item["id"],
                "name": item["name"],
                "artists": [artist["name"] for artist in item["artists"]],
                "duration_ms": item["duration_ms"],
                "popularity": item["popularity"],
                "uri": item["uri"]
            })
        return tracks
    except Exception as e:
        logger.error(f"Error searching tracks for '{query}': {e}")
        return []


def get_recent_used_tracks(playlist_id: str, sp: spotipy.Spotify, limit: int = 50) -> Set[str]:
    """
    Get recently used track IDs from the playlist to avoid repeats.

    Args:
        playlist_id: Spotify playlist ID
        sp: Spotify client instance
        limit: Number of recent tracks to consider

    Returns:
        Set of recently used track IDs
    """
    try:
        results = sp.playlist_tracks(playlist_id, limit=limit)
        recent_ids = {item["track"]["id"] for item in results.get("items", []) if item["track"]}
        return recent_ids
    except Exception as e:
        logger.error(f"Error getting recent playlist tracks: {e}")
        return set()


# ============================================================================
# PLAYLIST BUILDING LOGIC
# ============================================================================

def build_playlist(
    sp: spotipy.Spotify,
    mode: str,
    target_size: int = 20,
    playlist_id: str = None
) -> List[str]:
    """
    Build a curated playlist for the given radio mode.

    Args:
        sp: Spotify client instance
        mode: RadioMode constant
        target_size: Target number of tracks (default 20)
        playlist_id: Playlist ID to avoid recent repeats

    Returns:
        List of track URIs for the playlist
    """
    config = RADIO_CONFIG[mode]
    queries = config["queries"]
    energy_max = config["energy_max"]

    logger.info(f"Building playlist for mode: {mode} ({config['description']})")

    # Get recently used tracks to avoid repetition
    recent_ids = set()
    if playlist_id:
        recent_ids = get_recent_used_tracks(playlist_id, sp, limit=50)

    # Collect candidate tracks
    all_tracks = []
    artist_counts = {}

    for query in queries:
        logger.info(f"  Searching: {query}")
        tracks = search_tracks(sp, query, limit=30)

        for track in tracks:
            track_id = track["id"]

            # Skip if recently used
            if track_id in recent_ids:
                continue

            # Limit tracks per artist (max 2 per artist)
            main_artist = track["artists"][0] if track["artists"] else "Unknown"
            artist_counts[main_artist] = artist_counts.get(main_artist, 0) + 1
            if artist_counts[main_artist] > 2:
                continue

            # Add to candidates
            all_tracks.append(track)

    # Sort by popularity to prioritize well-known tracks
    all_tracks.sort(key=lambda x: x["popularity"], reverse=True)

    # Select top tracks (remove duplicates by ID)
    selected_tracks = []
    used_ids = set()

    for track in all_tracks:
        if len(selected_tracks) >= target_size:
            break
        if track["id"] not in used_ids:
            selected_tracks.append(track)
            used_ids.add(track["id"])

    logger.info(f"Selected {len(selected_tracks)} tracks for playlist")

    # Return track URIs (ready for Spotify API)
    track_uris = [track["uri"] for track in selected_tracks]
    return track_uris


# ============================================================================
# PLAYLIST UPDATE
# ============================================================================

def update_playlist(sp: spotipy.Spotify, playlist_id: str, track_uris: List[str]):
    """
    Replace playlist content with new tracks.

    Args:
        sp: Spotify client instance
        playlist_id: Spotify playlist ID to update
        track_uris: List of track URIs to add to playlist
    """
    if not track_uris:
        logger.warning("No tracks to add to playlist")
        return

    try:
        # Clear existing tracks (in batches of 100)
        logger.info(f"Clearing playlist {playlist_id}...")
        while True:
            results = sp.playlist_tracks(playlist_id, limit=100)
            items = results.get("items", [])
            if not items:
                break
            track_ids = [item["track"]["id"] for item in items if item["track"]]
            if track_ids:
                sp.playlist_remove_all_occurrences_of_items(playlist_id, track_ids)

        # Add new tracks (in batches of 100)
        logger.info(f"Adding {len(track_uris)} tracks to playlist...")
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i + 100]
            sp.playlist_add_items(playlist_id, batch)
            logger.info(f"  Added {min(100, len(track_uris) - i)} tracks")

        logger.info("Playlist updated successfully!")

    except Exception as e:
        logger.error(f"Error updating playlist: {e}")
        sys.exit(1)


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

def run_playlist_engine(playlist_id: str = None):
    """
    Main orchestration function: detect hour → select mode → build → update.

    Args:
        playlist_id: Spotify playlist ID (from env if not provided)
    """
    playlist_id = playlist_id or os.getenv("SPOTIFY_PLAYLIST_ID")

    if not playlist_id:
        logger.error("SPOTIFY_PLAYLIST_ID not found in environment variables")
        sys.exit(1)

    try:
        # Initialize Spotify client
        logger.info("Initializing Spotify client...")
        sp = init_spotify_client()

        # Get current time and determine mode
        now = datetime.now()
        hour = now.hour
        mode = get_radio_mode(hour)
        config = RADIO_CONFIG[mode]

        logger.info(f"Current time: {now.strftime('%H:%M:%S')}")
        logger.info(f"Radio mode: {mode} ({config['description']})")

        # Build playlist
        track_uris = build_playlist(sp, mode, target_size=20, playlist_id=playlist_id)

        if not track_uris:
            logger.error("Failed to build playlist: no tracks found")
            sys.exit(1)

        # Update Spotify playlist
        update_playlist(sp, playlist_id, track_uris)

        logger.info("✅ Playlist updated successfully!")

    except Exception as e:
        logger.error(f"Fatal error in playlist engine: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_playlist_engine()
