"""
Signe du jour — liste curatée de la faune caribéenne (Guadeloupe)
Chaque entrée : nom créole, nom commun, famille, conditions météo, éditions,
et le `savoir` factuel que Mistral formulera dans la voix de Maryse Condé.
"""

import random

# conditions : "soleil", "nuageux", "pluie", "vent", "orage", "chaleur"
#              liste vide = toutes conditions
# editions   : "matin", "soir", ou les deux

_WEATHER_KEYWORDS: list[tuple[str, list[str]]] = [
    ("orage",   ["orage", "orageux", "tempête", "foudre"]),
    ("pluie",   ["pluie", "averse", "pluvieux", "bruine", "précipitation", "mouillé"]),
    ("vent",    ["vent", "venteux", "brise", "rafale", "souffle"]),
    ("nuageux", ["nuageux", "nuages", "couvert", "voilé", "brumeux", "gris"]),
    ("chaleur", ["chaleur", "chaud", "tropical", "caniculaire"]),
    ("soleil",  ["soleil", "ensoleillé", "dégagé", "beau temps", "clair"]),
]


def _parse_conditions(weather_summary: str | None) -> list[str]:
    if not weather_summary:
        return []
    text = weather_summary.lower()
    return [cond for cond, kws in _WEATHER_KEYWORDS if any(kw in text for kw in kws)]


def pick_faune_signe(
    weather_summary: str | None,
    edition: str,
    exclude: list[str],
) -> dict | None:
    """Retourne une entrée de FAUNE_SIGNES adaptée à la météo, l'édition et l'anti-répétition."""
    conditions = _parse_conditions(weather_summary)

    candidates = [
        e for e in FAUNE_SIGNES
        if edition in e["editions"]
        and e["nom_creole"] not in exclude
        and (not e["conditions"] or any(c in conditions for c in e["conditions"]))
    ]

    if not candidates:
        # Fallback : ignorer les conditions météo, garder seulement edition + anti-répétition
        candidates = [
            e for e in FAUNE_SIGNES
            if edition in e["editions"] and e["nom_creole"] not in exclude
        ]

    if not candidates:
        return None

    return random.choice(candidates)


