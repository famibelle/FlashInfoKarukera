#!/usr/bin/env python3
"""
Carribean Music Database
Curated list of Caribbean songs for the radio playlist system
"""

CARIBBEAN_TRACKS = {
    "zouk": [
        {"name": "Zouk Machine", "artists": ["Zouk Machine"], "uri": "spotify:track:zouk_machine_1"},
        {"name": "Maldon", "artists": ["Zouk Machine"], "uri": "spotify:track:zouk_machine_2"},
        {"name": "A Lot of Love", "artists": ["Kassav"], "uri": "spotify:track:kassav_1"},
        {"name": "Zouk La Sé Sel Medikaman Nou Ni", "artists": ["Kassav"], "uri": "spotify:track:kassav_2"},
        {"name": "Doudou-a-Doudou", "artists": ["Princess Caroline"], "uri": "spotify:track:princess_1"},
        {"name": "Patiemment", "artists": ["Gilles Floro"], "uri": "spotify:track:gilles_1"},
        {"name": "Ka Dansé", "artists": ["Gilles Floro"], "uri": "spotify:track:gilles_2"},
        {"name": "Chez les Zoukettes", "artists": ["Edith Lefel"], "uri": "spotify:track:edith_1"},
    ],
    "kompa": [
        {"name": "Meter Dife", "artists": ["T-Vice"], "uri": "spotify:track:tvice_1"},
        {"name": "Kita Kita", "artists": ["T-Vice"], "uri": "spotify:track:tvice_2"},
        {"name": "Aba Gouche", "artists": ["Tabou Combo"], "uri": "spotify:track:tabou_1"},
        {"name": "Tabou Love", "artists": ["Tabou Combo"], "uri": "spotify:track:tabou_2"},
        {"name": "Lampe Lantern", "artists": ["Bel Accord"], "uri": "spotify:track:bel_1"},
        {"name": "Sentimental", "artists": ["Bel Accord"], "uri": "spotify:track:bel_2"},
        {"name": "Haiti Cherie", "artists": ["Nemours Jean-Baptiste"], "uri": "spotify:track:nemours_1"},
    ],
    "gwoka": [
        {"name": "Gwoka Live", "artists": ["Gérald Thalius"], "uri": "spotify:track:gerald_1"},
        {"name": "Touyéy", "artists": ["Gérald Thalius"], "uri": "spotify:track:gerald_2"},
        {"name": "Bèlè Kréyòl", "artists": ["Valérie Dhorasoo"], "uri": "spotify:track:valerie_1"},
        {"name": "Woulé Gwoka", "artists": ["Papa Liso"], "uri": "spotify:track:papa_1"},
        {"name": "Gwoka Drum", "artists": ["Gérard Lockel"], "uri": "spotify:track:gerard_1"},
    ],
    "reggae": [
        {"name": "Three Little Birds", "artists": ["Bob Marley"], "uri": "spotify:track:bob_1"},
        {"name": "Redemption Song", "artists": ["Bob Marley"], "uri": "spotify:track:bob_2"},
        {"name": "Get Up Stand Up", "artists": ["Bob Marley & Peter Tosh"], "uri": "spotify:track:bob_3"},
        {"name": "Iron Lion Zion", "artists": ["Bob Marley"], "uri": "spotify:track:bob_4"},
        {"name": "Is This Love", "artists": ["Bob Marley"], "uri": "spotify:track:bob_5"},
        {"name": "One Love", "artists": ["Bob Marley"], "uri": "spotify:track:bob_6"},
    ],
    "roots": [
        {"name": "Roots Vision", "artists": ["Burning Spear"], "uri": "spotify:track:burning_1"},
        {"name": "Jah Rasta Fari", "artists": ["Burning Spear"], "uri": "spotify:track:burning_2"},
        {"name": "Reggae Riddim", "artists": ["Luciano"], "uri": "spotify:track:luciano_1"},
        {"name": "Ancient Wisdom", "artists": ["Midnite"], "uri": "spotify:track:midnite_1"},
    ],
    "chill": [
        {"name": "Chill Out Vibes", "artists": ["Ky-Mani Marley"], "uri": "spotify:track:kymani_1"},
        {"name": "Easy to Love", "artists": ["Damian Marley"], "uri": "spotify:track:damian_1"},
        {"name": "Welcome to Jamrock", "artists": ["Damian Marley"], "uri": "spotify:track:damian_2"},
        {"name": "Sunset Boulevard", "artists": ["Shaggy"], "uri": "spotify:track:shaggy_1"},
        {"name": "Angel", "artists": ["Shaggy"], "uri": "spotify:track:shaggy_2"},
    ],
    "dancehall": [
        {"name": "Sensimilla", "artists": ["Shabba Ranks"], "uri": "spotify:track:shabba_1"},
        {"name": "Ting-A-Ling", "artists": ["Shabba Ranks"], "uri": "spotify:track:shabba_2"},
        {"name": "Rub A Dub", "artists": ["Sean Paul"], "uri": "spotify:track:sean_1"},
        {"name": "Get Busy", "artists": ["Sean Paul"], "uri": "spotify:track:sean_2"},
        {"name": "Hips Don't Lie", "artists": ["Shakira", "Wyclef Jean"], "uri": "spotify:track:shakira_1"},
    ],
    "soca": [
        {"name": "Wining Queen", "artists": ["Kes"], "uri": "spotify:track:kes_1"},
        {"name": "Palance", "artists": ["Machel Montano"], "uri": "spotify:track:machel_1"},
        {"name": "Bacchanal", "artists": ["Machel Montano"], "uri": "spotify:track:machel_2"},
        {"name": "Pump It Up", "artists": ["Bunji Garlin"], "uri": "spotify:track:bunji_1"},
        {"name": "Roll It Gal", "artists": ["Bunji Garlin"], "uri": "spotify:track:bunji_2"},
    ],
}

# Mapping genres to modes
MODE_MAPPING = {
    "morning": ["zouk", "reggae", "chill"],
    "midday": ["kompa", "soca", "dancehall", "zouk"],
    "evening": ["gwoka", "roots", "reggae", "chill"],
}

def get_tracks_by_mode(mode: str) -> list:
    """
    Get tracks for a specific radio mode.
    
    Args:
        mode: Radio mode ('morning', 'midday', 'evening')
        
    Returns:
        List of tracks for the mode
    """
    genres = MODE_MAPPING.get(mode, [])
    tracks = []
    
    for genre in genres:
        if genre in CARIBBEAN_TRACKS:
            tracks.extend(CARIBBEAN_TRACKS[genre])
    
    return tracks

def get_all_tracks() -> list:
    """Get all tracks in the database"""
    all_tracks = []
    for genre, tracks in CARIBBEAN_TRACKS.items():
        all_tracks.extend(tracks)
    return all_tracks

def get_genres() -> dict:
    """Get all genres and their track counts"""
    return {genre: len(tracks) for genre, tracks in CARIBBEAN_TRACKS.items()}
