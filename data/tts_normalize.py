"""Données de normalisation textuelle appliquées avant l'appel TTS Voxtral."""

# Prononciations locales guadeloupéennes (forme écrite → forme orale pour le TTS)
PRONONCIATIONS_LOCALES = {
    # Prononciations créoles
    "Lyannaj": "Lyan naje",   # Lyan-naje, deux syllabes distinctes
    "lyannaj": "Lyan naje",
    "Vieux-Habitants": "Vieux Zabitan",
    "Vieux Habitants":  "Vieux Zabitan",
    "Delgrès":          "Delgrèsse",   # /dɛl.ɡʁɛs/ — force le s final
    "Henri IV":         "Henri Quatre",
    "Henri 4":          "Henri Quatre",
    "cité Henri IV":    "cité Henri Quatre",
    "cité Henri 4":     "cité Henri Quatre",
    # Code départemental (filet de sécurité si le LLM l'a quand même converti)
    "neuf cent soixante et onze": "quatre-vingt-dix-sept-un",
    "971": "quatre-vingt-dix-sept-un",
    # Sigles locaux développés (avant l'épellation automatique)
    "UNAR": "Union Athlétique de Rivière-des-Pères",
    "JSVH": "Jeunesse Sportive de Vieux Zabitan",
    "SDIS": "Service Départemental d'Incendie et de Secours",
    "S.D.I.S": "Service Départemental d'Incendie et de Secours",
    "S.D.I.S.": "Service Départemental d'Incendie et de Secours",
}

# Sigles prononcés comme des mots (ne pas épeler lettre par lettre)
SIGLES_MOT = {"RCI", "UNESCO", "UNICEF", "NASA"}

# Abréviations et symboles à développer pour le TTS
ABBREVS = {
    "M.": "Monsieur", "Mme.": "Madame", "Mme": "Madame",
    "Dr.": "Docteur", "Dr": "Docteur", "Pr.": "Professeur", "Pr": "Professeur",
    "St.": "Saint", "Ste.": "Sainte",
    "km/h": "kilomètres par heure", "km": "kilomètres",
    "°C": "degrés", "m²": "mètres carrés", "m³": "mètres cubes",
    "&": "et", "...": ".",
}
