"""Données géographiques et médias pour l'extraction de lieux dans les articles RSS."""

# Mapping host RSS → nom de média affichable
SOURCE_NAMES = {
    "franceantilles":   "France-Antilles Guadeloupe",
    "rci.fm":           "RCI Guadeloupe",
    "la1ere":           "La Première",
    "zye-a-mangrovla":  "Zyé a Mangrov'la",
    "regionguadeloupe": "Région Guadeloupe",
}

# Communes et lieux guadeloupéens (plus long en premier pour éviter les faux-positifs)
LIEUX_GUADELOUPE = [
    # Communes
    "Pointe-à-Pitre", "Capesterre-Belle-Eau", "Capesterre de Marie-Galante",
    "Sainte-Anne", "Sainte-Rose", "Saint-François", "Saint-Claude",
    "Le Gosier", "Les Abymes", "Baie-Mahault", "Le Moule", "Petit-Bourg",
    "Lamentin", "Gourbeyre", "Bouillante", "Pointe-Noire", "Deshaies",
    "Vieux-Habitants", "Baillif", "Goyave", "Morne-à-l'Eau",
    "Port-Louis", "Anse-Bertrand", "Petit-Canal", "Dampierre",
    "Grand-Bourg", "Capesterre", "Saint-Louis", "Les Saintes", "Terre-de-Haut",
    "La Désirade", "Saint-Martin", "Marigot", "Saint-Barthélemy", "Gustavia",
    "Marie-Galante", "Grande-Terre", "Basse-Terre",
    # Lieux-dits et quartiers
    "Karukera", "Houëlmont", "Mougoutte", "Dubedou", "Ravine-Chaude", "Ravine-Blanche",
    "Boisripeaux", "La Jaille", "Grand-Camp", "Morne-Coco", "La Providence",
    "Blachon", "Baimbridge", "Conchou", "La Rosette", "Morne Moustique",
    "La Cocoyer", "Fond Lahaye", "La Retraite", "Anse Bertrand", "Morne à Louis",
    "La Caravelle", "Pointe de la Grande Vigie", "Anse à la Barque", "Fond Bananier",
    "Morne Pisquet", "Anse à l'Eau", "Pointe des Châteaux", "Destrellan",
    "Beausoleil", "Morne Piton", "Fond Baillif", "Morne à Vache", "La Plaine",
    "Rivière des Pères", "Carmélite", "Pointe à Vache", "Morne à Piton",
    "Sofaïa", "Pigeon", "Malendure", "Anse à la Perle", "Pointe Batterie",
    "Fond Cacao", "Bananier", "Morne-à-Lau", "Anse Duffaut", "Capesterre",
    "Folle Anse", "Viard", "La Boucan", "Morne-Piton", "La Datcha",
    "La Pointe de la Verdure", "Carénage", "Rawel", "La Pointe",
    "Bois-Jolan", "Anse Tarare", "Beauséjour",
    # Sites historiques et culturels
    "Bumidom", "Mémorial ACTe", "Fort Napoléon", "Habitation La Grivelière",
    "Habitation Murat", "Habitation coloniale", "Case créole",
]

# Pays et grandes villes du monde (en français, plus long en premier)
LIEUX_MONDE = [
    # Caraïbes et Amériques
    "République dominicaine", "Trinidad-et-Tobago", "États-Unis", "USA", "United States", "Costa Rica",
    "Porto Rico", "Saint-Kitts", "Saint-Vincent", "Sainte-Lucie",
    "Martinique", "Guadeloupe", "Guyane française", "Guyane", "La Réunion",
    "Haïti", "Cuba", "Jamaïque", "Barbade", "Dominique", "Antigua",
    "Venezuela", "Colombie", "Brésil", "Mexique", "Canada", "Argentine",
    "Washington", "New York", "Miami", "Houston", "Los Angeles",
    # Europe
    "Royaume-Uni", "Pays-Bas", "République tchèque", "Bosnie-Herzégovine",
    "France métropolitaine", "France",
    "Allemagne", "Espagne", "Italie", "Portugal", "Belgique", "Suisse",
    "Pologne", "Hongrie", "Roumanie", "Bulgarie", "Grèce", "Turquie",
    "Russie", "Ukraine", "Suède", "Norvège", "Danemark", "Finlande",
    "Paris", "Londres", "Berlin", "Madrid", "Rome", "Bruxelles",
    # Afrique
    "Afrique du Sud", "Côte d'Ivoire", "Burkina Faso", "République centrafricaine",
    "Sénégal", "Cameroun", "Maroc", "Algérie", "Tunisie", "Égypte",
    "Nigeria", "Ghana", "Mali", "Guinée", "Congo", "Kenya", "Éthiopie",
    "Abidjan", "Dakar", "Casablanca",
    "Sierra Leone", "Liban", "Soudan", "Somalie", "Tchad", "Niger",
    "Bénin", "Togo", "Madagascar", "Maurice", "Seychelles", "Comores",
    # Asie / Océanie / Moyen-Orient
    "Arabie saoudite", "Émirats arabes unis", "Corée du Sud", "Corée du Nord",
    "Chine", "Japon", "Inde", "Pakistan", "Australie", "Nouvelle-Zélande",
    "Israël", "Palestine", "Iran", "Irak", "Liban", "Syrie",
    "Pékin", "Tokyo", "Séoul", "Mumbai", "Sydney",
]
