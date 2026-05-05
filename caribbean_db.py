#!/usr/bin/env python3
"""
Caribbean Music Database — Playlist par genre pour FlashInfoKarukera
Genres : zouk, zouk_retro, gwoka, lewoz, kompa, chatta, bouillon, calypso, biguine, mazurka
Ordre : Par genre, puis par artiste (alphabétique), puis par popularité
"""

CARIBBEAN_TRACKS = {
    # =========================================================================
    # ZOUK (Guadeloupe/Martinique - moderne)
    # =========================================================================
    "zouk": [
        # Al Lirvat (biguine/zouk)
        {"name": "La Chouval Bwa", "artists": ["Al Lirvat"]},
        
        # Battery Crémil (zouk love - Martinique)
        {"name": "Cé ou sèl", "artists": ["Battery Crémil"]},
        {"name": "Déception", "artists": ["Battery Crémil"]},
        {"name": "Jodi ya", "artists": ["Battery Crémil"]},
        {"name": "Lanmou Raid", "artists": ["Battery Crémil"]},
        {"name": "La Vérité", "artists": ["Battery Crémil"]},
        {"name": "Gran Nonm pa ka Wont", "artists": ["Battery Crémil"]},
        {"name": "Mwen bisoin la Pè", "artists": ["Battery Crémil"]},
        {"name": "Mwen envie ouè ou", "artists": ["Battery Crémil", "Marcel Chéry"]},
        {"name": "Tchè mwen cé ta ou", "artists": ["Battery Crémil"]},
        
        # Claudette Anderson
        {"name": "Désirs d'enfants", "artists": ["Claudette Anderson"]},
        {"name": "Ti Larivyè", "artists": ["Claudette Anderson"]},
        
        # Dominique Panol (Guadeloupe)
        {"name": "Bolotte", "artists": ["Dominique Panol"]},
        {"name": "Hugo", "artists": ["Dominique Panol"]},
        {"name": "Oubliyé", "artists": ["Dominique Panol"]},
        {"name": "Son sé love", "artists": ["Dominique Panol"]},
        {"name": "Soup' A Pié", "artists": ["Dominique Panol"]},
        {"name": "Tan'n Son An Nou", "artists": ["Dominique Panol"]},
        {"name": "Ti Kadance", "artists": ["Dominique Panol"]},
        
        # Exile One (kadans → zouk)
        {"name": "E Lo Lo", "artists": ["Exile One"]},
        {"name": "Lotion", "artists": ["Exile One"]},
        {"name": "Wilomele", "artists": ["Exile One"]},
        
        # Jeff Joe (Dominique - cadence-lypso → zouk)
        {"name": "Island Life", "artists": ["Jeff Joe"]},
        {"name": "Jouway Morning", "artists": ["Jeff Joe"]},
        {"name": "Sweet Dominica", "artists": ["Jeff Joe"]},
        
        # Jocelyne Labylle
        {"name": "Aimer d'amour", "artists": ["Jocelyne Labylle"]},
        {"name": "Amour Interdit", "artists": ["Jocelyne Labylle"]},
        {"name": "Palé Ba Mwen", "artists": ["Jocelyne Labylle"]},
        {"name": "Ti zwazo", "artists": ["Jocelyne Labylle"]},
        
        # Kassav'
        {"name": "Je Suis Né Créole", "artists": ["Kassav"]},
        {"name": "Kolé Séré", "artists": ["Kassav"]},
        {"name": "Mwen Malad Aw", "artists": ["Kassav"]},
        {"name": "Ou Lé Sa", "artists": ["Kassav"]},
        {"name": "Syé Bwa", "artists": ["Kassav"]},
        {"name": "Zouk La Sé Sel Medikaman Nou Ni", "artists": ["Kassav"]},
        {"name": "A Lot of Love", "artists": ["Kassav"]},
        
        # Mario Chicot (zouk - Martinique)
        {"name": "Emiyo", "artists": ["Mario Chicot"]},
        {"name": "Je l'aime", "artists": ["Mario Chicot"]},
        {"name": "Mélancolie", "artists": ["Mario Chicot"]},
        {"name": "Petite fille", "artists": ["Mario Chicot"]},
        {"name": "Pour la première fois", "artists": ["Mario Chicot"]},
        {"name": "Pouki mwen konsa", "artists": ["Mario Chicot"]},
        {"name": "Si Sé Kon Sa", "artists": ["Mario Chicot"]},
        
        # Marcé (Kassav' → zouk)
        {"name": "Gwo Ka", "artists": ["Marcé"]},
        {"name": "Léwòz a Marcé", "artists": ["Marcé"]},
        {"name": "Sové Doubout", "artists": ["Marcé"]},
        {"name": "Tambou ka sonné", "artists": ["Marcé"]},
        
        # Meryl (zouk - Martinique)
        {"name": "Mauvaise Élève", "artists": ["Meryl"]},
        
        # Ralph Thamar
        {"name": "Aïe", "artists": ["Ralph Thamar"]},
        {"name": "Éloge de la créole", "artists": ["Ralph Thamar"]},
        {"name": "Mové Jou", "artists": ["Ralph Thamar"]},
        {"name": "Yen a marre", "artists": ["Ralph Thamar"]},
        
        # Tatiana
        {"name": "Ce Soir", "artists": ["Tanya Saint-Val"]},
        {"name": "Coeur blessé", "artists": ["Tanya Saint-Val"]},
        {"name": "Hé Oh Hé", "artists": ["Tanya Saint-Val"]},
        {"name": "Si tu savais", "artists": ["Tanya Saint-Val"]},
        
        # Zouk Machine
        {"name": "Adieu Forain", "artists": ["Zouk Machine"]},
        {"name": "Maldon", "artists": ["Zouk Machine"]},
        {"name": "Siwo", "artists": ["Zouk Machine"]},
        {"name": "Zouk Machine", "artists": ["Zouk Machine"]},
        
        # Jean-Philippe Marthely
        {"name": "An Ba Chenn", "artists": ["Jean-Philippe Marthely"]},
        {"name": "Manjé Sal", "artists": ["Jean-Philippe Marthely"]},
        {"name": "Nou pé ké séparé", "artists": ["Jean-Philippe Marthely"]},
        
        # Princes Caroline
        {"name": "Doudou-a-Doudou", "artists": ["Princess Caroline"]},
        {"name": "Jou di Bondié", "artists": ["Princess Caroline"]},
        {"name": "Rêve ou réalité", "artists": ["Princess Caroline"]},
    ],

    # =========================================================================
    # ZOUK RETRO (Guadeloupe/Martinique - vintage)
    # =========================================================================
    "zouk_retro": [
        # Claudette Anderson (retro)
        {"name": "Bèl ti manmay", "artists": ["Claudette Anderson"]},
        {"name": "Kon yon sel", "artists": ["Claudette Anderson"]},
        
        # Edith Lefel
        {"name": "Amour Plastique", "artists": ["Edith Lefel"]},
        {"name": "Bébé", "artists": ["Edith Lefel"]},
        {"name": "Chez les Zoukettes", "artists": ["Edith Lefel"]},
        {"name": "Mouri pou mouri", "artists": ["Edith Lefel"]},
        {"name": "Toujou Rèd", "artists": ["Edith Lefel"]},
        
        # Gilles Floro
        {"name": "Ka Dansé", "artists": ["Gilles Floro"]},
        {"name": "Tibouchina", "artists": ["Gilles Floro"]},
        {"name": "Tout doux", "artists": ["Gilles Floro"]},
        
        # Jacob Desvarieux (solo - zouk retro)
        {"name": "Bi Yé", "artists": ["Jacob Desvarieux"]},
        {"name": "Douce France", "artists": ["Jacob Desvarieux"]},
        {"name": "Promenons-nous dans les bois", "artists": ["Jacob Desvarieux"]},
        
        # Patrick Saint-Eloi
        {"name": "Je ne sais plus", "artists": ["Patrick Saint-Eloi"]},
        {"name": "Lanmou Ké Nou", "artists": ["Patrick Saint-Eloi"]},
        {"name": "Si Je Savais", "artists": ["Patrick Saint-Eloi"]},
        {"name": "Sucré-salé", "artists": ["Patrick Saint-Eloi"]},
        {"name": "Vié ko", "artists": ["Patrick Saint-Eloi"]},
        {"name": "Sonjé", "artists": ["Patrick Saint-Eloi"]},
    ],

    # =========================================================================
    # GWOKA (Guadeloupe - traditionnel)
    # =========================================================================
    "gwoka": [
        # Akiyo (correction depuis chatta)
        {"name": "Akiyo an ba la", "artists": ["Akiyo"]},
        {"name": "Fraternité", "artists": ["Akiyo"]},
        {"name": "Mas a Mas", "artists": ["Akiyo"]},
        {"name": "Résistans", "artists": ["Akiyo"]},
        {"name": "Tèt a tèt", "artists": ["Akiyo"]},
        
        # Anzala
        {"name": "Léwòz", "artists": ["Ti Paris", "Anzala"]},
        
        # Carlos Nilson
        {"name": "Ka doubout", "artists": ["Carlos Nilson"]},
        {"name": "Kan nou té jenn", "artists": ["Carlos Nilson"]},
        {"name": "Péyi doubout", "artists": ["Carlos Nilson"]},
        {"name": "Sonjé", "artists": ["Carlos Nilson"]},
        
        # Dominique Coco (Guadeloupe)
        {"name": "An Rivé", "artists": ["Dominique Coco"]},
        {"name": "Clair Obscur", "artists": ["Dominique Coco", "Volt Face"]},
        {"name": "Eden", "artists": ["Dominique Coco"]},
        {"name": "Fow Rouvini", "artists": ["Dominique Coco"]},
        {"name": "If I Say Yes", "artists": ["Dominique Coco"]},
        {"name": "Mwen Sé Gwadloupéyen", "artists": ["Dominique Coco"]},
        {"name": "Soleil à Sion", "artists": ["Dominique Coco"]},
        {"name": "Soley La", "artists": ["Dominique Coco"]},
        {"name": "Zouké Light", "artists": ["Dominique Coco"]},
        
        # Dédé Saint-Prix (correction depuis bouillon)
        {"name": "Anba Tonnel", "artists": ["Dédé Saint-Prix"]},
        {"name": "Jou ouvè", "artists": ["Dédé Saint-Prix"]},
        
        # Gaoulé (correction depuis chatta)
        {"name": "Fos mas", "artists": ["Gaoulé"]},
        {"name": "Gaoulé mas", "artists": ["Gaoulé"]},
        {"name": "Péyi la ka chanté", "artists": ["Gaoulé"]},
        {"name": "Tanbou doubout", "artists": ["Gaoulé"]},
        
        # Jacob Desvarieux (gwoka)
        {"name": "Ka doubout", "artists": ["Jacob Desvarieux"]},
        
        # Kan'nida (correction depuis chatta)
        {"name": "Chanté pou péyi", "artists": ["Kan'nida"]},
        {"name": "Kanaval", "artists": ["Kan'nida"]},
        {"name": "Lévé doubout", "artists": ["Kan'nida"]},
        {"name": "Mas an listwa", "artists": ["Kan'nida"]},
        
        # Léona Gabriel
        {"name": "An fanm doubout", "artists": ["Léona Gabriel"]},
        {"name": "Soley kouché", "artists": ["Léona Gabriel"]},
        {"name": "Té ka chanté", "artists": ["Léona Gabriel"]},
        
        # Ti Paris
        {"name": "Léwòz", "artists": ["Ti Paris", "Anzala"]},
        
        # Voukoum (correction depuis chatta)
        {"name": "Doubout pou péyi", "artists": ["Voukoum"]},
        {"name": "Gwoka mas", "artists": ["Voukoum"]},
        {"name": "Mas doubout", "artists": ["Voukoum"]},
        {"name": "Voukoum tambou", "artists": ["Voukoum"]},
    ],

    # =========================================================================
    # LEWOZ (Guadeloupe - cérémoniel)
    # =========================================================================
    "lewoz": [
        # À développer - extraire des morceaux spécifiques de gwoka
        # Exemples : certains titres de Ti Paris, Anzala, Dominique Coco
    ],

    # =========================================================================
    # KOMPA (Haïti)
    # =========================================================================
    "kompa": [
        # BélO
        {"name": "Doudou-a-Doudou", "artists": ["BélO"]},
        {"name": "Manman", "artists": ["BélO"]},
        {"name": "Pa pati", "artists": ["BélO"]},
        {"name": "Revòlisyon", "artists": ["BélO"]},
        
        # Bel Accord
        {"name": "Lampe Lantern", "artists": ["Bel Accord"]},
        {"name": "Pa janm kite'm", "artists": ["Bel Accord"]},
        {"name": "Sentimental", "artists": ["Bel Accord"]},
        
        # Carimi
        {"name": "Ou beswen mwen", "artists": ["Carimi"]},
        {"name": "Ou pa bon pou mwen", "artists": ["Carimi"]},
        {"name": "Pwofesè", "artists": ["Carimi"]},
        {"name": "Rose", "artists": ["Carimi"]},
        {"name": "Tchaka", "artists": ["Carimi"]},
        
        # Djakout #1
        {"name": "Ayiti pa pèdi", "artists": ["Djakout #1"]},
        {"name": "Balance", "artists": ["Djakout #1"]},
        {"name": "Renmen w", "artists": ["Djakout #1"]},
        {"name": "Sans issue", "artists": ["Djakout #1"]},
        
        # Harmonik
        {"name": "Ba mwen yon ti bo", "artists": ["Harmonik"]},
        {"name": "Mwen pa vle", "artists": ["Harmonik"]},
        {"name": "Nati pa'm", "artists": ["Harmonik"]},
        {"name": "Pa kite'm", "artists": ["Harmonik"]},
        
        # Jean-Michel Jean-Louis
        {"name": "Angoisse", "artists": ["Jean-Michel Jean-Louis"]},
        {"name": "Dju", "artists": ["Jean-Michel Jean-Louis"]},
        {"name": "La Permission", "artists": ["Jean-Michel Jean-Louis"]},
        {"name": "Profité", "artists": ["Jean-Michel Jean-Louis"]},
        {"name": "Tilo", "artists": ["Jean-Michel Jean-Louis"]},
        
        # Les Aiglons
        {"name": "Détèwminasyon", "artists": ["Les Aiglons"]},
        {"name": "Konsyans", "artists": ["Les Aiglons"]},
        {"name": "Le Poids Lourd", "artists": ["Les Aiglons"]},
        
        # Mass Kanal (correction depuis chatta)
        {"name": "Chatta Mass Kanal", "artists": ["Mass Kanal"]},
        {"name": "Doubout Gwadloup", "artists": ["Mass Kanal"]},
        {"name": "Mas ka défilé", "artists": ["Mass Kanal"]},
        {"name": "Péyi a nou", "artists": ["Mass Kanal"]},
        
        # Naika
        {"name": "One Track Mind", "artists": ["Naika"]},
        
        # Nu-Look
        {"name": "Ou Pito", "artists": ["Nu-Look"]},
        {"name": "Ou toujou bèl", "artists": ["Nu-Look"]},
        {"name": "Se pou ou", "artists": ["Nu-Look"]},
        {"name": "Si m ta konnen", "artists": ["Nu-Look"]},
        
        # Sweet Micky
        {"name": "Ou Pito", "artists": ["Sweet Micky"]},
        
        # Meryl (kompa)
        {"name": "Jack Sparrow", "artists": ["Meryl"]},
        
        # T-Vice
        {"name": "Déréglé", "artists": ["T-Vice"]},
        {"name": "Fè yon bagay", "artists": ["T-Vice"]},
        {"name": "Kè m poko lib", "artists": ["T-Vice"]},
        {"name": "Kita Kita", "artists": ["T-Vice"]},
        {"name": "Meter Dife", "artists": ["T-Vice"]},
        {"name": "Ou fèm pè", "artists": ["T-Vice"]},
        
        # Tabou Combo
        {"name": "Aba Gouche", "artists": ["Tabou Combo"]},
        {"name": "Haiti", "artists": ["Tabou Combo"]},
        {"name": "Kamoken", "artists": ["Tabou Combo"]},
        {"name": "La Toto", "artists": ["Tabou Combo"]},
        {"name": "New York City", "artists": ["Tabou Combo"]},
        {"name": "Tabou Love", "artists": ["Tabou Combo"]},
        
        # Top Vice
        {"name": "Ayibobo", "artists": ["Top Vice"]},
        {"name": "Kè m poko lib", "artists": ["Top Vice"]},
        {"name": "Ou bèl", "artists": ["Top Vice"]},
        
        # Zin
        {"name": "Ou mèt ale", "artists": ["Zin"]},
        {"name": "Pa di'm adye", "artists": ["Zin"]},
        {"name": "Pran swen", "artists": ["Zin"]},
        {"name": "Kè m pa sote", "artists": ["Zin"]},
    ],

    # =========================================================================
    # CHATTA (Haïti - carnavalesque)
    # =========================================================================
    "chatta": [
        # À vérifier - la plupart des artistes ont été recatégorisés
        # Kan'nida, Gaoulé, Voukoum, Mass Kanal, Akiyo ont été déplacés
        # Seuls les vrais chatta haïtiens restent ici
    ],

    # =========================================================================
    # BOUILLON (Haïti - rapide)
    # =========================================================================
    "bouillon": [
        # Stellio (biguine, mais historiquement associé)
        {"name": "Biguine à St-Pierre", "artists": ["Stellio"]},
        
        # WCK (Windward Caribbean Kulture - Haïti)
        {"name": "Bouyon Massive", "artists": ["WCK"]},
        {"name": "Jing Ping", "artists": ["WCK"]},
        {"name": "Ring de Bell", "artists": ["WCK"]},
        {"name": "Willy the Man", "artists": ["WCK"]},
    ],

    # =========================================================================
    # CALYPSO (Caraïbes anglophones)
    # =========================================================================
    "calypso": [
        # Burning Flames (Grenade - soca/calypso)
        {"name": "Fete", "artists": ["Burning Flames"]},
        {"name": "Nah Let Go", "artists": ["Burning Flames"]},
        {"name": "Pump Me Up", "artists": ["Burning Flames"]},
        {"name": "Worky Worky", "artists": ["Burning Flames"]},
        
        # Jeff Joe (Dominique - cadence-lypso)
        {"name": "Island Life", "artists": ["Jeff Joe"]},
        {"name": "Jouway Morning", "artists": ["Jeff Joe"]},
        {"name": "Sweet Dominica", "artists": ["Jeff Joe"]},
    ],

    # =========================================================================
    # BIGUINE (Martinique/Guadeloupe)
    # =========================================================================
    "biguine": [
        # Al Lirvat (déplacé depuis bouillon)
        {"name": "Biguine à Gogo", "artists": ["Al Lirvat"]},
        
        # Stellio
        {"name": "Biguine à St-Pierre", "artists": ["Stellio"]},
    ],

    # =========================================================================
    # MAZURKA (Guadeloupe - traditionnel)
    # =========================================================================
    "mazurka": [
        # Al Lirvat
        {"name": "La Chouval Bwa", "artists": ["Al Lirvat"]},
        {"name": "Mazurka créole", "artists": ["Al Lirvat"]},
    ],
}

# =========================================================================
# BLOCK GENRES - Répartition des genres par bloc temporel
# =========================================================================
BLOCK_GENRES = {
    "night":   ["zouk_retro", "gwoka", "bouillon"],      # Ambiance calme/tradition
    "morning": ["zouk", "gwoka", "biguine"],              # Énergie modérée
    "midday":  ["kompa", "zouk", "calypso"],            # Dynamique
    "evening": ["gwoka", "zouk", "kompa", "mazurka"],    # Varié
}
