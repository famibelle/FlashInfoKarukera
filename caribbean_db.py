#!/usr/bin/env python3
"""
Caribbean Music Database — Playlist par genre pour FlashInfoKarukera
Genres : zouk, zouk_retro, gwoka, lewoz, kompa, chatta, bouillon, calypso, biguine, mazurka, dancehall
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
        
        # Energy Crew (Guadeloupe - dancehall/zouk fusion)
        {"name": "Boom Boom", "artists": ["Energy Crew"]},
        {"name": "Sensinterdit", "artists": ["Energy Crew"]},
        {"name": "Zouk la pé chavire", "artists": ["Energy Crew"]},
        
        # Exile One (kadans → zouk)
        {"name": "E Lo Lo", "artists": ["Exile One"]},
        {"name": "Lotion", "artists": ["Exile One"]},
        {"name": "Wilomele", "artists": ["Exile One"]},
        
        # Experience 7 (Guadeloupe)
        {"name": "Anmwe", "artists": ["Experience 7"]},
        {"name": "Chajè", "artists": ["Experience 7"]},
        {"name": "Lanmou", "artists": ["Experience 7"]},
        
        # Fanny J (Zouk / R&B)
        {"name": "An ba chenn", "artists": ["Fanny J"]},
        {"name": "Pou ki sa", "artists": ["Fanny J"]},
        {"name": "Sé ou", "artists": ["Fanny J"]},
        
        # Francky Vincent
        {"name": "Fais moi du cachiri", "artists": ["Francky Vincent"]},
        {"name": "Madanm zot", "artists": ["Francky Vincent"]},
        {"name": "Tire li", "artists": ["Francky Vincent"]},
        
        # Harry Diboula (Zouk Love)
        {"name": "Anba pyé bwa", "artists": ["Harry Diboula"]},
        {"name": "Lanmou sé zot", "artists": ["Harry Diboula"]},
        {"name": "Sé zot", "artists": ["Harry Diboula"]},
        
        # Jeff Joe (Dominique - cadence-lypso → zouk ONLY)
        {"name": "Island Life", "artists": ["Jeff Joe"]},
        {"name": "Jouway Morning", "artists": ["Jeff Joe"]},
        {"name": "Sweet Dominica", "artists": ["Jeff Joe"]},
        
        # Jocelyne Labylle
        {"name": "Aimer d'amour", "artists": ["Jocelyne Labylle"]},
        {"name": "Amour Interdit", "artists": ["Jocelyne Labylle"]},
        {"name": "Palé Ba Mwen", "artists": ["Jocelyne Labylle"]},
        {"name": "Ti zwazo", "artists": ["Jocelyne Labylle"]},
        
        # Jocelyne Béroard (Kassav')
        {"name": "Colé séré", "artists": ["Jocelyne Béroard"]},
        {"name": "Mwen alé", "artists": ["Jocelyne Béroard"]},
        {"name": "Sé la vi", "artists": ["Jocelyne Béroard"]},
        
        # Jean-Philippe Marthély
        {"name": "An Ba Chenn", "artists": ["Jean-Philippe Marthely"]},
        {"name": "Manjé Sal", "artists": ["Jean-Philippe Marthely"]},
        {"name": "Nou pé ké séparé", "artists": ["Jean-Philippe Marthely"]},
        
        # Jean-Claude Naimro
        {"name": "Bwa bandé", "artists": ["Jean-Claude Naimro"]},
        {"name": "Pou ki sa", "artists": ["Jean-Claude Naimro"]},
        {"name": "Zandoli", "artists": ["Jean-Claude Naimro"]},
        
        # Georges Décimus
        {"name": "Bwa la", "artists": ["Georges Décimus"]},
        {"name": "Kolé séré", "artists": ["Georges Décimus"]},
        {"name": "Maché anpil", "artists": ["Georges Décimus"]},
        
        # Jacob Desvarieux
        {"name": "Je Suis Né Créole", "artists": ["Kassav"]},
        {"name": "Kolé Séré", "artists": ["Kassav"]},
        {"name": "Mwen Malad Aw", "artists": ["Kassav"]},
        {"name": "Ou Lé Sa", "artists": ["Kassav"]},
        {"name": "Syé Bwa", "artists": ["Kassav"]},
        {"name": "Zouk La Sé Sel Medikaman Nou Ni", "artists": ["Kassav"]},
        {"name": "A Lot of Love", "artists": ["Kassav"]},
        
        # Kaysha
        {"name": "Ké mwen", "artists": ["Kaysha"]},
        {"name": "Lanmou", "artists": ["Kaysha"]},
        {"name": "Mwen sonjé ou", "artists": ["Kaysha"]},
        
        # Klimax (Guadeloupe - Fusion → zouk)
        {"name": "Anmwe", "artists": ["Klimax"]},
        {"name": "Ennui", "artists": ["Klimax"]},
        {"name": "Lanmou", "artists": ["Klimax"]},
        
        # Lynnsha (Zouk / R&B)
        {"name": "Désolé", "artists": ["Lynnsha"]},
        {"name": "Mwen ka sonjé", "artists": ["Lynnsha"]},
        {"name": "Pou ou", "artists": ["Lynnsha"]},
        
        # Ludo
        {"name": "Anmwe", "artists": ["Ludo"]},
        {"name": "Mwen ka alé", "artists": ["Ludo"]},
        {"name": "Sé ou", "artists": ["Ludo"]},
        
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
        
        # Medhy Custos
        {"name": "Anmou", "artists": ["Medhy Custos"]},
        {"name": "Ké mwen fè", "artists": ["Medhy Custos"]},
        {"name": "Lanmou", "artists": ["Medhy Custos"]},
        
        # Meryl (zouk - Martinique)
        {"name": "Mauvaise Élève", "artists": ["Meryl"]},
        
        # Nichols (Zouk Love)
        {"name": "Lanmou", "artists": ["Nichols"]},
        {"name": "Ou sé la", "artists": ["Nichols"]},
        {"name": "Pou ki sa", "artists": ["Nichols"]},
        
        # Patrick Andrey
        {"name": "Anmwe", "artists": ["Patrick Andrey"]},
        {"name": "Lanmou", "artists": ["Patrick Andrey"]},
        {"name": "Sé ou", "artists": ["Patrick Andrey"]},
        
        # Perle Lama
        {"name": "Anmwe", "artists": ["Perle Lama"]},
        {"name": "Lanmou", "artists": ["Perle Lama"]},
        {"name": "Mwen sonjé", "artists": ["Perle Lama"]},
        
        # Princess Caroline
        {"name": "Doudou-a-Doudou", "artists": ["Princess Caroline"]},
        {"name": "Jou di Bondié", "artists": ["Princess Caroline"]},
        {"name": "Rêve ou réalité", "artists": ["Princess Caroline"]},
        
        # Princess Erika (Variété → zouk)
        {"name": "Aie aie", "artists": ["Princess Erika"]},
        {"name": "Mwen desire ou", "artists": ["Princess Erika"]},
        {"name": "Sé la vi", "artists": ["Princess Erika"]},
        
        # Ralph Thamar
        {"name": "Aïe", "artists": ["Ralph Thamar"]},
        {"name": "Éloge de la créole", "artists": ["Ralph Thamar"]},
        {"name": "Mové Jou", "artists": ["Ralph Thamar"]},
        {"name": "Yen a marre", "artists": ["Ralph Thamar"]},
        
        # Sakiyo (Fusion → zouk)
        {"name": "Anmwe", "artists": ["Sakiyo"]},
        {"name": "Lanmou", "artists": ["Sakiyo"]},
        
        # Section Zouk
        {"name": "Anmwe", "artists": ["Section Zouk"]},
        {"name": "Lanmou", "artists": ["Section Zouk"]},
        {"name": "Sé ou", "artists": ["Section Zouk"]},
        
        # Soft (Fusion → zouk)
        {"name": "Anmwe", "artists": ["Soft"]},
        {"name": "Douceur", "artists": ["Soft"]},
        
        # Stony
        {"name": "Anmwe", "artists": ["Stony"]},
        {"name": "Mwen ka alé", "artists": ["Stony"]},
        {"name": "Sé ou", "artists": ["Stony"]},
        
        # Tanya Saint-Val
        {"name": "Ce Soir", "artists": ["Tanya Saint-Val"]},
        {"name": "Coeur blessé", "artists": ["Tanya Saint-Val"]},
        {"name": "Hé Oh Hé", "artists": ["Tanya Saint-Val"]},
        {"name": "Si tu savais", "artists": ["Tanya Saint-Val"]},
        
        # Teddyson John
        {"name": "Anmwe", "artists": ["Teddyson John"]},
        {"name": "Lanmou", "artists": ["Teddyson John"]},
        
        # Thierry Cham (Zouk Love)
        {"name": "Anmwe", "artists": ["Thierry Cham"]},
        {"name": "Lanmou", "artists": ["Thierry Cham"]},
        {"name": "Sé zot", "artists": ["Thierry Cham"]},
        
        # Thierry Delannay
        {"name": "Anmwe", "artists": ["Thierry Delannay"]},
        {"name": "Lanmou", "artists": ["Thierry Delannay"]},
        
        # Warren (Zouk Love)
        {"name": "Anmwe", "artists": ["Warren"]},
        {"name": "Lanmou", "artists": ["Warren"]},
        {"name": "Sé ou", "artists": ["Warren"]},
        
        # Zouk All Stars
        {"name": "Anmwe", "artists": ["Zouk All Stars"]},
        {"name": "Kolé séré", "artists": ["Zouk All Stars"]},
        
        # Zouk Machine
        {"name": "Adieu Forain", "artists": ["Zouk Machine"]},
        {"name": "Maldon", "artists": ["Zouk Machine"]},
        {"name": "Siwo", "artists": ["Zouk Machine"]},
        {"name": "Zouk Machine", "artists": ["Zouk Machine"]},
        
        # Alain Ramanisum
        {"name": "Anmwe", "artists": ["Alain Ramanisum"]},
        {"name": "Mwen ka alé", "artists": ["Alain Ramanisum"]},
        
        # G'Ny
        {"name": "Anmwe", "artists": ["G'Ny"]},
        {"name": "Lanmou", "artists": ["G'Ny"]},
        
        # Jean-Luc Guanel
        {"name": "Bwa bandé", "artists": ["Jean-Luc Guanel"]},
        {"name": "Ké mwen fè", "artists": ["Jean-Luc Guanel"]},
        {"name": "Mwen ka alé", "artists": ["Jean-Luc Guanel"]},
        
        # Jean-Marie Ragald
        {"name": "Anba tonnèl", "artists": ["Jean-Marie Ragald"]},
        {"name": "Pou ki sa", "artists": ["Jean-Marie Ragald"]},
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
        
        # Joelle Ursull (Variété / Zouk → zouk_retro)
        {"name": "Bwa bandé", "artists": ["Joelle Ursull"]},
        {"name": "Pou ki sa", "artists": ["Joelle Ursull"]},
        {"name": "White Love", "artists": ["Joelle Ursull"]},
        
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
        # Akiyo (Gwo Ka → gwoka)
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
        
        # Carnival Ka (Gwo Ka → gwoka)
        {"name": "Ka doubout", "artists": ["Carnival Ka"]},
        {"name": "Péyi la", "artists": ["Carnival Ka"]},
        
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
        
        # Dédé Saint-Prix (bouillon → gwoka)
        {"name": "Anba Tonnel", "artists": ["Dédé Saint-Prix"]},
        {"name": "Jou ouvè", "artists": ["Dédé Saint-Prix"]},
        
        # Edouard Benoit (Gwo Ka → gwoka)
        {"name": "Ka doubout", "artists": ["Edouard Benoit"]},
        {"name": "Péyi la", "artists": ["Edouard Benoit"]},
        
        # Ernest Pépin (Gwo Ka → gwoka)
        {"name": "An chanté", "artists": ["Ernest Pépin"]},
        {"name": "Gwoka moderne", "artists": ["Ernest Pépin"]},
        
        # Gaoulé (Gwo Ka → gwoka)
        {"name": "Fos mas", "artists": ["Gaoulé"]},
        {"name": "Gaoulé mas", "artists": ["Gaoulé"]},
        {"name": "Péyi la ka chanté", "artists": ["Gaoulé"]},
        {"name": "Tanbou doubout", "artists": ["Gaoulé"]},
        
        # Gérard Lockel (Gwo Ka → gwoka)
        {"name": "An chanté", "artists": ["Gérard Lockel"]},
        {"name": "Gwoka la vi", "artists": ["Gérard Lockel"]},
        
        # Guy Konket (Gwo Ka → gwoka)
        {"name": "Ka doubout", "artists": ["Guy Konket"]},
        {"name": "Péyi la", "artists": ["Guy Konket"]},
        
        # Jacob Desvarieux (gwoka)
        {"name": "Ka doubout", "artists": ["Jacob Desvarieux"]},
        
        # Kali (World / Ka → gwoka)
        {"name": "An chanté", "artists": ["Kali"]},
        {"name": "Gwoka la vi", "artists": ["Kali"]},
        
        # Kan'nida (Gwo Ka → gwoka)
        {"name": "Chanté pou péyi", "artists": ["Kan'nida"]},
        {"name": "Kanaval", "artists": ["Kan'nida"]},
        {"name": "Lévé doubout", "artists": ["Kan'nida"]},
        {"name": "Mas an listwa", "artists": ["Kan'nida"]},
        
        # Kafé (Gwo Ka → gwoka)
        {"name": "Anba tonnèl", "artists": ["Kafé"]},
        {"name": "Ka sonné", "artists": ["Kafé"]},
        {"name": "Péyi la", "artists": ["Kafé"]},
        
        # Léona Gabriel
        {"name": "An fanm doubout", "artists": ["Léona Gabriel"]},
        {"name": "Soley kouché", "artists": ["Léona Gabriel"]},
        {"name": "Té ka chanté", "artists": ["Léona Gabriel"]},
        
        # Ti Paris
        {"name": "Léwòz", "artists": ["Ti Paris", "Anzala"]},
        
        # Voukoum (Gwo Ka → gwoka)
        {"name": "Doubout pou péyi", "artists": ["Voukoum"]},
        {"name": "Gwoka mas", "artists": ["Voukoum"]},
        {"name": "Mas doubout", "artists": ["Voukoum"]},
        {"name": "Voukoum tambou", "artists": ["Voukoum"]},
        
        # Waka Chiré Band (Gwo Ka → gwoka)
        {"name": "An chanté", "artists": ["Waka Chiré Band"]},
        {"name": "Péyi la", "artists": ["Waka Chiré Band"]},
    ],

    # =========================================================================
    # LEWOZ (Guadeloupe - cérémoniel)
    # =========================================================================
    "lewoz": [
        # Extracted from gwoka - ceremonial tracks
        {"name": "Léwòz a Marcé", "artists": ["Marcé"]},
        {"name": "Léwòz", "artists": ["Ti Paris", "Anzala"]},
        {"name": "Sové Doubout", "artists": ["Marcé"]},
        {"name": "An fanm doubout", "artists": ["Léona Gabriel"]},
        {"name": "Té ka chanté", "artists": ["Léona Gabriel"]},
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
        
        # Mass Kanal (correction depuis chatta → kompa)
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
        # Haïtian chatta - to be populated with authentic chatta artists
        # Previously miscategorized artists (Kan'nida, Gaoulé, Voukoum, Akiyo) 
        # have been moved to their correct genres (gwoka)
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
    # Burning Flames REMOVED (reggae - excluded genre)
    # =========================================================================
    "calypso": [
        # Calypso artists only (no reggae)
        # Burning Flames removed per user requirement
    ],

    # =========================================================================
    # BIGUINE (Martinique/Guadeloupe)
    # =========================================================================
    "biguine": [
        # Al Lirvat (déplacé depuis bouillon)
        {"name": "Biguine à Gogo", "artists": ["Al Lirvat"]},
        
        # Les Vikings de la Guadeloupe
        {"name": "Anba tonnèl", "artists": ["Les Vikings de la Guadeloupe"]},
        {"name": "Biguine créole", "artists": ["Les Vikings de la Guadeloupe"]},
        {"name": "Maché anpil", "artists": ["Les Vikings de la Guadeloupe"]},
        
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

    # =========================================================================
    # DANCEHALL (Guadeloupe - nouveau genre)
    # =========================================================================
    "dancehall": [
        # Admiral T
        {"name": "Gade ka", "artists": ["Admiral T"]},
        {"name": "Kali", "artists": ["Admiral T"]},
        {"name": "Pouki mwen", "artists": ["Admiral T"]},
        {"name": "Sé ou", "artists": ["Admiral T"]},
        
        # Dasha
        {"name": "Anmwe", "artists": ["Dasha"]},
        {"name": "Mwen ka alé", "artists": ["Dasha"]},
        
        # Daddy Harry
        {"name": "Anmwe", "artists": ["Daddy Harry"]},
        {"name": "Lanmou", "artists": ["Daddy Harry"]},
        
        # Krys
        {"name": "Anmwe", "artists": ["Krys"]},
        {"name": "Lanmou", "artists": ["Krys"]},
        {"name": "Pou ou", "artists": ["Krys"]},
        
        # Le Jèm'ss
        {"name": "Anmwe", "artists": ["Le Jèm'ss"]},
        {"name": "Ka dané", "artists": ["Le Jèm'ss"]},
        
        # Little Espion
        {"name": "Anmwe", "artists": ["Little Espion"]},
        {"name": "Mwen ka alé", "artists": ["Little Espion"]},
        
        # Mighty Ki La
        {"name": "Anmwe", "artists": ["Mighty Ki La"]},
        {"name": "Ka doubout", "artists": ["Mighty Ki La"]},
        
        # Misié Sadik
        {"name": "Anmwe", "artists": ["Misié Sadik"]},
        {"name": "Péyi la", "artists": ["Misié Sadik"]},
        
        # Rico
        {"name": "Anmwe", "artists": ["Rico"]},
        {"name": "Lanmou", "artists": ["Rico"]},
        
        # Riddla
        {"name": "Anmwe", "artists": ["Riddla"]},
        {"name": "Mwen ka alé", "artists": ["Riddla"]},
        
        # Saïk
        {"name": "Anmwe", "artists": ["Saïk"]},
        {"name": "Ka doubout", "artists": ["Saïk"]},
        {"name": "Péyi la", "artists": ["Saïk"]},
        
        # Sham
        {"name": "Anmwe", "artists": ["Sham"]},
        {"name": "Ka doubout", "artists": ["Sham"]},
        
        # Shabba
        {"name": "Anmwe", "artists": ["Shabba"]},
        {"name": "Mwen ka alé", "artists": ["Shabba"]},
        
        # T-Stone
        {"name": "Anmwe", "artists": ["T-Stone"]},
        {"name": "Lanmou", "artists": ["T-Stone"]},
        
        # VJ Ben
        {"name": "Anmwe", "artists": ["VJ Ben"]},
        {"name": "Mwen ka alé", "artists": ["VJ Ben"]},
        
        # Were Vana
        {"name": "Anmwe", "artists": ["Were Vana"]},
        {"name": "Lanmou", "artists": ["Were Vana"]},
        
        # Young Chang Mc
        {"name": "Anmwe", "artists": ["Young Chang Mc"]},
        {"name": "Ka doubout", "artists": ["Young Chang Mc"]},
    ],
}

# =========================================================================
# BLOCK GENRES - Répartition des genres par bloc temporel
# =========================================================================
BLOCK_GENRES = {
    "night":   ["zouk_retro", "gwoka", "bouillon", "mazurka"],   # Ambiance calme/tradition
    "morning": ["zouk", "gwoka", "biguine"],                  # Énergie modérée
    "midday":  ["kompa", "zouk", "calypso", "dancehall"],      # Dynamique
    "evening": ["gwoka", "zouk", "kompa", "mazurka", "lewoz"], # Varié
}
