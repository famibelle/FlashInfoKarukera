#!/usr/bin/env python3
"""
Spotify Dynamic Radio Playlist Engine - FREE ACCOUNT VERSION
Generates radio recommendations based on time of day (no playlist modification)
Works with free Spotify accounts

For free accounts, the script:
- Generates track recommendations based on radio mode
- Exports as JSON for manual import
- Creates shareable Spotify links
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Set
import logging
import json
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
    Works with both free and premium accounts for reading.
    
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
        redirect_uri="https://famibelle.github.io/FlashInfoKarukera/spotify-callback.html",
        scope="playlist-read-public playlist-read-private"
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
                "uri": item["uri"],
                "external_urls": item.get("external_urls", {})
            })
        return tracks
    except Exception as e:
        logger.error(f"Error searching tracks for '{query}': {e}")
        return []


# ============================================================================
# PLAYLIST BUILDING LOGIC
# ============================================================================

def build_playlist(
    sp: spotipy.Spotify,
    mode: str,
    target_size: int = 20
) -> List[Dict]:
    """
    Build a curated playlist for the given radio mode.

    Args:
        sp: Spotify client instance
        mode: RadioMode constant
        target_size: Target number of tracks (default 20)

    Returns:
        List of track dictionaries with all info
    """
    config = RADIO_CONFIG[mode]
    queries = config["queries"]

    logger.info(f"Building playlist for mode: {mode} ({config['description']})")

    # Collect candidate tracks
    all_tracks = []
    artist_counts = {}

    for query in queries:
        logger.info(f"  Searching: {query}")
        tracks = search_tracks(sp, query, limit=30)

        for track in tracks:
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

    return selected_tracks


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def export_to_json(tracks: List[Dict], filename: str = None) -> str:
    """
    Export tracks to JSON file for easy sharing/import.

    Args:
        tracks: List of track dictionaries
        filename: Optional output filename

    Returns:
        Path to saved JSON file
    """
    if not filename:
        now = datetime.now()
        mode = get_radio_mode(now.hour)
        filename = f"radio_playlist_{mode}_{now.strftime('%Y-%m-%d_%H-%M')}.json"

    data = {
        "generated_at": datetime.now().isoformat(),
        "radio_mode": get_radio_mode(),
        "track_count": len(tracks),
        "tracks": tracks
    }

    filepath = os.path.join("playlists", filename)
    os.makedirs("playlists", exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Playlist exported to {filepath}")
    return filepath


def create_spotify_playlist_link(tracks: List[Dict]) -> str:
    """
    Create a Spotify URI list that can be added to a playlist manually.

    Args:
        tracks: List of track dictionaries

    Returns:
        Formatted string with Spotify URIs
    """
    uris = [track["uri"] for track in tracks]
    playlist_text = "SPOTIFY TRACKS:\n"
    playlist_text += "===============\n\n"

    for i, track in enumerate(tracks, 1):
        artists = ", ".join(track["artists"])
        playlist_text += f"{i}. {track['name']}\n"
        playlist_text += f"   Artist(s): {artists}\n"
        playlist_text += f"   Link: {track['external_urls'].get('spotify', 'N/A')}\n"
        playlist_text += f"   URI: {track['uri']}\n\n"

    return playlist_text


def export_playlist_text(tracks: List[Dict], filename: str = None) -> str:
    """
    Export playlist as readable text file.

    Args:
        tracks: List of track dictionaries
        filename: Optional output filename

    Returns:
        Path to saved text file
    """
    if not filename:
        now = datetime.now()
        mode = get_radio_mode(now.hour)
        filename = f"radio_playlist_{mode}_{now.strftime('%Y-%m-%d_%H-%M')}.txt"

    filepath = os.path.join("playlists", filename)
    os.makedirs("playlists", exist_ok=True)

    content = create_spotify_playlist_link(tracks)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info(f"Playlist text exported to {filepath}")
    return filepath


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

def run_playlist_engine():
    """
    Main orchestration function: detect hour → select mode → build → export.
    Works with FREE Spotify accounts.
    """
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
        tracks = build_playlist(sp, mode, target_size=20)

        if not tracks:
            logger.error("Failed to build playlist: no tracks found")
            sys.exit(1)

        # Export to JSON
        json_file = export_to_json(tracks)

        # Export to text
        txt_file = export_playlist_text(tracks)

        # Print results
        logger.info("\n" + "=" * 70)
        logger.info("✅ PLAYLIST GENERATED SUCCESSFULLY!")
        logger.info("=" * 70)
        logger.info(f"\n📁 Files saved:")
        logger.info(f"   • JSON: {json_file}")
        logger.info(f"   • Text: {txt_file}")
        logger.info(f"\n🎵 Tracks in playlist: {len(tracks)}")
        logger.info(f"\n📋 HOW TO IMPORT TO SPOTIFY:")
        logger.info(f"   1. Open {txt_file}")
        logger.info(f"   2. Copy the Spotify links")
        logger.info(f"   3. Create a playlist manually in Spotify")
        logger.info(f"   4. Add the tracks via the links")
        logger.info("\nOr use the JSON file with a third-party tool\n")

        # Print track preview
        logger.info("First 5 tracks:")
        for i, track in enumerate(tracks[:5], 1):
            artists = ", ".join(track["artists"])
            logger.info(f"   {i}. {track['name']} - {artists}")

    except Exception as e:
        logger.error(f"Fatal error in playlist engine: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_playlist_engine()
