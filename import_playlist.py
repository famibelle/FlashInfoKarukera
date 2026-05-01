#!/usr/bin/env python3
"""
Spotify Playlist Importer
Adds tracks from the generated playlist to a Spotify playlist
Uses the Spotify Web API with OAuth authentication
"""

import os
import sys
from typing import List, Dict, Optional
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
# SPOTIFY AUTHENTICATION
# ============================================================================

def init_spotify_client():
    """
    Initialize Spotify client with OAuth authentication for the logged-in user.
    This uses the user's own credentials, not the app credentials.
    """
    # For user-based auth, we use SpotifyOAuth with proper scopes
    oauth = SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri="https://famibelle.github.io/FlashInfoKarukera/spotify-callback.html",
        scope="playlist-modify-public playlist-modify-private"
    )

    # This will open browser if needed or use cached token
    token_info = oauth.get_cached_token()

    if not token_info:
        logger.info("Opening Spotify authorization page...")
        logger.info("Please authorize the application to access your Spotify account")
        auth_url = oauth.get_authorize_url()
        logger.info(f"URL: {auth_url}")

        # For automation, we need the user to complete the flow
        sys.exit(1)

    return spotipy.Spotify(auth=token_info["access_token"])


def init_spotify_client_with_refresh(refresh_token: str):
    """
    Initialize Spotify client using a refresh token.
    This bypasses the browser authentication flow.
    """
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

    if not all([client_id, client_secret, refresh_token]):
        logger.error("Missing credentials")
        sys.exit(1)

    oauth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="https://famibelle.github.io/FlashInfoKarukera/spotify-callback.html",
        scope="playlist-modify-public playlist-modify-private"
    )

    try:
        token_info = oauth.refresh_access_token(refresh_token)
        access_token = token_info["access_token"]
        return spotipy.Spotify(auth=access_token)
    except Exception as e:
        logger.error(f"Failed to authenticate with refresh token: {e}")
        sys.exit(1)


# ============================================================================
# PLAYLIST MANAGEMENT
# ============================================================================

def get_user_playlists(sp: spotipy.Spotify) -> List[Dict]:
    """
    Get all playlists owned by the current user.

    Returns:
        List of playlist dictionaries with id, name, etc.
    """
    try:
        results = sp.current_user_playlists(limit=50)
        playlists = []
        for item in results.get("items", []):
            playlists.append({
                "id": item["id"],
                "name": item["name"],
                "owner": item["owner"]["display_name"],
                "public": item["public"],
                "tracks_count": item["tracks"]["total"]
            })
        return playlists
    except Exception as e:
        logger.error(f"Error fetching playlists: {e}")
        return []


def search_and_get_track_uri(sp: spotipy.Spotify, track_name: str, artist_name: str) -> Optional[str]:
    """
    Search for a track on Spotify and return its URI.

    Args:
        sp: Spotify client
        track_name: Name of the track
        artist_name: Name of the artist

    Returns:
        Spotify track URI if found, None otherwise
    """
    try:
        query = f"track:{track_name} artist:{artist_name}"
        results = sp.search(q=query, type="track", limit=1)

        items = results.get("tracks", {}).get("items", [])
        if items:
            return items[0]["uri"]

        logger.warning(f"Track not found: {track_name} - {artist_name}")
        return None

    except Exception as e:
        logger.error(f"Error searching for track '{track_name}': {e}")
        return None


def add_tracks_to_playlist(sp: spotipy.Spotify, playlist_id: str, track_uris: List[str]):
    """
    Add tracks to a Spotify playlist.

    Args:
        sp: Spotify client
        playlist_id: ID of the target playlist
        track_uris: List of track URIs to add
    """
    if not track_uris:
        logger.warning("No tracks to add")
        return

    try:
        # Add in batches of 100 (Spotify API limit)
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i + 100]
            sp.playlist_add_items(playlist_id, batch)
            logger.info(f"Added {len(batch)} tracks to playlist")

        logger.info(f"✅ Successfully added {len(track_uris)} tracks to playlist")

    except Exception as e:
        logger.error(f"Error adding tracks to playlist: {e}")
        sys.exit(1)


# ============================================================================
# FILE LOADING
# ============================================================================

