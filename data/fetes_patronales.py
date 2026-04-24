"""Fêtes patronales des communes de Guadeloupe — clé "MM-DD".

Source : dédicaces des églises principales (diocèse de Basse-Terre et Pointe-à-Pitre).
Note : Lamentin (Sainte-Trinité) est exclue car la date est variable (dimanche après la Pentecôte).
"""

COMMUNES_FETES_PATRONALES: dict[str, list[str]] = {
    "03-19": ["Vieux-Habitants"],           # Saint Joseph
    "05-03": ["Petit-Canal"],               # Saints Philippe et Jacques
    "06-24": ["Baie-Mahault", "Le Moule"],  # Saint Jean-Baptiste
    "06-29": ["Deshaies", "Pointe-à-Pitre"],# Saints Pierre et Paul
    "07-26": ["Goyave", "Sainte-Anne"],     # Sainte Anne
    "08-07": ["Vieux-Fort"],                # Saint Albert
    "08-08": ["Baillif"],                   # Saint Dominique
    "08-15": [                              # Assomption / Notre-Dame
        "Basse-Terre", "La Désirade", "Petit-Bourg",
        "Pointe-Noire", "Port-Louis", "Terre-de-Haut", "Trois-Rivières",
    ],
    "08-17": ["Capesterre-Belle-Eau"],      # Saint Hyacinthe
    "08-23": ["Sainte-Rose"],               # Sainte Rose de Lima
    "08-25": ["Bouillante", "Le Gosier"],   # Saint Louis
    "08-28": ["Saint-Claude"],              # Saint Augustin
    "10-04": ["Saint-François"],            # Saint François d'Assise
    "10-09": ["Anse-Bertrand"],             # Saint Denis
    "11-04": ["Gourbeyre"],                 # Saint Charles Borromée
    "11-30": ["Morne-à-l'Eau"],             # Saint André
    "12-06": ["Terre-de-Bas"],              # Saint Nicolas
    "12-08": ["Grand-Bourg", "Les Abymes"],# Immaculée Conception
}
