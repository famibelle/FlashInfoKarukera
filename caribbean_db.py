#!/usr/bin/env python3
"""
Caribbean Music Database — Zouk, Gwoka, Kompa uniquement.
Aucun URI/ID — le moteur de playlist résout les titres à l'exécution.
"""

CARIBBEAN_TRACKS = {
    "zouk": [
        {"name": "Zouk Machine",                        "artists": ["Zouk Machine"]},
        {"name": "Maldon",                              "artists": ["Zouk Machine"]},
        {"name": "A Lot of Love",                       "artists": ["Kassav"]},
        {"name": "Zouk La Sé Sel Medikaman Nou Ni",     "artists": ["Kassav"]},
        {"name": "Syé Bwa",                             "artists": ["Kassav"]},
        {"name": "Kolé Séré",                           "artists": ["Kassav"]},
        {"name": "Doudou-a-Doudou",                     "artists": ["Princess Caroline"]},
        {"name": "Patiemment",                          "artists": ["Gilles Floro"]},
        {"name": "Ka Dansé",                            "artists": ["Gilles Floro"]},
        {"name": "Chez les Zoukettes",                  "artists": ["Edith Lefel"]},
        {"name": "Toujou Rèd",                          "artists": ["Edith Lefel"]},
        {"name": "Amour Plastique",                     "artists": ["Edith Lefel"]},
        {"name": "Lélé",                                "artists": ["Tanya Saint-Val"]},
        {"name": "Ce Soir",                             "artists": ["Tanya Saint-Val"]},
        {"name": "Aimer d'amour",                       "artists": ["Jocelyne Labylle"]},
        {"name": "Palé Ba Mwen",                        "artists": ["Jocelyne Labylle"]},
        {"name": "Aïe",                                 "artists": ["Ralph Thamar"]},
        {"name": "Mové Jou",                            "artists": ["Ralph Thamar"]},
        {"name": "Désirs d'enfants",                    "artists": ["Claudette Anderson"]},
        {"name": "Nou pé ké séparé",                    "artists": ["Jean-Philippe Marthely"]},
    ],
    "gwoka": [
        {"name": "Gwoka Live",          "artists": ["Gérald Thalius"]},
        {"name": "Touyéy",              "artists": ["Gérald Thalius"]},
        {"name": "Zétwal an nou",       "artists": ["Gérald Thalius"]},
        {"name": "Bèlè Kréyòl",        "artists": ["Valérie Dhorasoo"]},
        {"name": "Pa fonsé",            "artists": ["Valérie Dhorasoo"]},
        {"name": "Woulé Gwoka",         "artists": ["Papa Liso"]},
        {"name": "Gwoka Drum",          "artists": ["Gérard Lockel"]},
        {"name": "Lewoz",               "artists": ["Gérard Lockel"]},
        {"name": "Mawonaj",             "artists": ["Ti Paris"]},
        {"name": "Vélo",                "artists": ["Ti Paris"]},
        {"name": "Mas a mas",           "artists": ["Anzala"]},
        {"name": "Graj Kò'w",           "artists": ["Anzala"]},
        {"name": "Kan nou té jenn",     "artists": ["Carlos Nilson"]},
        {"name": "Sonjé",               "artists": ["Carlos Nilson"]},
    ],
    "kompa": [
        {"name": "Meter Dife",              "artists": ["T-Vice"]},
        {"name": "Kita Kita",               "artists": ["T-Vice"]},
        {"name": "Ou fèm pè",               "artists": ["T-Vice"]},
        {"name": "Aba Gouche",              "artists": ["Tabou Combo"]},
        {"name": "Tabou Love",              "artists": ["Tabou Combo"]},
        {"name": "New York City",           "artists": ["Tabou Combo"]},
        {"name": "Lampe Lantern",           "artists": ["Bel Accord"]},
        {"name": "Sentimental",             "artists": ["Bel Accord"]},
        {"name": "Haiti Cherie",            "artists": ["Nemours Jean-Baptiste"]},
        {"name": "Konpa Kreyòl",            "artists": ["Nemours Jean-Baptiste"]},
        {"name": "Tchaka",                  "artists": ["Carimi"]},
        {"name": "Rose",                    "artists": ["Carimi"]},
        {"name": "Ou Pito",                 "artists": ["Nu-Look"]},
        {"name": "Si m ta konnen",          "artists": ["Nu-Look"]},
        {"name": "Pa kite'm",               "artists": ["Harmonik"]},
        {"name": "Nati pa'm",               "artists": ["Harmonik"]},
        {"name": "Sans issue",              "artists": ["Djakout #1"]},
        {"name": "Balance",                 "artists": ["Djakout #1"]},
        {"name": "Pran swen",               "artists": ["Zin"]},
        {"name": "Kè m pa sote",            "artists": ["Zin"]},
    ],
}

MODE_MAPPING = {
    "morning": ["zouk", "gwoka"],
    "midday":  ["kompa", "zouk"],
    "evening": ["gwoka", "zouk", "kompa"],
}


def get_tracks_by_mode(mode: str) -> list:
    tracks = []
    for genre in MODE_MAPPING.get(mode, []):
        tracks.extend(CARIBBEAN_TRACKS.get(genre, []))
    return tracks


def get_all_tracks() -> list:
    return [t for tracks in CARIBBEAN_TRACKS.values() for t in tracks]


def get_genres() -> dict:
    return {genre: len(tracks) for genre, tracks in CARIBBEAN_TRACKS.items()}