def load_playlist_from_json(filepath: str) -> List[Dict]:
    """
    Load playlist from JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        List of track dictionaries
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("tracks", [])
    except Exception as e:
        logger.error(f"Error loading JSON file: {e}")
        sys.exit(1)


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

def import_playlist_to_spotify(json_file: Optional[str] = None, playlist_name: Optional[str] = None):
    """
    Main function: Load playlist from JSON and import to Spotify.

    Args:
        json_file: Path to the JSON playlist file (if None, finds latest)
        playlist_name: Name of the Spotify playlist to import to
    """
    try:
        logger.info("=" * 70)
        logger.info("🎵 SPOTIFY PLAYLIST IMPORTER")
        logger.info("=" * 70)

        # Find JSON file if not provided
        if not json_file:
            import glob
            json_files = sorted(glob.glob("playlists/radio_playlist_*.json"), reverse=True)
            if not json_files:
                logger.error("No JSON playlist files found in playlists/ directory")
                logger.info("Run 'python playlist_engine_static.py' first")
                sys.exit(1)
            json_file = json_files[0]
            logger.info(f"Found latest playlist: {json_file}")

        # Load tracks from JSON
        logger.info(f"\nLoading tracks from: {json_file}")
        tracks = load_playlist_from_json(json_file)
        logger.info(f"Loaded {len(tracks)} tracks")

        # Get Spotify client
        logger.info("\nAuthenticating with Spotify...")
        refresh_token = os.getenv("SPOTIPY_REFRESH_TOKEN")

        if refresh_token:
            sp = init_spotify_client_with_refresh(refresh_token)
            logger.info("✅ Authenticated with refresh token")
        else:
            logger.error("SPOTIPY_REFRESH_TOKEN not found in .env")
            sys.exit(1)

        # Get current user
        try:
            user_info = sp.current_user()
            username = user_info.get("display_name", user_info.get("id", "Unknown"))
            logger.info(f"Logged in as: {username}")
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            logger.error("This usually means your account is not Premium or there's an auth issue")
            sys.exit(1)

        # Get or create target playlist
        if not playlist_name:
            playlist_name = "Radio Guadeloupe Luxembourg"

        logger.info(f"\nLooking for playlist: '{playlist_name}'")
        user_playlists = get_user_playlists(sp)

        target_playlist = None
        for playlist in user_playlists:
            if playlist["name"].lower() == playlist_name.lower():
                target_playlist = playlist
                break

        if not target_playlist:
            logger.info(f"Playlist '{playlist_name}' not found")
            logger.info("Creating new playlist...")

            try:
                playlist_obj = sp.user_playlist_create(
                    user_info["id"],
                    playlist_name,
                    public=False,
                    description="🎵 Radio des Îles - Dynamically generated Caribbean music playlist"
                )
                target_playlist = {
                    "id": playlist_obj["id"],
                    "name": playlist_obj["name"],
                    "owner": user_info["id"],
                    "public": False,
                    "tracks_count": 0
                }
                logger.info(f"✅ Created playlist: {playlist_name}")
            except Exception as e:
                logger.error(f"Error creating playlist: {e}")
                logger.error("This usually means your account is not Premium")
                sys.exit(1)

        logger.info(f"Target playlist: {target_playlist['name']} (ID: {target_playlist['id']})")
        logger.info(f"Current tracks: {target_playlist['tracks_count']}")

        # Search for tracks and get URIs
        logger.info(f"\nSearching for {len(tracks)} tracks on Spotify...")
        track_uris = []
        found_count = 0
        not_found = []

        for i, track in enumerate(tracks, 1):
            track_name = track.get("name", "")
            artists = track.get("artists", [])
            artist_name = artists[0] if artists else "Unknown"

            uri = search_and_get_track_uri(sp, track_name, artist_name)

            if uri:
                track_uris.append(uri)
                found_count += 1
                logger.info(f"  ✓ {i}/{len(tracks)}: {track_name} - {artist_name}")
            else:
                not_found.append(f"{track_name} - {artist_name}")
                logger.warning(f"  ✗ {i}/{len(tracks)}: {track_name} - {artist_name}")

        logger.info(f"\n📊 Results: {found_count}/{len(tracks)} tracks found")

        if not_found:
            logger.warning(f"\n❌ Not found ({len(not_found)}):")
            for track in not_found[:5]:  # Show first 5
                logger.warning(f"   • {track}")
            if len(not_found) > 5:
                logger.warning(f"   ... and {len(not_found) - 5} more")

        # Add tracks to playlist
        if track_uris:
            logger.info(f"\n📝 Adding {len(track_uris)} tracks to playlist...")
            add_tracks_to_playlist(sp, target_playlist["id"], track_uris)

        # Final result
        logger.info("\n" + "=" * 70)
        logger.info("✅ IMPORT COMPLETE!")
        logger.info("=" * 70)
        logger.info(f"\n🎵 Playlist: {target_playlist['name']}")
        logger.info(f"📊 Tracks added: {found_count}/{len(tracks)}")
        logger.info(f"🔗 Open Spotify to listen: https://open.spotify.com/playlist/{target_playlist['id']}")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import_playlist_to_spotify()
