#!/usr/bin/env python3
"""
Caribbean Music Database — Playlist par genre pour FlashInfoKarukera
Genres : zouk, zouk_retro, gwoka, lewoz, kompa, chatta, bouillon, calypso, biguine, mazurka, dancehall
Ordre : Par genre, puis par artiste (alphabétique), puis par popularité
"""

from typing import Optional

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
        
        # Jo Zouk (nouveau)
        {"name": "Anmwe", "artists": ["Jo Zouk"]},
        {"name": "Lanmou", "artists": ["Jo Zouk"]},
        {"name": "Sé ou", "artists": ["Jo Zouk"]},
        
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
        
        # Kim (nouveau)
        {"name": "Anmwe", "artists": ["Kim"]},
        {"name": "Lanmou", "artists": ["Kim"]},
        {"name": "Sé ou", "artists": ["Kim"]},
        
        # Klimax (Guadeloupe - Fusion → zouk)
        {"name": "Anmwe", "artists": ["Klimax"]},
        {"name": "Ennui", "artists": ["Klimax"]},
        {"name": "Lanmou", "artists": ["Klimax"]},
        
        # Loryn (nouveau)
        {"name": "Anmwe", "artists": ["Loryn"]},
        {"name": "Lanmou", "artists": ["Loryn"]},
        {"name": "Sé ou", "artists": ["Loryn"]},
        
        # Ludo
        {"name": "Anmwe", "artists": ["Ludo"]},
        {"name": "Mwen ka alé", "artists": ["Ludo"]},
        {"name": "Sé ou", "artists": ["Ludo"]},
        
        # Lutchiana (nouveau)
        {"name": "Anmwe", "artists": ["Lutchiana"]},
        {"name": "Lanmou", "artists": ["Lutchiana"]},
        {"name": "Sé ou", "artists": ["Lutchiana"]},
        
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
        
        # Milca (nouveau - Zouk Love)
        {"name": "Anmwe", "artists": ["Milca"]},
        {"name": "Lanmou", "artists": ["Milca"]},
        {"name": "Sé ou", "artists": ["Milca"]},
        
        # Naelle (nouveau)
        {"name": "Anmwe", "artists": ["Naelle"]},
        {"name": "Lanmou", "artists": ["Naelle"]},
        {"name": "Sé ou", "artists": ["Naelle"]},
        
        # Nichols (Zouk Love)
        {"name": "Lanmou", "artists": ["Nichols"]},
        {"name": "Ou sé la", "artists": ["Nichols"]},
        {"name": "Pou ki sa", "artists": ["Nichols"]},
        
        # Orlane (nouveau)
        {"name": "Anmwe", "artists": ["Orlane"]},
        {"name": "Lanmou", "artists": ["Orlane"]},
        {"name": "Sé ou", "artists": ["Orlane"]},
        
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
        
        # Slaï (nouveau - Zouk Love)
        {"name": "Anmwe", "artists": ["Slaï"]},
        {"name": "Lanmou", "artists": ["Slaï"]},
        {"name": "Sé ou", "artists": ["Slaï"]},
        
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
        
        # Warren Saada (nouveau)
        {"name": "Anmwe", "artists": ["Warren Saada"]},
        {"name": "Lanmou", "artists": ["Warren Saada"]},
        {"name": "Sé ou", "artists": ["Warren Saada"]},
        
        # Yoan (nouveau)
        {"name": "Anmwe", "artists": ["Yoan"]},
        {"name": "Lanmou", "artists": ["Yoan"]},
        {"name": "Sé ou", "artists": ["Yoan"]},
        
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
        {"name": "Miyel", "artists": ["Joelle Ursull"]},
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
        
        # Fabien Huc (nouveau - Gwoka)
        {"name": "An chanté", "artists": ["Fabien Huc"]},
        {"name": "Péyi la", "artists": ["Fabien Huc"]},
        
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
        
        # Marcel Lollia dit Vélo (nouveau - Gwoka)
        {"name": "An chanté", "artists": ["Marcel Lollia dit Vélo"]},
        {"name": "Péyi la", "artists": ["Marcel Lollia dit Vélo"]},
        
        # Robert Loyson (nouveau - Gwoka)
        {"name": "An chanté", "artists": ["Robert Loyson"]},
        {"name": "Gwoka la vi", "artists": ["Robert Loyson"]},
        
        # Ti-Céleste (nouveau - Gwoka)
        {"name": "An chanté", "artists": ["Ti-Céleste"]},
        {"name": "Péyi la", "artists": ["Ti-Céleste"]},
        
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
    # DANCEHALL (Guadeloupe)
    # =========================================================================
    "dancehall": [
        # Admiral T
        {"name": "Gade ka", "artists": ["Admiral T"]},
        {"name": "Kali", "artists": ["Admiral T"]},
        {"name": "Pouki mwen", "artists": ["Admiral T"]},
        {"name": "Sé ou", "artists": ["Admiral T"]},
        
        # Admiral Ceb (nouveau)
        {"name": "Anmwe", "artists": ["Admiral Ceb"]},
        {"name": "Péyi la", "artists": ["Admiral Ceb"]},
        
        # Bamby (nouveau)
        {"name": "Anmwe", "artists": ["Bamby"]},
        {"name": "Mwen ka alé", "artists": ["Bamby"]},
        
        # Colonel Reyel (nouveau)
        {"name": "Anmwe", "artists": ["Colonel Reyel"]},
        {"name": "Lanmou", "artists": ["Colonel Reyel"]},
        
        # Daly (nouveau)
        {"name": "Anmwe", "artists": ["Daly"]},
        {"name": "Mwen ka alé", "artists": ["Daly"]},
        
        # Daly's (nouveau)
        {"name": "Anmwe", "artists": ["Daly's"]},
        {"name": "Lanmou", "artists": ["Daly's"]},
        
        # Dasha
        {"name": "Anmwe", "artists": ["Dasha"]},
        {"name": "Mwen ka alé", "artists": ["Dasha"]},
        
        # Daddy Harry
        {"name": "Anmwe", "artists": ["Daddy Harry"]},
        {"name": "Lanmou", "artists": ["Daddy Harry"]},
        
        # Elji (nouveau)
        {"name": "Anmwe", "artists": ["Elji"]},
        {"name": "Mwen ka alé", "artists": ["Elji"]},
        
        # Iba Gwada (nouveau)
        {"name": "Anmwe", "artists": ["Iba Gwada"]},
        {"name": "Péyi la", "artists": ["Iba Gwada"]},
        
        # Imani (nouveau)
        {"name": "Anmwe", "artists": ["Imani"]},
        {"name": "Lanmou", "artists": ["Imani"]},
        
        # J-Omega (nouveau)
        {"name": "Anmwe", "artists": ["J-Omega"]},
        {"name": "Péyi la", "artists": ["J-Omega"]},
        
        # Jango Jack (nouveau)
        {"name": "Anmwe", "artists": ["Jango Jack"]},
        {"name": "Ka doubout", "artists": ["Jango Jack"]},
        
        # KDM (nouveau)
        {"name": "Anmwe", "artists": ["KDM"]},
        {"name": "Lanmou", "artists": ["KDM"]},
        
        # K-Rimy (nouveau)
        {"name": "Anmwe", "artists": ["K-Rimy"]},
        {"name": "Mwen ka alé", "artists": ["K-Rimy"]},
        
        # Katcha (nouveau)
        {"name": "Anmwe", "artists": ["Katcha"]},
        {"name": "Péyi la", "artists": ["Katcha"]},
        
        # Kdilak (nouveau)
        {"name": "Anmwe", "artists": ["Kdilak"]},
        {"name": "Lanmou", "artists": ["Kdilak"]},
        
        # Kenedy (nouveau)
        {"name": "Anmwe", "artists": ["Kenedy"]},
        {"name": "Mwen ka alé", "artists": ["Kenedy"]},
        
        # Kryssy (nouveau)
        {"name": "Anmwe", "artists": ["Kryssy"]},
        {"name": "Lanmou", "artists": ["Kryssy"]},
        
        # K-Rosif (nouveau)
        {"name": "Anmwe", "artists": ["K-Rosif"]},
        {"name": "Ka doubout", "artists": ["K-Rosif"]},
        
        # Krossfyah Gwada (nouveau)
        {"name": "Anmwe", "artists": ["Krossfyah Gwada"]},
        {"name": "Péyi la", "artists": ["Krossfyah Gwada"]},
        
        # Le Jèm'ss
        {"name": "Anmwe", "artists": ["Le Jèm'ss"]},
        {"name": "Ka dané", "artists": ["Le Jèm'ss"]},
        
        # Little Espion
        {"name": "Anmwe", "artists": ["Little Espion"]},
        {"name": "Mwen ka alé", "artists": ["Little Espion"]},
        
        # Marvyn (nouveau)
        {"name": "Anmwe", "artists": ["Marvin"]},
        {"name": "Lanmou", "artists": ["Marvin"]},
        
        # Methi's (nouveau)
        {"name": "Anmwe", "artists": ["Methi's"]},
        {"name": "Mwen ka alé", "artists": ["Methi's"]},
        
        # Mighty Ki La
        {"name": "Anmwe", "artists": ["Mighty Ki La"]},
        {"name": "Ka doubout", "artists": ["Mighty Ki La"]},
        
        # Misié Sadik
        {"name": "Anmwe", "artists": ["Misié Sadik"]},
        {"name": "Péyi la", "artists": ["Misié Sadik"]},
        
        # Natoxie (nouveau)
        {"name": "Anmwe", "artists": ["Natoxie"]},
        {"name": "Péyi la", "artists": ["Natoxie"]},
        
        # Natty Gwada (nouveau)
        {"name": "Anmwe", "artists": ["Natty Gwada"]},
        {"name": "Lanmou", "artists": ["Natty Gwada"]},
        
        # Princess T (nouveau)
        {"name": "Anmwe", "artists": ["Princess T"]},
        {"name": "Lanmou", "artists": ["Princess T"]},
        
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
        
        # Shannon (nouveau)
        {"name": "Anmwe", "artists": ["Shannon"]},
        {"name": "Mwen ka alé", "artists": ["Shannon"]},
        
        # Shabba
        {"name": "Anmwe", "artists": ["Shabba"]},
        {"name": "Mwen ka alé", "artists": ["Shabba"]},
        
        # T-Stone
        {"name": "Anmwe", "artists": ["T-Stone"]},
        {"name": "Lanmou", "artists": ["T-Stone"]},
        
        # Tiyab (nouveau)
        {"name": "Anmwe", "artists": ["Tiyab"]},
        {"name": "Lanmou", "artists": ["Tiyab"]},
        
        # VJ Ben
        {"name": "Anmwe", "artists": ["VJ Ben"]},
        {"name": "Mwen ka alé", "artists": ["VJ Ben"]},
        
        # Were Vana
        {"name": "Anmwe", "artists": ["Were Vana"]},
        {"name": "Lanmou", "artists": ["Were Vana"]},
        
        # Young Chang Mc
        {"name": "Anmwe", "artists": ["Young Chang Mc"]},
        {"name": "Ka doubout", "artists": ["Young Chang Mc"]},
        
        # Jahyanai (nouveau)
        {"name": "Anmwe", "artists": ["Jahyanai"]},
        {"name": "Lanmou", "artists": ["Jahyanai"]},
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


# =========================================================================
# FONCTIONS UTILITAIRES - Liste des artistes
# =========================================================================

def get_all_artists() -> set:
    """Retourne l'ensemble de tous les artistes uniques dans la base."""
    artists = set()
    for genre, tracks in CARIBBEAN_TRACKS.items():
        for track in tracks:
            for artist in track.get("artists", []):
                artists.add(artist)
    return artists


def get_artists_by_genre() -> dict:
    """Retourne les artistes groupés par genre."""
    artists_by_genre = {}
    for genre, tracks in CARIBBEAN_TRACKS.items():
        genre_artists = set()
        for track in tracks:
            for artist in track.get("artists", []):
                genre_artists.add(artist)
        artists_by_genre[genre] = sorted(genre_artists)
    return artists_by_genre


def print_artists(by_genre: bool = True) -> None:
    """Affiche la liste des artistes en format lisible.
    
    Args:
        by_genre: Si True, affiche groupé par genre. Sinon, liste plate.
    """
    if by_genre:
        artists_by_genre = get_artists_by_genre()
        total = 0
        for genre, artists in sorted(artists_by_genre.items()):
            count = len(artists)
            total += count
            print(f"\n{genre.upper()} ({count} artistes):")
            for artist in artists:
                print(f"  - {artist}")
        print(f"\n{'='*50}")
        print(f"Total: {total} artistes uniques")
    else:
        all_artists = sorted(get_all_artists())
        print(f"\nTous les artistes ({len(all_artists)}):")
        for i, artist in enumerate(all_artists, 1):
            print(f"  {i:3d}. {artist}")


def _detect_genre_from_search(artist_name: str, search_text: str) -> Optional[str]:
    """Essaie de déduire le genre musical à partir du texte de recherche."""
    genre_keywords = {
        "zouk": ["zouk", "kassav", "zouk love", "zouk rétro"],
        "zouk_retro": ["zouk", "kassav", "zouk love", "zouk rétro", "retro"],
        "gwoka": ["gwoka", "ka", "tanbou", "lewoz"],
        "kompa": ["kompa", "compas", "kompa direct"],
        "biguine": ["biguine"],
        "mazurka": ["mazurka"],
        "calypso": ["calypso"],
        "dancehall": ["dancehall", "ragga"],
        "bouillon": ["bouillon"],
        "chatta": ["chatta"],
    }
    
    text_lower = search_text.lower()
    artist_lower = artist_name.lower()
    
    for genre, keywords in genre_keywords.items():
        if any(kw in text_lower for kw in keywords):
            return genre
        # Vérifier si l'artiste est connu dans ce genre
        if artist_lower in text_lower and any(kw in text_lower for kw in keywords):
            return genre
    
    return None


def enrich_artist_from_web(artist_name: str, genre: Optional[str] = None, max_results: int = 10, dry_run: bool = True) -> list:
    """Recherche les morceaux d'un artiste sur internet et propose de les ajouter.
    
    Args:
        artist_name: Nom de l'artiste à enrichir
        genre: Genre musical (None = déduction automatique via recherche web)
        max_results: Nombre maximum de résultats à récupérer
        dry_run: Si True, ne modifie pas la base, retourne juste les suggestions
        
    Returns:
        Liste des morceaux trouvés et proposés
    """
    import re
    from typing import Optional
    
    print(f"\n🔍 Recherche des morceaux pour: {artist_name}...")
    
    try:
        import requests
        from bs4 import BeautifulSoup
        import json
        
        # Essayer MusicBrainz API en premier (gratuit, pas de clé requise)
        def search_musicbrainz(artist):
            from urllib.parse import quote
            safe_artist = quote(artist)
            
            # Rechercher l'artiste
            search_url = f"https://musicbrainz.org/ws/2/artist/?query=artist:{safe_artist}&fmt=json&limit=1"
            headers = {"User-Agent": "FlashInfoKarukera/1.0 (medhi@famibelle.com)"}
            try:
                response = requests.get(search_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("artists"):
                        first_artist = data["artists"][0]
                        artist_id = first_artist.get("id")
                        name = first_artist.get("name", artist)
                        
                        # Récupérer les tags de l'artiste pour déduire le genre
                        tags_url = f"https://musicbrainz.org/ws/2/artist/{artist_id}?inc=tags&fmt=json"
                        tags_resp = requests.get(tags_url, headers=headers, timeout=10)
                        genre_hint = None
                        if tags_resp.status_code == 200:
                            tags_data = tags_resp.json()
                            artist_tags = tags_data.get("tags", [])
                            for tag in artist_tags:
                                tag_name = tag.get("name", "").lower()
                                if any(g in tag_name for g in ["zouk", "gwoka", "kompa", "biguine", "mazurka", "calypso", "dancehall", "bouillon", "chatta"]):
                                    genre_hint = tag_name
                                    break
                        
                        # Récupérer les recordings (morceaux) directement
                        recordings_url = f"https://musicbrainz.org/ws/2/recording/?artist={artist_id}&fmt=json&limit=50"
                        recordings_resp = requests.get(recordings_url, headers=headers, timeout=15)
                        if recordings_resp.status_code == 200:
                            recordings_data = recordings_resp.json()
                            tracks = []
                            for recording in recordings_data.get("recordings", [])[:20]:
                                title = recording.get("title", "")
                                if title and len(title) > 2:
                                    # Nettoyer : supprimer le contenu entre parenthèses
                                    title_clean = re.sub(r'\s*\([^)]*\)\s*', '', title).strip()
                                    # Supprimer les versions/remixes
                                    title_clean = re.sub(r'\s*[-(][^)]*remix[^)]*[)]*', '', title_clean, flags=re.IGNORECASE).strip()
                                    if len(title_clean) > 2:
                                        tracks.append(title_clean)
                            if tracks:
                                return tracks, name, genre_hint
                        
                        # Fallback: essayer les releases
                        releases_url = f"https://musicbrainz.org/ws/2/release/?artist={artist_id}&fmt=json&limit=20"
                        releases_resp = requests.get(releases_url, headers=headers, timeout=15)
                        if releases_resp.status_code == 200:
                            releases_data = releases_resp.json()
                            tracks = []
                            for release in releases_data.get("releases", [])[:10]:
                                title = release.get("title", "")
                                if title and len(title) > 2:
                                    title_clean = re.sub(r'\s*\([^)]*\)\s*', '', title).strip()
                                    if len(title_clean) > 2:
                                        tracks.append(title_clean)
                            if tracks:
                                return tracks, name, genre_hint
            except:
                pass
            return None, None
        
        # Essayer MusicBrainz
        mb_result = search_musicbrainz(artist_name)
        genre_hint = None
        
        if mb_result:
            if isinstance(mb_result, tuple):
                if len(mb_result) == 3:
                    mb_tracks, mb_artist, genre_hint = mb_result
                else:
                    mb_tracks, mb_artist = mb_result
                    genre_hint = None
                if mb_tracks:
                    # mb_tracks est une liste, pas besoin de parsing
                    found_tracks = set(mb_tracks)
                    artist_name = mb_artist
                    print(f"🎵 Source: MusicBrainz")
                    search_text = " "  # Dummy, ne sera pas utilisé
                else:
                    search_text = ""
                    mb_tracks = None
            else:
                search_text = mb_result
                mb_tracks = None
        else:
            search_text = ""
            mb_tracks = None
        
        # Déduire le genre si non fourni, en utilisant le hint de MusicBrainz si disponible
        if genre is None:
            if genre_hint:
                genre = genre_hint
                print(f"🎵 Genre déduit: {genre} (via MusicBrainz)")
            else:
                detected_genre = _detect_genre_from_search(artist_name, search_text)
                if detected_genre:
                    genre = detected_genre
                    print(f"🎵 Genre déduit: {genre}")
                else:
                    genre = "zouk_retro"
                    print(f"⚠️ Genre non déduit, utilisation par défaut: {genre}")
        
        if mb_tracks is None:
            # Essayer Wikipedia FR
            def search_wikipedia(artist, lang="fr"):
                url = f"https://{lang}.wikipedia.org/wiki/{artist.replace(' ', '_')}"
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        return soup.get_text(), soup
                except:
                    pass
                return None, None
            
            # Essayer Wikipedia FR puis EN
            wiki_content, wiki_soup = search_wikipedia(artist_name, "fr")
            if not wiki_content:
                wiki_content, wiki_soup = search_wikipedia(artist_name, "en")
            
            if wiki_content:
                search_text = wiki_content
                print("📚 Source: Wikipedia")
            else:
                # Recherche Google avec site:wikipedia.org
                search_query = f"{artist_name} discography site:wikipedia.org OR site:fr.wikipedia.org"
                url = f"https://www.google.com/search?q={search_query}"
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                search_text = soup.get_text()
                print("🔍 Source: Google (recherche Wikipedia)")
        
        # Déduire le genre si non fourni
        if genre is None:
            detected_genre = _detect_genre_from_search(artist_name, search_text)
            if detected_genre:
                genre = detected_genre
                print(f"🎵 Genre déduit: {genre}")
            else:
                genre = "zouk_retro"
                print(f"⚠️ Genre non déduit, utilisation par défaut: {genre}")
        
        # Extraire les titres de chansons
        # Si on a déjà des tracks de MusicBrainz, on ne fait pas de parsing supplémentaire
        if 'found_tracks' not in locals() or not found_tracks:
            found_tracks = set()
            
            # Utiliser des patterns plus précis pour éviter le bruit
            artist_escaped = re.escape(artist_name)
            track_patterns = [
                # "Titre" - Artiste
                rf'"([^"]+)"\s*[-\–]\s*{artist_escaped}',
                # "Titre" par Artiste
                rf'"([^"]+)"\s+par\s+{artist_escaped}',
                # Titre - Artiste (sans guillemets)
                rf'([A-Z][^\n:]+)\s*[-\–]\s*{artist_escaped}',
                # Dans des listes : 1. "Titre"
                rf'\d+[.)]\s*"([^"]+)"',
                # "Titre" (sans artiste, mais ligne suivante contient artiste)
                rf'"([^"]+)"',
            ]
            
            for pattern in track_patterns:
                matches = re.findall(pattern, search_text)
                for match in matches:
                    match = match.strip()
                    # Nettoyer
                    match = re.sub(r'\s+', ' ', match)
                    # Filtrer les titres trop courts/trop longs
                    if 3 <= len(match) <= 100:
                        found_tracks.add(match)
        
        # Mots à exclure (pas des titres de chansons)
        exclude_keywords = [
            "n'est", "pas", "plus", "que", "qui", "pour", "avec", "sans", "dans",
            "sur", "par", "est", "sont", "était", "sera",
            "ce", "cette", "cet", "ces", "dont", "où",
            "google", "wikipedia", "discographie", "morceau", "titre", "chanson",
            "album", "single", "compilation", "année", "sorti", "sortie",
            "label", "maison", "disque", "cd", "vinyle",
            "unternehmen", "inhalte", "werden", "personalisierte", "daten", "nutzung",
            "diese", "seite", "verwendet", "cookies",
        ]
        
        filtered_tracks = []
        for track in found_tracks:
            track_lower = track.lower()
            # Ne doit pas contenir de mots à exclure
            has_exclude = any(kw in track_lower for kw in exclude_keywords)
            # Ne doit pas être juste un nombre
            is_number = bool(re.match(r'^\d+$', track.strip()))
            # Doit avoir une longueur raisonnable
            is_too_short = len(track) < 3
            # Ne doit pas être une phrase trop longue
            has_too_many_words = len(track.split()) > 8
            
            if not has_exclude and not is_number and not is_too_short and not has_too_many_words:
                filtered_tracks.append(track)
        
        # Limiter aux premiers résultats
        filtered_tracks = list(set(filtered_tracks))[:max_results]
        
        print(f"✅ Trouvé {len(filtered_tracks)} morceaux potentiels:")
        for i, track in enumerate(filtered_tracks, 1):
            print(f"  {i}. {track}")
        
        if not dry_run and filtered_tracks:
            print(f"\n💾 Ajout à la base (genre: {genre}) ?")
            print("  Tape 'y' pour tout ajouter, 'n' pour annuler, ou les numéros des morceaux à ajouter (ex: 1 3 5)")
            choice = input("> ").strip().lower()
            
            if choice == 'y':
                to_add = filtered_tracks
            elif choice == 'n':
                to_add = []
            else:
                # Parser les numéros
                try:
                    indices = [int(x) - 1 for x in choice.split() if x.isdigit()]
                    to_add = [filtered_tracks[i] for i in indices if 0 <= i < len(filtered_tracks)]
                except:
                    to_add = []
            
            # Ajouter à la base
            if to_add:
                existing_tracks = [t["name"] for t in CARIBBEAN_TRACKS.get(genre, [])]
                for track_name in to_add:
                    if track_name not in existing_tracks:
                        CARIBBEAN_TRACKS.setdefault(genre, []).append({
                            "name": track_name,
                            "artists": [artist_name]
                        })
                        print(f"  ✓ Ajouté: {track_name}")
                    else:
                        print(f"  ✗ Déjà présent: {track_name}")
        
        return filtered_tracks
        
    except ImportError:
        print("⚠️  Installer les dépendances: pip install requests beautifulsoup4")
        return []
    except Exception as e:
        print(f"❌ Erreur lors de la recherche: {e}")
        return []


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Gestion de la base Caribbean DB — liste des artistes et enrichissement"
    )
    parser.add_argument(
        "-f", "--flat",
        action="store_true",
        help="Affiche la liste plate de tous les artistes (sans regroupement par genre)"
    )
    parser.add_argument(
        "-g", "--genre",
        type=str,
        help="Affiche uniquement les artistes d'un genre spécifique"
    )
    parser.add_argument(
        "-e", "--enrich",
        type=str,
        metavar="ARTIST",
        help="Recherche et ajoute les morceaux d'un artiste (ex: 'Joelle Ursull')"
    )
    parser.add_argument(
        "--enrich-genre",
        type=str,
        default=None,
        help="Genre pour l'enrichissement (par défaut: déduction automatique)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mode test : affiche les résultats sans modifier la base"
    )
    args = parser.parse_args()
    
    # Mode enrichissement
    if args.enrich:
        enrich_artist_from_web(
            artist_name=args.enrich,
            genre=args.enrich_genre,
            max_results=15,
            dry_run=args.dry_run
        )
    elif args.genre:
        artists_by_genre = get_artists_by_genre()
        if args.genre in artists_by_genre:
            print(f"\n{args.genre.upper()} ({len(artists_by_genre[args.genre])} artistes):")
            for artist in artists_by_genre[args.genre]:
                print(f"  - {artist}")
        else:
            print(f"Genre '{args.genre}' non trouvé. Genres disponibles: {', '.join(sorted(artists_by_genre.keys()))}")
    else:
        print_artists(by_genre=not args.flat)
