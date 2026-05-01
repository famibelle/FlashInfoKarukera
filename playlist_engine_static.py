#!/usr/bin/env python3
"""
Spotify Dynamic Radio Playlist Engine - STATIC VERSION
Generates radio recommendations based on time of day
Uses a curated Caribbean music database - NO API REQUIRED

Works with:
- Free and Premium Spotify accounts
- Offline environments
- No Spotify API limitations
"""

import os
import sys
from datetime import datetime
from typing import List, Dict
import logging
import json
import random
from caribbean_db import get_tracks_by_mode, MODE_MAPPING, get_genres

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
        "description": "🌅 Ambiance matinale - Zouk doux & musique classique caribéenne"
    },
    RadioMode.MIDDAY: {
        "time_range": "12:00-17:59",
        "description": "☀️ Ambiance midi - Kompa & Zouk festif radio"
    },
    RadioMode.EVENING: {
        "time_range": "18:00-05:59",
        "description": "🌙 Ambiance soirée - Gwoka, Léwoz & vibes relaxantes"
    }
}


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
# PLAYLIST BUILDING LOGIC
# ============================================================================

def build_playlist(
    mode: str,
    target_size: int = 20
) -> List[Dict]:
    """
    Build a curated playlist for the given radio mode from static database.

    Args:
        mode: RadioMode constant
        target_size: Target number of tracks (default 20)

    Returns:
        List of track dictionaries with all info
    """
    config = RADIO_CONFIG[mode]

    logger.info(f"Building playlist for mode: {mode}")
    logger.info(f"Description: {config['description']}")

    # Get all tracks for this mode
    all_tracks = get_tracks_by_mode(mode)

    if not all_tracks:
        logger.warning(f"No tracks found for mode: {mode}")
        return []

    logger.info(f"Available tracks for this mode: {len(all_tracks)}")

    # Shuffle and select tracks
    shuffled = all_tracks.copy()
    random.shuffle(shuffled)

    # Take up to target_size tracks
    selected_tracks = shuffled[:min(target_size, len(shuffled))]

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
        "radio_description": RADIO_CONFIG[get_radio_mode()]["description"],
        "track_count": len(tracks),
        "tracks": tracks
    }

    filepath = os.path.join("playlists", filename)
    os.makedirs("playlists", exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Playlist exported to {filepath}")
    return filepath


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

    mode = get_radio_mode()
    config = RADIO_CONFIG[mode]

    content = f"""
═══════════════════════════════════════════════════════════════════════════════
🎵 RADIO DES ÎLES - PLAYLIST GENERATOR
═══════════════════════════════════════════════════════════════════════════════

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Radio Mode: {mode.upper()} {config['description']}

───────────────────────────────────────────────────────────────────────────────
TRACKS ({len(tracks)})
───────────────────────────────────────────────────────────────────────────────

"""

    for i, track in enumerate(tracks, 1):
        artists = ", ".join(track["artists"])
        content += f"{i:2d}. {track['name']}\n"
        content += f"    Artist(s): {artists}\n"
        if "uri" in track and track["uri"].startswith("spotify:"):
            content += f"    Spotify: {track['uri']}\n"
        content += "\n"

    content += f"""
───────────────────────────────────────────────────────────────────────────────
HOW TO IMPORT TO SPOTIFY (FREE ACCOUNT)
───────────────────────────────────────────────────────────────────────────────

1. Open Spotify (web or app)
2. Create a new playlist
3. Click "Add songs"
4. Search for each song using the title and artist
5. Add each track to your playlist

Alternative: Use the JSON file with a third-party tool
See: https://github.com/topics/spotify-playlist-importer

───────────────────────────────────────────────────────────────────────────────
═══════════════════════════════════════════════════════════════════════════════
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info(f"Playlist text exported to {filepath}")
    return filepath


def export_playlist_m3u(tracks: List[Dict], filename: str = None) -> str:
    """
    Export playlist in M3U format (compatible with many players).

    Args:
        tracks: List of track dictionaries
        filename: Optional output filename

    Returns:
        Path to saved M3U file
    """
    if not filename:
        now = datetime.now()
        mode = get_radio_mode(now.hour)
        filename = f"radio_playlist_{mode}_{now.strftime('%Y-%m-%d_%H-%M')}.m3u"

    filepath = os.path.join("playlists", filename)
    os.makedirs("playlists", exist_ok=True)

    content = "#EXTM3U\n"
    content += f"# Generated: {datetime.now().isoformat()}\n"
    content += f"# Mode: {get_radio_mode()}\n\n"

    for track in tracks:
        artists = ", ".join(track["artists"])
        content += f"#EXTINF:-1,{track['name']} - {artists}\n"
        content += f"{track.get('uri', '')}\n"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info(f"M3U playlist exported to {filepath}")
    return filepath


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

def run_playlist_engine():
    """
    Main orchestration function: detect hour → select mode → build → export.
    Static version - no Spotify API required!
    """
    try:
        # Get current time and determine mode
        now = datetime.now()
        hour = now.hour
        mode = get_radio_mode(hour)
        config = RADIO_CONFIG[mode]

        logger.info("=" * 70)
        logger.info("🎵 SPOTIFY RADIO PLAYLIST GENERATOR (STATIC VERSION)")
        logger.info("=" * 70)
        logger.info(f"\nCurrent time: {now.strftime('%H:%M:%S')}")
        logger.info(f"Radio mode: {mode.upper()} {config['description']}\n")

        # Show available genres
        genres = get_genres()
        logger.info("Available genres in database:")
        for genre, count in genres.items():
            logger.info(f"  • {genre}: {count} tracks")

        # Build playlist
        tracks = build_playlist(mode, target_size=20)

        if not tracks:
            logger.error("Failed to build playlist: no tracks found")
            sys.exit(1)

        # Export to multiple formats
        json_file = export_to_json(tracks)
        txt_file = export_playlist_text(tracks)
        m3u_file = export_playlist_m3u(tracks)

        # Print results
        logger.info("\n" + "=" * 70)
        logger.info("✅ PLAYLIST GENERATED SUCCESSFULLY!")
        logger.info("=" * 70)
        logger.info(f"\n📁 Files saved:")
        logger.info(f"   • JSON: {json_file}")
        logger.info(f"   • Text: {txt_file}")
        logger.info(f"   • M3U:  {m3u_file}")
        logger.info(f"\n🎵 Tracks in playlist: {len(tracks)}")
        logger.info(f"\n📋 NEXT STEPS:")
        logger.info(f"   1. Open {txt_file}")
        logger.info(f"   2. Search each track in Spotify")
        logger.info(f"   3. Add to your playlist")
        logger.info(f"\n🎧 First 5 tracks:")
        for i, track in enumerate(tracks[:5], 1):
            artists = ", ".join(track["artists"])
            logger.info(f"   {i}. {track['name']} - {artists}")

        logger.info("\n" + "=" * 70)

    except Exception as e:
        logger.error(f"Fatal error in playlist engine: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_playlist_engine()
