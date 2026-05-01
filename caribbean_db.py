#!/usr/bin/env python3
"""
Caribbean Music Database
Curated list of Caribbean tracks (platform-agnostic — names and artists only).
The playlist engine searches for these on Deezer at runtime.
To add a track: just add name + artists, no ID needed.
"""

CARIBBEAN_TRACKS = {
    "zouk": [
        {"name": "Zouk Machine",                      "artists": ["Zouk Machine"]},
        {"name": "Maldon",                             "artists": ["Zouk Machine"]},
        {"name": "A Lot of Love",                      "artists": ["Kassav"]},
        {"name": "Zouk La Sé Sel Medikaman Nou Ni",    "artists": ["Kassav"]},
        {"name": "Doudou-a-Doudou",                    "artists": ["Princess Caroline"]},
        {"name": "Patiemment",                         "artists": ["Gilles Floro"]},
        {"name": "Ka Dansé",                           "artists": ["Gilles Floro"]},
        {"name": "Chez les Zoukettes",                 "artists": ["Edith Lefel"]},
    ],
    "kompa": [
        {"name": "Meter Dife",      "artists": ["T-Vice"]},
        {"name": "Kita Kita",       "artists": ["T-Vice"]},
        {"name": "Aba Gouche",      "artists": ["Tabou Combo"]},
        {"name": "Tabou Love",      "artists": ["Tabou Combo"]},
        {"name": "Lampe Lantern",   "artists": ["Bel Accord"]},
        {"name": "Sentimental",     "artists": ["Bel Accord"]},
        {"name": "Haiti Cherie",    "artists": ["Nemours Jean-Baptiste"]},
    ],
    "gwoka": [
        {"name": "Gwoka Live",   "artists": ["Gérald Thalius"]},
        {"name": "Touyéy",       "artists": ["Gérald Thalius"]},
        {"name": "Bèlè Kréyòl",  "artists": ["Valérie Dhorasoo"]},
        {"name": "Woulé Gwoka",  "artists": ["Papa Liso"]},
        {"name": "Gwoka Drum",   "artists": ["Gérard Lockel"]},
    ],
    "reggae": [
        {"name": "Three Little Birds",  "artists": ["Bob Marley"]},
        {"name": "Redemption Song",     "artists": ["Bob Marley"]},
        {"name": "Get Up Stand Up",     "artists": ["Bob Marley"]},
        {"name": "Iron Lion Zion",      "artists": ["Bob Marley"]},
        {"name": "Is This Love",        "artists": ["Bob Marley"]},
        {"name": "One Love",            "artists": ["Bob Marley"]},
    ],
    "roots": [
        {"name": "Roots Vision",  "artists": ["Burning Spear"]},
        {"name": "Jah Rasta Fari","artists": ["Burning Spear"]},
        {"name": "Reggae Riddim", "artists": ["Luciano"]},
        {"name": "Ancient Wisdom","artists": ["Midnite"]},
    ],
    "chill": [
        {"name": "Chill Out Vibes",    "artists": ["Ky-Mani Marley"]},
        {"name": "Easy to Love",       "artists": ["Damian Marley"]},
        {"name": "Welcome to Jamrock", "artists": ["Damian Marley"]},
        {"name": "Sunset Boulevard",   "artists": ["Shaggy"]},
        {"name": "Angel",              "artists": ["Shaggy"]},
    ],
    "dancehall": [
        {"name": "Sensimilla",    "artists": ["Shabba Ranks"]},
        {"name": "Ting-A-Ling",   "artists": ["Shabba Ranks"]},
        {"name": "Rub A Dub",     "artists": ["Sean Paul"]},
        {"name": "Get Busy",      "artists": ["Sean Paul"]},
        {"name": "Hips Don't Lie","artists": ["Shakira", "Wyclef Jean"]},
    ],
    "soca": [
        {"name": "Wining Queen", "artists": ["Kes"]},
        {"name": "Palance",      "artists": ["Machel Montano"]},
        {"name": "Bacchanal",    "artists": ["Machel Montano"]},
        {"name": "Pump It Up",   "artists": ["Bunji Garlin"]},
        {"name": "Roll It Gal",  "artists": ["Bunji Garlin"]},
    ],
}

MODE_MAPPING = {
    "morning": ["zouk", "reggae", "chill"],
    "midday":  ["kompa", "soca", "dancehall", "zouk"],
    "evening": ["gwoka", "roots", "reggae", "chill"],
}


def get_tracks_by_mode(mode: str) -> list:
    """Return all tracks for the given mode (shuffled genres)."""
    tracks = []
    for genre in MODE_MAPPING.get(mode, []):
        tracks.extend(CARIBBEAN_TRACKS.get(genre, []))
    return tracks


def get_all_tracks() -> list:
    return [t for tracks in CARIBBEAN_TRACKS.values() for t in tracks]


def get_genres() -> dict:
    return {genre: len(tracks) for genre, tracks in CARIBBEAN_TRACKS.items()}