FAUNE_SIGNES: list[dict] = [

    # ── Oiseaux ───────────────────────────────────────────────────────────────

    {
        "nom_creole":  "fwou-fwou",
        "nom_commun":  "Colibri huppé / Orthorhyncus cristatus",
        "famille":     "oiseaux",
        "conditions":  ["soleil", "chaleur"],
        "editions":    ["matin"],
        "savoir": (
            "Son nom vient directement des Arawaks — le souffle de l'air à travers ses ailes. "
            "Il bat des ailes jusqu'à soixante fois par seconde, suspendu immobile devant la fleur. "
            "Les anciens disaient que le voir au lever du soleil annonce une journée qui ira vite, "
            "mais où il faut savoir s'arrêter sur ce qui compte."
        ),
    },
    {
        "nom_creole":  "kolibri madè",
        "nom_commun":  "Colibri à gorge pourpre / Eulampis jugularis",
        "famille":     "oiseaux",
        "conditions":  ["soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Sa gorge est pourpre sous le soleil direct, presque noire dans l'ombre. "
            "Le même oiseau, la même plume, deux couleurs selon la lumière qu'on pose dessus. "
            "Les anciens y lisaient un enseignement : ce qu'on voit d'une personne dépend "
            "du regard qu'on apporte, pas seulement de ce qu'elle est."
        ),
    },
    {
        "nom_creole":  "sucrier",
        "nom_commun":  "Sucrier à ventre jaune / Coereba flaveola",
        "famille":     "oiseaux",
        "conditions":  ["nuageux", "soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Petit oiseau jaune de tous les jardins créoles — il vit là où vit l'homme. "
            "Son chant change de rythme avant les changements de temps : "
            "les anciens l'écoutaient pour savoir si la pluie allait venir. "
            "Ce qui prévient sans crier, et qu'on n'entend que si on s'arrête."
        ),
    },
    {
        "nom_creole":  "pélikan",
        "nom_commun":  "Pélican brun / Pelecanus occidentalis",
        "famille":     "oiseaux",
        "conditions":  ["soleil", "vent"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Animal totem des pêcheurs — quand les pélicans plongent en masse, "
            "le banc de poissons est là. Leur présence groupée annonce le beau temps et la bonne prise. "
            "Les anciens disaient qu'ils lisaient la mer mieux que n'importe quelle boussole. "
            "Signe de ce qui sait, sans avoir appris dans les livres."
        ),
    },
    {
        "nom_creole":  "frégat",
        "nom_commun":  "Frégate superbe / Fregata magnificens",
        "famille":     "oiseaux",
        "conditions":  ["vent", "soleil"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Ses ailes déployées mesurent plus de deux mètres. Elle ne se pose presque jamais, "
            "vole des jours entiers sans toucher terre ni eau — ses plumes ne sont pas imperméables. "
            "Les anciens en faisaient le symbole du marronage aérien, de l'insoumission totale. "
            "Ce qui ne peut pas être enchaîné parce qu'il a choisi de ne jamais atterrir."
        ),
    },
    {
        "nom_creole":  "pic gwadloup",
        "nom_commun":  "Pic de Guadeloupe / Melanerpes herminieri",
        "famille":     "oiseaux",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["matin"],
        "savoir": (
            "Endémique unique au monde — il n'existe nulle part ailleurs. "
            "Son tambourinage dans les arbres morts était interprété par les anciens "
            "comme un message des esprits de la forêt : une convocation, un avertissement, "
            "une réponse à une question qu'on n'avait pas encore posée."
        ),
    },
    {
        "nom_creole":  "yòlò",
        "nom_commun":  "Siffleur des montagnes / Myiadestes genibarbis",
        "famille":     "oiseaux",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["soir"],
        "savoir": (
            "Il vit dans la forêt haute, là où les mornes touchent les nuages. "
            "Son chant plaintif et long n'atteint le bourg qu'au crépuscule. "
            "Les anciens des hauteurs l'associaient aux esprits des marrons qui ne sont jamais redescendus. "
            "Ce qui chante la liberté depuis un endroit où les chaînes ne montent pas."
        ),
    },
    {
        "nom_creole":  "soukouyan",
        "nom_commun":  "Soukouyan (figure du folklore créole)",
        "famille":     "oiseaux",
        "conditions":  [],
        "editions":    ["soir"],
        "savoir": (
            "À la nuit tombée, le soukouyan enlève sa peau humaine et l'accroche aux branches "
            "d'un fromager. Il prend la forme d'une boule de feu ou d'un oiseau noir "
            "pour traverser le pays sans être reconnu. "
            "Signe de ce qui se dépouille de sa forme pour aller là où son apparence ordinaire ne le laisserait pas."
        ),
    },
    {
        "nom_creole":  "papillon nwè",
        "nom_commun":  "Grand papillon noir (Heraclides andraemon)",
        "famille":     "oiseaux",
        "conditions":  [],
        "editions":    ["soir"],
        "savoir": (
            "Un grand papillon noir qui entre dans une maison est l'âme d'un ancêtre "
            "venu rendre visite. On ne le chasse jamais — lui faire du mal attire le malheur. "
            "Les anciens lui laissaient la place et attendaient en silence qu'il reparte de lui-même. "
            "Ce qui entre sans frapper parce qu'il est chez lui."
        ),
    },

    # ── Reptiles ──────────────────────────────────────────────────────────────

    {
        "nom_creole":  "igwann vèt",
        "nom_commun":  "Iguane vert / Iguana iguana",
        "famille":     "reptiles",
        "conditions":  ["soleil", "chaleur"],
        "editions":    ["matin"],
        "savoir": (
            "Animal totem des Arawaks, gardien de Petite-Terre. "
            "Les marrons s'en inspiraient : immobile et invisible dans la végétation, "
            "il voit tout sans être vu, sait attendre des heures avant d'agir. "
            "Les anciens disaient qu'observer un iguane, c'est apprendre la patience "
            "qui permet de survivre quand l'ennemi est plus fort."
        ),
    },
    {
        "nom_creole":  "zandoli",
        "nom_commun":  "Anoli / Anolis marmoratus",
        "famille":     "reptiles",
        "conditions":  ["soleil", "chaleur"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Il en existe douze sous-espèces — une pour chaque île de l'archipel. "
            "Sa gorge se déploie en fanion coloré pour séduire ou intimider. "
            "Quand le danger est trop grand, il abandonne sa queue qui continue à gigoter — "
            "et lui, il repart libre. Signe de ce qui se libère en laissant derrière ce dont il n'a plus besoin."
        ),
    },
    {
        "nom_creole":  "mabouya",
        "nom_commun":  "Mabouya / Sphaerodactylus fantasticus",
        "famille":     "reptiles",
        "conditions":  [],
        "editions":    ["soir"],
        "savoir": (
            "Lézard nocturne des murs et des cases — ses ventouses lui permettent de marcher au plafond. "
            "Son nom était celui du dieu du mal chez les Kalinagos. "
            "Les familles créoles le respectaient sans l'aimer : on ne le tue jamais dans la maison. "
            "Ce qui colle aux murs et aux mémoires, et qu'on garde malgré soi."
        ),
    },
    {
        "nom_creole":  "koures",
        "nom_commun":  "Couresse / Alsophis antillensis",
        "famille":     "reptiles",
        "conditions":  ["nuageux"],
        "editions":    ["matin"],
        "savoir": (
            "Couleuvre inoffensive, endémique des Antilles — elle ne mord que si on la provoque. "
            "Gardienne silencieuse des jardins et des réserves à grain, elle mange les rats et les fourmis. "
            "Les anciens disaient qu'une couresse installée sous la case, c'est une chance. "
            "Signe de ce qui effraie sans raison, et protège sans bruit."
        ),
    },

    # ── Amphibiens ────────────────────────────────────────────────────────────

    {
        "nom_creole":  "grenn-bwa",
        "nom_commun":  "Hylode de Basse-Terre / Eleutherodactylus barlagnei",
        "famille":     "amphibiens",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["soir"],
        "savoir": (
            "Endémique de Basse-Terre uniquement — il vit dans les feuilles mortes de la forêt tropicale. "
            "Son chant nocturne est constant, mais quand il s'arrête d'un coup, "
            "les anciens levaient la tête : cela signifie un danger proche, ou la présence d'un esprit. "
            "Ce qui se tait au moment précis où il faut être attentif."
        ),
    },
    {
        "nom_creole":  "krapo",
        "nom_commun":  "Crapaud buffle / Rhinella marina",
        "famille":     "amphibiens",
        "conditions":  ["pluie", "nuageux"],
        "editions":    ["soir"],
        "savoir": (
            "Ses glandes parotides sécrètent un venin qui paralyse les prédateurs. "
            "Les gadèzafé créoles l'utilisaient dans leurs préparations les plus puissantes. "
            "Les enfants l'évitaient, les anciens le respectaient. "
            "Signe de ce qui contient une puissance qu'on ne soupçonne pas à le regarder."
        ),
    },

    # ── Insectes ──────────────────────────────────────────────────────────────

    {
        "nom_creole":  "luciole",
        "nom_commun":  "Luciole / Ti flambeau",
        "famille":     "insectes",
        "conditions":  [],
        "editions":    ["soir"],
        "savoir": (
            "Les anciens disaient que les lucioles sont les âmes des enfants morts sans baptême "
            "qui errent dans les mornes en attendant. Les voir en groupe dans la nuit "
            "est signe que les ancêtres sont proches. "
            "On ne les attrape jamais — ce qui éclaire la nuit ne demande pas la permission."
        ),
    },
    {
        "nom_creole":  "kabribo",
        "nom_commun":  "Cabrit-bois / Grillon des Antilles",
        "famille":     "insectes",
        "conditions":  [],
        "editions":    ["soir"],
        "savoir": (
            "Son chant tisse la nuit créole — régulier, sans relâche. "
            "Mais quand il s'arrête brusquement, les anciens immobilisaient toute la maison : "
            "quelqu'un approche, ou quelque chose qu'on ne voit pas. "
            "Il donne l'heure sans montre et l'alerte sans crier."
        ),
    },
    {
        "nom_creole":  "myèl péyi",
        "nom_commun":  "Abeille péyi / Trigona sp.",
        "famille":     "insectes",
        "conditions":  ["soleil", "chaleur"],
        "editions":    ["matin"],
        "savoir": (
            "Dans la tradition africaine portée aux Antilles, l'abeille est messagère "
            "entre les vivants et les ancêtres. Un essaim qui entre dans une maison "
            "annonce l'arrivée d'un esprit ou d'une bonne nouvelle. "
            "Elle bâtit en silence quelque chose de plus grand qu'elle — "
            "signe de ce qu'on construit sans jamais voir le résultat de son vivant."
        ),
    },
    {
        "nom_creole":  "foumi manyok",
        "nom_commun":  "Fourmi manioc / Acromyrmex octospinosus",
        "famille":     "insectes",
        "conditions":  ["soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Ses colonnes traversent la forêt nuit et jour — des milliers d'ouvrières "
            "qui découpent et transportent sans jamais se reposer. "
            "Les Arawaks observaient le sens de leurs colonnes pour prévoir la pluie. "
            "Les anciens disaient : « Foumi ka travay, foumi ka manyé. » "
            "Ce qui résiste en collectif, sans chef visible, depuis la nuit des temps."
        ),
    },
    {
        "nom_creole":  "guimbo",
        "nom_commun":  "Chauve-souris / Artibeus jamaicensis",
        "famille":     "insectes",
        "conditions":  [],
        "editions":    ["soir"],
        "savoir": (
            "Elle voit dans l'obscurité ce que le jour cache entièrement. "
            "Dans le quimbois créole, elle est l'animal du passage entre les mondes — "
            "associée aux zombis et aux esprits errants. "
            "Les anciens ne la tuaient jamais dans la maison. "
            "Signe de ce qui navigue sans lumière parce qu'il porte la sienne en lui."
        ),
    },

    # ── Mammifères terrestres ─────────────────────────────────────────────────

    {
        "nom_creole":  "gouti",
        "nom_commun":  "Agouti / Dasyprocta antillensis",
        "famille":     "mammifères",
        "conditions":  ["soleil", "nuageux"],
        "editions":    ["matin"],
        "savoir": (
            "Il a traversé la Caraïbe dans les pirogues des Arawaks — animal de compagnie "
            "et de subsistance amérindien, apporté exprès pour peupler les îles. "
            "Il enterre les graines et les oublie parfois — il est ainsi le premier planteur de forêt. "
            "Signe de ce qui continue depuis avant la colonisation, porté par une mémoire plus ancienne."
        ),
    },
    {
        "nom_creole":  "raton laveur",
        "nom_commun":  "Raton laveur de Guadeloupe / Procyon minor",
        "famille":     "mammifères",
        "conditions":  ["nuageux"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Symbole du Parc National de la Guadeloupe — sa présence dans une zone "
            "indique un écosystème forestier en bonne santé. "
            "Il lave ses aliments dans l'eau avant de les manger — les anciens le trouvaient "
            "plus propre que bien des hommes. Signe de ce qui ne trompe pas sur l'état d'un monde."
        ),
    },

    # ── Faune marine ──────────────────────────────────────────────────────────

    {
        "nom_creole":  "tòti vèt",
        "nom_commun":  "Tortue verte / Chelonia mydas",
        "famille":     "marins",
        "conditions":  ["soleil", "chaleur"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Animal totem amérindien — longévité, fertilité, sagesse des âges. "
            "Elle revient pondre chaque année exactement sur la plage où elle est née, "
            "des décennies plus tard. Les anciens y voyaient la promesse que ce qui part "
            "finit toujours par revenir sur la terre qui l'a fait naître."
        ),
    },
    {
        "nom_creole":  "tòti luth",
        "nom_commun":  "Tortue luth / Dermochelys coriacea",
        "famille":     "marins",
        "conditions":  [],
        "editions":    ["soir"],
        "savoir": (
            "Plus grande tortue du monde — jusqu'à sept cents kilos. "
            "Elle émerge de la mer dans la nuit noire pour pondre, seule, en silence. "
            "Les anciens qui la voyaient creuser la terre au clair de lune gardaient le silence : "
            "on ne dérange pas ce qui surgit de l'obscurité pour accomplir ce qui doit être accompli."
        ),
    },
    {
        "nom_creole":  "tòti karé",
        "nom_commun":  "Tortue imbriquée / Eretmochelys imbricata",
        "famille":     "marins",
        "conditions":  ["vent", "soleil"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Sa carapace translucide et dorée était taillée en parures rituelles amérindiennes. "
            "Aujourd'hui en danger critique d'extinction. "
            "Les anciens disaient qu'elle porte un monde entier sur le dos — "
            "et que quand une espèce disparaît, c'est un morceau du monde qu'elle emporte avec elle."
        ),
    },
    {
        "nom_creole":  "balèn",
        "nom_commun":  "Baleine à bosse / Megaptera novaeangliae",
        "famille":     "marins",
        "conditions":  ["vent"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Les Kalinagos y voyaient des ancêtres revenus sous forme marine. "
            "Les tuer portait malheur — conviction partagée par tous les pêcheurs créoles. "
            "Son chant traverse des centaines de kilomètres de mer. "
            "Signe de ce qui revient de loin pour témoigner, et qu'on entend avant de le voir."
        ),
    },
    {
        "nom_creole":  "manman dlo",
        "nom_commun":  "Lamantin des Caraïbes / Trichechus manatus",
        "famille":     "marins",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["soir"],
        "savoir": (
            "Les premiers marins ont pris le lamantin pour une sirène — "
            "à l'origine des légendes de la Manman Dlo caribéenne. "
            "Il allaite ses petits comme une femme, flotte entre deux eaux, appartient aux deux mondes. "
            "Espèce aujourd'hui en grand danger. Signe de ce qui nage entre deux mondes "
            "sans appartenir à aucun des deux."
        ),
    },
    {
        "nom_creole":  "chatou",
        "nom_commun":  "Poulpe / Octopus vulgaris",
        "famille":     "marins",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["soir"],
        "savoir": (
            "Huit bras, trois cœurs, sang bleu, intelligence de ce qui n'a pas d'os. "
            "Les pêcheurs créoles lui vouent un respect mêlé de crainte — "
            "il attrape depuis les profondeurs sans qu'on le voie venir. "
            "Les anciens disaient que croiser un chatou dans les rochers, "
            "c'est un signe qu'il faut regarder ce qui se cache sous la surface."
        ),
    },
    {
        "nom_creole":  "wasou",
        "nom_commun":  "Ouassou / Macrobrachium carcinus",
        "famille":     "marins",
        "conditions":  ["pluie", "nuageux"],
        "editions":    ["matin"],
        "savoir": (
            "Crevette géante des rivières de Basse-Terre — elle remonte les courants "
            "jusqu'aux sources les plus hautes des mornes. "
            "Elle vivait dans les rivières que les anciens considéraient comme sacrées. "
            "Signe de ce qui prospère dans les eaux claires, profondes, et qu'on n'atteint "
            "qu'en ayant le courage de remonter à contre-courant."
        ),
    },

    # ── Crustacés terrestres ──────────────────────────────────────────────────

    {
        "nom_creole":  "krab tè",
        "nom_commun":  "Crabe de terre / Cardisoma guanhumi",
        "famille":     "crustacés",
        "conditions":  ["pluie"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Il sort de la terre au moment précis où la saison tourne — "
            "la matoutou du lundi de Pâques, le festin du crabe après le carême. "
            "Nourriture sacrée du retour du printemps, partagée collectivement. "
            "Signe de ce qui émerge à l'heure exacte, ni avant ni après, "
            "et qu'il faut être là pour accueillir."
        ),
    },
    {
        "nom_creole":  "touloulou",
        "nom_commun":  "Crabe touloulou / Gecarcinus lateralis",
        "famille":     "crustacés",
        "conditions":  ["vent", "nuageux"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Son nom est hérité direct des Kalinagos, intact depuis des siècles. "
            "Il a donné son nom aux femmes masquées du carnaval de Guadeloupe — "
            "les touloulous qui choisissent leurs cavaliers et ne se découvrent jamais. "
            "Signe de ce qui se cache pour être plus libre, "
            "qui préserve son mystère pour garder le pouvoir de choisir."
        ),
    },

    # ── Faune du volcan ───────────────────────────────────────────────────────

    {
        "nom_creole":  "myg",
        "nom_commun":  "Mygale de la Soufrière / Theraphosidae sp.",
        "famille":     "arachnides",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["soir"],
        "savoir": (
            "Découverte seulement en 1999 sur les flancs de la Soufrière — "
            "pendant des siècles, elle était là sans que personne ne la connaisse. "
            "Elle vit là où les autres ne s'aventurent pas, dans les fissures du volcan. "
            "Gardienne des hauteurs. Signe des choses qui existent sans qu'on les ait nommées, "
            "et qui n'ont pas besoin de notre regard pour être réelles."
        ),
    },
]
