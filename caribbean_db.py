#!/usr/bin/env python3
"""
Caribbean Music Database — Zouk, Zouk rétro, Gwoka, Kompa, Chatta, Bouillon.
Aucun URI/ID — le moteur de playlist résout les titres à l'exécution.
"""

CARIBBEAN_TRACKS = {
    "zouk": [
        # Kassav
        {"name": "Zouk La Sé Sel Medikaman Nou Ni",     "artists": ["Kassav"]},
        {"name": "Syé Bwa",                              "artists": ["Kassav"]},
        {"name": "Kolé Séré",                            "artists": ["Kassav"]},
        {"name": "A Lot of Love",                        "artists": ["Kassav"]},
        {"name": "Mwen Malad Aw",                        "artists": ["Kassav"]},
        {"name": "Je Suis Né Créole",                    "artists": ["Kassav"]},
        {"name": "Ou Lé Sa",                             "artists": ["Kassav"]},
        # Zouk Machine
        {"name": "Maldon",                               "artists": ["Zouk Machine"]},
        {"name": "Zouk Machine",                         "artists": ["Zouk Machine"]},
        {"name": "Adieu Forain",                         "artists": ["Zouk Machine"]},
        {"name": "Siwo",                                 "artists": ["Zouk Machine"]},
        # Jocelyne Labylle
        {"name": "Aimer d'amour",                        "artists": ["Jocelyne Labylle"]},
        {"name": "Palé Ba Mwen",                         "artists": ["Jocelyne Labylle"]},
        {"name": "Amour Interdit",                       "artists": ["Jocelyne Labylle"]},
        {"name": "Ti zwazo",                             "artists": ["Jocelyne Labylle"]},
        # Tanya Saint-Val
        {"name": "Lélé",                                 "artists": ["Tanya Saint-Val"]},
        {"name": "Ce Soir",                              "artists": ["Tanya Saint-Val"]},
        {"name": "Tou dousiw",                           "artists": ["Tanya Saint-Val"]},
        {"name": "Je ne veux que toi",                   "artists": ["Tanya Saint-Val"]},
        # Jean-Philippe Marthely
        {"name": "Nou pé ké séparé",                     "artists": ["Jean-Philippe Marthely"]},
        {"name": "An Ba Chenn",                          "artists": ["Jean-Philippe Marthely"]},
        {"name": "Manjé Sal",                            "artists": ["Jean-Philippe Marthely"]},
        # Tatiana
        {"name": "Hé Oh Hé",                             "artists": ["Tatiana"]},
        {"name": "Coeur blessé",                         "artists": ["Tatiana"]},
        {"name": "Si tu savais",                         "artists": ["Tatiana"]},
        # Ralph Thamar
        {"name": "Aïe",                                  "artists": ["Ralph Thamar"]},
        {"name": "Mové Jou",                             "artists": ["Ralph Thamar"]},
        {"name": "Yen a marre",                          "artists": ["Ralph Thamar"]},
        {"name": "Éloge de la créole",                   "artists": ["Ralph Thamar"]},
        # Princess Caroline
        {"name": "Doudou-a-Doudou",                      "artists": ["Princess Caroline"]},
        {"name": "Jou di Bondié",                        "artists": ["Princess Caroline"]},
        {"name": "Rêve ou réalité",                      "artists": ["Princess Caroline"]},
        # Claudette Anderson
        {"name": "Désirs d'enfants",                     "artists": ["Claudette Anderson"]},
        {"name": "Ti Larivyè",                           "artists": ["Claudette Anderson"]},
        # Gilles Floro
        {"name": "Patiemment",                           "artists": ["Gilles Floro"]},
    ],

    "zouk_retro": [
        # Edith Lefel
        {"name": "Chez les Zoukettes",                   "artists": ["Edith Lefel"]},
        {"name": "Toujou Rèd",                           "artists": ["Edith Lefel"]},
        {"name": "Amour Plastique",                      "artists": ["Edith Lefel"]},
        {"name": "Bébé",                                 "artists": ["Edith Lefel"]},
        {"name": "Mouri pou mouri",                      "artists": ["Edith Lefel"]},
        # Patrick Saint-Eloi
        {"name": "Si Je Savais",                         "artists": ["Patrick Saint-Eloi"]},
        {"name": "Lanmou Ké Nou",                        "artists": ["Patrick Saint-Eloi"]},
        {"name": "Je ne sais plus",                      "artists": ["Patrick Saint-Eloi"]},
        {"name": "Vié ko",                               "artists": ["Patrick Saint-Eloi"]},
        {"name": "Sucré-salé",                           "artists": ["Patrick Saint-Eloi"]},
        {"name": "Sonjé",                                "artists": ["Patrick Saint-Eloi"]},
        # Jacob Desvarieux (solo)
        {"name": "Douce France",                         "artists": ["Jacob Desvarieux"]},
        {"name": "Bi Yé",                                "artists": ["Jacob Desvarieux"]},
        {"name": "Promenons-nous dans les bois",         "artists": ["Jacob Desvarieux"]},
        # Gilles Floro
        {"name": "Ka Dansé",                             "artists": ["Gilles Floro"]},
        {"name": "Tibouchina",                           "artists": ["Gilles Floro"]},
        {"name": "Tout doux",                            "artists": ["Gilles Floro"]},
        # Claudette Anderson (retro)
        {"name": "Kon yon sel",                          "artists": ["Claudette Anderson"]},
        {"name": "Bèl ti manmay",                        "artists": ["Claudette Anderson"]},
        # Frédéric Caracas
        {"name": "Mal nécessaire",                       "artists": ["Frédéric Caracas"]},
        {"name": "Lamour pa ka manti",                   "artists": ["Frédéric Caracas"]},
        {"name": "Nana",                                 "artists": ["Frédéric Caracas"]},
        # Dominique Zorobabel
        {"name": "Krazé la fèt",                         "artists": ["Dominique Zorobabel"]},
        {"name": "Chak matin",                           "artists": ["Dominique Zorobabel"]},
        {"name": "Madras",                               "artists": ["Dominique Zorobabel"]},
        # Guy Houllié
        {"name": "Amour couleur chocolat",               "artists": ["Guy Houllié"]},
        {"name": "Pa di mwen sa",                        "artists": ["Guy Houllié"]},
        {"name": "Ti bonhomme",                          "artists": ["Guy Houllié"]},
        # Kassav retro (classiques 80s)
        {"name": "Syé Bwa",                              "artists": ["Kassav"]},
        {"name": "Ou Pa Connaît Malheur",                "artists": ["Kassav"]},
        {"name": "Douvanjou Ka Lévé",                    "artists": ["Kassav"]},
        {"name": "Alé",                                  "artists": ["Kassav"]},
        # Zouk Machine retro
        {"name": "Mazouk a nou",                         "artists": ["Zouk Machine"]},
        {"name": "Maldòn",                               "artists": ["Zouk Machine"]},
        # Ralph Thamar retro
        {"name": "Matinik sé tan nou",                   "artists": ["Ralph Thamar"]},
    ],

    "gwoka": [
        # Gérald Thalius
        {"name": "Touyéy",                               "artists": ["Gérald Thalius"]},
        {"name": "Zétwal an nou",                        "artists": ["Gérald Thalius"]},
        {"name": "Gwoka Live",                           "artists": ["Gérald Thalius"]},
        {"name": "Bòdaj",                                "artists": ["Gérald Thalius"]},
        {"name": "Fòs péyi nou",                         "artists": ["Gérald Thalius"]},
        # Gérard Lockel
        {"name": "Gwoka Drum",                           "artists": ["Gérard Lockel"]},
        {"name": "Lewoz",                                "artists": ["Gérard Lockel"]},
        {"name": "Gwo Ka Modènn",                        "artists": ["Gérard Lockel"]},
        {"name": "Ka Fô Nou Fè",                         "artists": ["Gérard Lockel"]},
        # Ti Paris
        {"name": "Mawonaj",                              "artists": ["Ti Paris"]},
        {"name": "Vélo",                                 "artists": ["Ti Paris"]},
        {"name": "Wout a mwen",                          "artists": ["Ti Paris"]},
        {"name": "Péyi la",                              "artists": ["Ti Paris"]},
        # Anzala
        {"name": "Mas a mas",                            "artists": ["Anzala"]},
        {"name": "Graj Kò'w",                            "artists": ["Anzala"]},
        {"name": "Lévé doubout",                         "artists": ["Anzala"]},
        # Carlos Nilson
        {"name": "Kan nou té jenn",                      "artists": ["Carlos Nilson"]},
        {"name": "Sonjé",                                "artists": ["Carlos Nilson"]},
        {"name": "Péyi doubout",                         "artists": ["Carlos Nilson"]},
        # Léona Gabriel
        {"name": "Soley kouché",                         "artists": ["Léona Gabriel"]},
        {"name": "An fanm doubout",                      "artists": ["Léona Gabriel"]},
        {"name": "Té ka chanté",                         "artists": ["Léona Gabriel"]},
        # Marcé
        {"name": "Gwo Ka",                               "artists": ["Marcé"]},
        {"name": "Léwòz a Marcé",                        "artists": ["Marcé"]},
        {"name": "Sové Doubout",                         "artists": ["Marcé"]},
        {"name": "Tambou ka sonné",                      "artists": ["Marcé"]},
        # Divers gwoka
        {"name": "Voukoum tambou",                       "artists": ["Voukoum"]},
        {"name": "Ka doubout",                           "artists": ["Jacob Desvarieux"]},
        {"name": "Mas a Mas",                            "artists": ["Akiyo"]},
        {"name": "Léwòz",                                "artists": ["Ti Paris", "Anzala"]},
    ],

    "kompa": [
        # T-Vice
        {"name": "Meter Dife",                           "artists": ["T-Vice"]},
        {"name": "Kita Kita",                            "artists": ["T-Vice"]},
        {"name": "Ou fèm pè",                            "artists": ["T-Vice"]},
        {"name": "Déréglé",                              "artists": ["T-Vice"]},
        {"name": "Fè yon bagay",                         "artists": ["T-Vice"]},
        # Tabou Combo
        {"name": "Aba Gouche",                           "artists": ["Tabou Combo"]},
        {"name": "New York City",                        "artists": ["Tabou Combo"]},
        {"name": "Tabou Love",                           "artists": ["Tabou Combo"]},
        {"name": "Haiti",                                "artists": ["Tabou Combo"]},
        {"name": "Kamoken",                              "artists": ["Tabou Combo"]},
        {"name": "La Toto",                              "artists": ["Tabou Combo"]},
        # Carimi
        {"name": "Tchaka",                               "artists": ["Carimi"]},
        {"name": "Rose",                                 "artists": ["Carimi"]},
        {"name": "Ou beswen mwen",                       "artists": ["Carimi"]},
        {"name": "Pwofesè",                              "artists": ["Carimi"]},
        {"name": "Ou pa bon pou mwen",                   "artists": ["Carimi"]},
        # Nu-Look
        {"name": "Ou Pito",                              "artists": ["Nu-Look"]},
        {"name": "Si m ta konnen",                       "artists": ["Nu-Look"]},
        {"name": "Ou toujou bèl",                        "artists": ["Nu-Look"]},
        {"name": "Se pou ou",                            "artists": ["Nu-Look"]},
        # Harmonik
        {"name": "Pa kite'm",                            "artists": ["Harmonik"]},
        {"name": "Nati pa'm",                            "artists": ["Harmonik"]},
        {"name": "Mwen pa vle",                          "artists": ["Harmonik"]},
        {"name": "Ba mwen yon ti bo",                    "artists": ["Harmonik"]},
        {"name": "Kite yo pale",                         "artists": ["Harmonik"]},
        # Djakout #1
        {"name": "Sans issue",                           "artists": ["Djakout #1"]},
        {"name": "Balance",                              "artists": ["Djakout #1"]},
        {"name": "Renmen w",                             "artists": ["Djakout #1"]},
        {"name": "Ayiti pa pèdi",                        "artists": ["Djakout #1"]},
        # Zin
        {"name": "Pran swen",                            "artists": ["Zin"]},
        {"name": "Kè m pa sote",                         "artists": ["Zin"]},
        {"name": "Ou mèt ale",                           "artists": ["Zin"]},
        {"name": "Pa di'm adye",                         "artists": ["Zin"]},
        # Bel Accord
        {"name": "Lampe Lantern",                        "artists": ["Bel Accord"]},
        {"name": "Sentimental",                          "artists": ["Bel Accord"]},
        {"name": "Pa janm kite'm",                       "artists": ["Bel Accord"]},
        # Nemours Jean-Baptiste
        {"name": "Haiti Cherie",                         "artists": ["Nemours Jean-Baptiste"]},
        {"name": "Konpa Kreyòl",                         "artists": ["Nemours Jean-Baptiste"]},
        {"name": "Choucoune",                            "artists": ["Nemours Jean-Baptiste"]},
        {"name": "Ti-coca",                              "artists": ["Nemours Jean-Baptiste"]},
        # Sweet Micky (Michel Martelly)
        {"name": "Ou la la",                             "artists": ["Sweet Micky"]},
        {"name": "Micky pa renmen sa",                   "artists": ["Sweet Micky"]},
        {"name": "Ban mwen yon ti bo",                   "artists": ["Sweet Micky"]},
        # BélO
        {"name": "BélO",                                 "artists": ["BélO"]},
        {"name": "Manman",                               "artists": ["BélO"]},
        {"name": "Pa pati",                              "artists": ["BélO"]},
        {"name": "Revòlisyon",                           "artists": ["BélO"]},
        # Top Vice
        {"name": "Kè m poko lib",                        "artists": ["Top Vice"]},
        {"name": "Ayibobo",                              "artists": ["Top Vice"]},
        {"name": "Ou bèl",                               "artists": ["Top Vice"]},
    ],

    "chatta": [
        # Akiyo
        {"name": "Akiyo an ba la",                       "artists": ["Akiyo"]},
        {"name": "Fraternité",                           "artists": ["Akiyo"]},
        {"name": "Résistans",                            "artists": ["Akiyo"]},
        {"name": "Tèt a tèt",                            "artists": ["Akiyo"]},
        # Voukoum
        {"name": "Voukoum kanaval",                      "artists": ["Voukoum"]},
        {"name": "Gwoka mas",                            "artists": ["Voukoum"]},
        {"name": "Doubout pou péyi",                     "artists": ["Voukoum"]},
        {"name": "Mas doubout",                          "artists": ["Voukoum"]},
        # Mass Kanal
        {"name": "Chatta Mass Kanal",                    "artists": ["Mass Kanal"]},
        {"name": "Péyi a nou",                           "artists": ["Mass Kanal"]},
        {"name": "Doubout Gwadloup",                     "artists": ["Mass Kanal"]},
        {"name": "Mas ka défilé",                        "artists": ["Mass Kanal"]},
        # Kan'nida
        {"name": "Kanaval",                              "artists": ["Kan'nida"]},
        {"name": "Lévé doubout",                         "artists": ["Kan'nida"]},
        {"name": "Mas an listwa",                        "artists": ["Kan'nida"]},
        {"name": "Chanté pou péyi",                      "artists": ["Kan'nida"]},
        # Gaoulé
        {"name": "Gaoulé mas",                           "artists": ["Gaoulé"]},
        {"name": "Tanbou doubout",                       "artists": ["Gaoulé"]},
        {"name": "Péyi la ka chanté",                    "artists": ["Gaoulé"]},
        {"name": "Fos mas",                              "artists": ["Gaoulé"]},
    ],

    "bouillon": [
        # WCK (Windward Caribbean Kulture)
        {"name": "Jing Ping",                            "artists": ["WCK"]},
        {"name": "Ring de Bell",                         "artists": ["WCK"]},
        {"name": "Bouyon Massive",                       "artists": ["WCK"]},
        {"name": "Willy the Man",                        "artists": ["WCK"]},
        # Burning Flames
        {"name": "Pump Me Up",                           "artists": ["Burning Flames"]},
        {"name": "Worky Worky",                          "artists": ["Burning Flames"]},
        {"name": "Fete",                                 "artists": ["Burning Flames"]},
        {"name": "Nah Let Go",                           "artists": ["Burning Flames"]},
        # Jeff Joe
        {"name": "Sweet Dominica",                       "artists": ["Jeff Joe"]},
        {"name": "Island Life",                          "artists": ["Jeff Joe"]},
        {"name": "Jouway Morning",                       "artists": ["Jeff Joe"]},
        # Exile One
        {"name": "Lotion",                               "artists": ["Exile One"]},
        {"name": "E Lo Lo",                              "artists": ["Exile One"]},
        {"name": "Wilomele",                             "artists": ["Exile One"]},
        # Al Lirvat (biguine)
        {"name": "Biguine à Gogo",                       "artists": ["Al Lirvat"]},
        {"name": "Mazurka créole",                       "artists": ["Al Lirvat"]},
        {"name": "La Chouval Bwa",                       "artists": ["Al Lirvat"]},
        # Dédé Saint-Prix (biguine/créole)
        {"name": "Anba Tonnel",                          "artists": ["Dédé Saint-Prix"]},
        {"name": "Jou ouvè",                             "artists": ["Dédé Saint-Prix"]},
        # Stellio (biguine classique)
        {"name": "Biguine à St-Pierre",                  "artists": ["Stellio"]},
    ],
}

MODE_MAPPING = {
    "night":   ["zouk_retro", "gwoka", "bouillon"],
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
