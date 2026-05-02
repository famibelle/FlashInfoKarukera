"""
Signe du jour — liste curatée de la flore caribéenne (Guadeloupe)
Chaque entrée : nom créole, nom commun, famille, conditions météo, éditions,
et le `savoir` factuel que Mistral formulera dans la voix de Maryse Condé.
"""

# conditions : "soleil", "nuageux", "pluie", "vent", "orage", "chaleur"
#              liste vide = toutes conditions
# editions   : "matin", "soir", ou les deux

FLORA_SIGNES: list[dict] = [

    # ── Arbres & bois ─────────────────────────────────────────────────────────

    {
        "nom_creole":  "courbaril",
        "nom_commun":  "Courbaril / Locust tree",
        "famille":     "arbres",
        "conditions":  ["soleil", "chaleur"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Sa résine dorée — le copal — était récoltée par les guérisseurs pour calmer "
            "les douleurs articulaires et purifier l'espace. Bois imputrescible, "
            "il résiste aux siècles et aux termites. Symbole de ce qui tient quand tout cède."
        ),
    },
    {
        "nom_creole":  "fromager",
        "nom_commun":  "Fromager / Kapokier",
        "famille":     "arbres",
        "conditions":  [],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Arbre sacré dans toute la Caraïbe — les anciens croyaient qu'il abritait "
            "les esprits des ancêtres. Son kapok garnissait les matelas et les gilets de sauvetage. "
            "On ne l'abat pas sans demander permission."
        ),
    },
    {
        "nom_creole":  "bois-canon",
        "nom_commun":  "Bois-canon / Trompette",
        "famille":     "arbres",
        "conditions":  ["pluie", "nuageux"],
        "editions":    ["matin"],
        "savoir": (
            "Il pousse vite là où la forêt a été blessée — premier à revenir après un cyclone. "
            "Sa tige creuse servait de conduit d'eau. Signe de renouveau après la perturbation, "
            "de ce qui repousse sans hésiter."
        ),
    },
    {
        "nom_creole":  "manguier",
        "nom_commun":  "Manguier",
        "famille":     "arbres",
        "conditions":  ["soleil", "chaleur"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "L'arbre de la générosité — il donne à tous sans distinction. "
            "Son ombre a abrité des palabres, des siestes, des naissances. "
            "Ses feuilles séchées calmaient la fièvre. On dit que là où pousse un manguier, "
            "la maison ne manque jamais."
        ),
    },
    {
        "nom_creole":  "calebassier",
        "nom_commun":  "Calebassier",
        "famille":     "arbres",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["soir"],
        "savoir": (
            "Sa calebasse était le premier récipient — bol, louche, gourde, instrument de musique. "
            "Les quimboiseurs l'utilisaient pour les cérémonies de purification. "
            "Trouver un calebassier rappelle que l'utile peut être beau."
        ),
    },
    {
        "nom_creole":  "gommier",
        "nom_commun":  "Gommier blanc",
        "famille":     "arbres",
        "conditions":  ["soleil", "vent"],
        "editions":    ["matin"],
        "savoir": (
            "C'est de lui qu'on taillait les pirogues de pêche — son bois léger et sa résine "
            "imperméable en faisaient le compagnon idéal de la mer. "
            "Les Amérindiens l'utilisaient aussi comme torche naturelle. Signe du voyage, "
            "de ce qu'on construit pour traverser."
        ),
    },
    {
        "nom_creole":  "arbre à pain",
        "nom_commun":  "Arbre à pain / Fruit à pain",
        "famille":     "arbres",
        "conditions":  [],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Amené aux Antilles pour nourrir les esclaves, il est devenu l'arbre nourricier "
            "par excellence. Bouilli, rôti, frit — le fruit à pain ne se refuse jamais. "
            "Symbole d'une générosité imposée qui s'est transformée en ancrage."
        ),
    },
    {
        "nom_creole":  "mombin",
        "nom_commun":  "Mombin / Prunier mombin",
        "famille":     "arbres",
        "conditions":  ["soleil", "chaleur"],
        "editions":    ["matin"],
        "savoir": (
            "Son fruit acidulé désaltère les marcheurs. L'écorce en décoction calmait "
            "les inflammations de gorge. Les enfants le grimpaient — c'est l'arbre "
            "de l'enfance libre, de la récréation, de ce qui pousse sans être cultivé."
        ),
    },
    {
        "nom_creole":  "flamboyant",
        "nom_commun":  "Flamboyant",
        "famille":     "arbres",
        "conditions":  ["soleil", "chaleur"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Il fleurit en plein cœur de la saison sèche, quand tout se dessèche — "
            "rouge et orange au-dessus du vide. Aucune utilité médicinale décisive, "
            "juste la beauté têtue. Signe que l'éclat ne demande pas la permission de venir."
        ),
    },
    {
        "nom_creole":  "poirier pays",
        "nom_commun":  "Poirier pays / Roble",
        "famille":     "arbres",
        "conditions":  ["nuageux"],
        "editions":    ["matin"],
        "savoir": (
            "Ses fleurs roses tombent avant les feuilles — il fleurit à nu, sans rien cacher. "
            "Bois dur utilisé pour les charpentes et les meubles anciens. "
            "Symbole de ce qui s'expose avant de s'expliquer."
        ),
    },
    {
        "nom_creole":  "palmiste royal",
        "nom_commun":  "Palmiste royal",
        "famille":     "arbres",
        "conditions":  ["soleil", "vent"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Il pousse droit, toujours, même quand le vent courbe les autres. "
            "Son cœur — le chou palmiste — était le mets des jours de fête. "
            "On le réservait aux grandes occasions car couper le palmiste, c'est le tuer."
        ),
    },
    {
        "nom_creole":  "coco",
        "nom_commun":  "Cocotier",
        "famille":     "arbres",
        "conditions":  ["soleil", "vent"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Rien ne se perd : l'eau, la chair, l'huile, la coque, la feuille, le bois. "
            "Les pêcheurs lisaient dans la direction de ses palmes l'orientation du vent dominant. "
            "Arbre de l'abondance totale — il donne sans jamais s'épuiser."
        ),
    },
    {
        "nom_creole":  "bois-baume",
        "nom_commun":  "Bois-baume / Balata",
        "famille":     "arbres",
        "conditions":  ["pluie", "nuageux"],
        "editions":    ["soir"],
        "savoir": (
            "Son latex rouge-brun — le balata — servait à calfater les embarcations "
            "et à fabriquer les premières balles de golf. Arbre de la forêt profonde, "
            "difficile à trouver. Signe des choses rares, de la patience que méritent "
            "les belles matières."
        ),
    },
    {
        "nom_creole":  "acajou pays",
        "nom_commun":  "Acajou des Antilles",
        "famille":     "arbres",
        "conditions":  ["soleil"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Bois noble, rougeâtre, à grain serré — les ébénistes créoles en faisaient "
            "les buffets et les lits à baldaquin des grandes maisons. "
            "Surexploité, il se fait rare. Sa présence rappelle ce qui a de la valeur "
            "et qu'on doit apprendre à ne pas dilapider."
        ),
    },
    {
        "nom_creole":  "châtaignier pays",
        "nom_commun":  "Châtaignier des Antilles",
        "famille":     "arbres",
        "conditions":  ["pluie", "nuageux"],
        "editions":    ["soir"],
        "savoir": (
            "Arbre de la forêt humide de montagne, il ancre les terres en pente "
            "et retient l'eau des crêtes. Sa noix, enveloppée d'un brou hérissé, "
            "se grille sur la braise. Signe des hauteurs, de ce qui protège en restant discret."
        ),
    },
    {
        "nom_creole":  "figuier maudit",
        "nom_commun":  "Figuier maudit / Clusia",
        "famille":     "arbres",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["soir"],
        "savoir": (
            "Il commence sa vie comme épiphyte, posé sur un autre arbre, "
            "puis descend ses racines jusqu'au sol et finit par envelopper son hôte. "
            "Redouté et respecté. Les anciens y voyaient le symbole des liens "
            "qui commencent doucement et finissent par tout tenir."
        ),
    },
    {
        "nom_creole":  "mahogany",
        "nom_commun":  "Acajou à grandes feuilles / Mahogany",
        "famille":     "arbres",
        "conditions":  ["soleil", "nuageux"],
        "editions":    ["matin"],
        "savoir": (
            "Planté en allées devant les grandes habitations, il témoigne encore "
            "de cette histoire. Son bois — parmi les plus recherchés au monde — "
            "a alimenté un commerce qui a dépouillé les forêts. "
            "Le croiser, c'est lire l'histoire dans l'écorce."
        ),
    },
    {
        "nom_creole":  "mapou",
        "nom_commun":  "Mapou / Bois-savane",
        "famille":     "arbres",
        "conditions":  ["vent", "orage"],
        "editions":    ["soir"],
        "savoir": (
            "Les pêcheurs amerindiens écrasaient ses feuilles et racines dans l'eau "
            "pour étourdir les poissons — pêche traditionnelle, interdite aujourd'hui. "
            "Arbre des lisières, entre la mer et la terre. Signe des frontières "
            "et de ce qui sait vivre entre deux mondes."
        ),
    },
    {
        "nom_creole":  "corossolier",
        "nom_commun":  "Corossol / Soursop",
        "famille":     "arbres",
        "conditions":  ["chaleur", "soleil"],
        "editions":    ["soir"],
        "savoir": (
            "La tisane de feuilles de corossol est le remède du soir — "
            "elle appelle le sommeil et calme la fièvre. "
            "Son fruit énorme, hérissé, vert, cache une chair blanche et douce. "
            "Signe que l'extérieur rugueux ne dit rien de la douceur dedans."
        ),
    },
    {
        "nom_creole":  "bois-côtelette",
        "nom_commun":  "Bois-côtelette / Amargo",
        "famille":     "arbres",
        "conditions":  ["pluie"],
        "editions":    ["matin"],
        "savoir": (
            "Amer comme son nom l'indique. Sa décoction était donnée aux convalescents "
            "pour purifier le sang après une maladie. L'amertume qui soigne — "
            "ce que la médecine créole savait avant que la pharmacie arrive."
        ),
    },

    # ── Plantes & herbes médicinales ──────────────────────────────────────────

    {
        "nom_creole":  "citronnelle",
        "nom_commun":  "Citronnelle",
        "famille":     "herbes",
        "conditions":  ["chaleur", "soleil"],
        "editions":    ["soir"],
        "savoir": (
            "Plantée aux abords des cases pour éloigner les moustiques — "
            "sa tige froissée entre les paumes suffit. "
            "En tisane, elle fait tomber la fièvre. Plante de la vigilance discrète, "
            "de la protection par la seule vertu de sa présence."
        ),
    },
    {
        "nom_creole":  "verveine pays",
        "nom_commun":  "Verveine pays / Lippia",
        "famille":     "herbes",
        "conditions":  ["nuageux", "soleil"],
        "editions":    ["soir"],
        "savoir": (
            "C'est la tisane du coucher — elle calme les nerfs et appelle le sommeil. "
            "Les mères en donnaient aux enfants agités, aux adultes anxieux. "
            "Douce, sans danger, efficace. Signe qu'on peut poser ce qu'on porte."
        ),
    },
    {
        "nom_creole":  "herbe à tous maux",
        "nom_commun":  "Herbe à tous maux / Origan du pays",
        "famille":     "herbes",
        "conditions":  [],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Son nom dit tout — toux, fièvre, digestion, rhume, douleur. "
            "On la trouve dans presque chaque jardin créole. "
            "Feuille épaisse, veloutée, odeur puissante. Signe de la médecine du quotidien, "
            "de ce qui soigne sans ordonnance."
        ),
    },
    {
        "nom_creole":  "basilic",
        "nom_commun":  "Basilic grand vert",
        "famille":     "herbes",
        "conditions":  ["soleil", "chaleur"],
        "editions":    ["matin"],
        "savoir": (
            "Planté près de la porte, il protège la maison — croyance partagée "
            "de l'Inde aux Antilles. En cuisine il aromatise les court-bouillons. "
            "Son odeur seule éloigne certains insectes. "
            "Plante du seuil, de ce qui garde sans barrer."
        ),
    },
    {
        "nom_creole":  "sensitive",
        "nom_commun":  "Sensitive / Herbe qui se cache",
        "famille":     "herbes",
        "conditions":  ["soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Elle se referme au moindre contact — ses feuilles se plient, "
            "comme pour protéger ce qui est fragile en elle. "
            "Les enfants l'effleurent des heures. Signe que la sensibilité "
            "n'est pas une faiblesse, mais une intelligence du corps."
        ),
    },
    {
        "nom_creole":  "herbe à mouton",
        "nom_commun":  "Herbe bleue / Verveine bleue",
        "famille":     "herbes",
        "conditions":  ["chaleur", "soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Plante des bords de route et des terrains vagues — "
            "elle pousse où personne ne la sème. En tisane, elle fait suer "
            "et casse la fièvre. Signe de la résilience ordinaire, "
            "de ce qui soigne sans chercher les honneurs."
        ),
    },
    {
        "nom_creole":  "chadron bénit",
        "nom_commun":  "Chadron bénit / Chaya",
        "famille":     "herbes",
        "conditions":  [],
        "editions":    ["matin"],
        "savoir": (
            "Feuilles riches en fer et en protéines — cuites, elles nourrissent mieux "
            "que beaucoup d'autres légumes. Les communautés rurales en vivaient. "
            "Signe de ce qui est nutritif et accessible, si on prend la peine de regarder."
        ),
    },
    {
        "nom_creole":  "liane amère",
        "nom_commun":  "Margose / Liane amère",
        "famille":     "herbes",
        "conditions":  ["soleil", "chaleur"],
        "editions":    ["matin"],
        "savoir": (
            "Son fruit vert et ridé est un des plus amers qui soit. "
            "Les anciens en faisaient un remède contre le sucre dans le sang — "
            "la médecine moderne l'a confirmé. "
            "L'amertume qui régule, qui rééquilibre. Ce n'est pas agréable, mais ça tient."
        ),
    },
    {
        "nom_creole":  "zeb à ver",
        "nom_commun":  "Herbe à vers / Ansérine",
        "famille":     "herbes",
        "conditions":  ["nuageux"],
        "editions":    ["soir"],
        "savoir": (
            "Remède ancestral contre les parasites intestinaux — "
            "donné aux enfants chaque année, à jeun, avec du miel. "
            "Odeur forte, goût âcre, effet radical. "
            "Signe des remèdes qui font mal à prendre et du bien à faire."
        ),
    },
    {
        "nom_creole":  "herbe savon",
        "nom_commun":  "Herbe savon / Petiveria",
        "famille":     "herbes",
        "conditions":  ["pluie", "nuageux"],
        "editions":    ["matin"],
        "savoir": (
            "Son odeur — ail et terre mouillée mélangés — est reconnaissable entre mille. "
            "On l'utilisait pour les bains purificateurs, pour nettoyer ce qu'on ne voit pas. "
            "Plante de la séparation et du renouveau. Signe qu'il est temps de laisser quelque chose derrière."
        ),
    },
    {
        "nom_creole":  "ortie brûlante",
        "nom_commun":  "Ortie brûlante des Antilles",
        "famille":     "herbes",
        "conditions":  ["soleil", "chaleur"],
        "editions":    ["matin"],
        "savoir": (
            "Ses poils urticants brûlent la peau pour plusieurs heures. "
            "Mais sa décoction en cataplasme soulage les douleurs articulaires — "
            "même remède que l'agression. "
            "Signe que ce qui blesse peut aussi guérir, si on sait comment l'approcher."
        ),
    },
    {
        "nom_creole":  "ti-baume",
        "nom_commun":  "Ti-baume / Poivre des Antilles",
        "famille":     "herbes",
        "conditions":  ["pluie"],
        "editions":    ["soir"],
        "savoir": (
            "Ses feuilles froissées libèrent un arôme poivré et boisé. "
            "On les glissait sous l'oreiller pour éloigner les mauvais rêves. "
            "Les guérisseurs s'en servaient pour les bains de chance. "
            "Signe de la protection nocturne, de ce qui veille pendant qu'on dort."
        ),
    },
    {
        "nom_creole":  "canne rivière",
        "nom_commun":  "Canne rivière / Costus",
        "famille":     "herbes",
        "conditions":  ["pluie", "nuageux"],
        "editions":    ["matin"],
        "savoir": (
            "Elle pousse en spirale — ses feuilles s'enroulent autour d'une tige unique. "
            "Sa sève calmait les irritations de la gorge et les toux sèches. "
            "Plante des bords de ruisseau, de l'ombre fraîche. Signe de la fluidité, "
            "de ce qui trouve toujours son chemin vers l'eau."
        ),
    },
    {
        "nom_creole":  "herbe à pic",
        "nom_commun":  "Herbe à pic / Bident",
        "famille":     "herbes",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["matin"],
        "savoir": (
            "Ses graines s'accrochent aux vêtements et aux poils des animaux — "
            "elle voyage ainsi partout où passent les vivants. "
            "Ses feuilles en cataplasme cicatrisaient les petites plaies. "
            "Plante tenace, voyageuse, soignante. Signe des liens qui tiennent sans qu'on les cherche."
        ),
    },
    {
        "nom_creole":  "raisinier bord de mer",
        "nom_commun":  "Raisinier bord de mer",
        "famille":     "herbes",
        "conditions":  ["vent", "soleil"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Ses grandes feuilles rondes et coriaces résistent aux embruns et au vent marin. "
            "Ses baies violettes se mangeaient et servaient à faire une boisson fermentée. "
            "Signe de la résistance en bord de mer, de ce qui tient face à ce qui érode."
        ),
    },
    {
        "nom_creole":  "passiflore",
        "nom_commun":  "Passiflore / Grenadille",
        "famille":     "herbes",
        "conditions":  ["soleil"],
        "editions":    ["soir"],
        "savoir": (
            "Sa fleur complexe — couronne, étamines, pistil — impressionna les missionnaires "
            "qui y virent les symboles de la Passion. En tisane, ses feuilles calment "
            "l'anxiété et facilitent le sommeil. Signe de la beauté qui apaise."
        ),
    },
    {
        "nom_creole":  "liane de mer",
        "nom_commun":  "Patate bord de mer / Ipomoée",
        "famille":     "herbes",
        "conditions":  ["vent", "soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Elle rampe sur le sable et fixe les dunes — ses racines retiennent "
            "ce que la mer voudrait emporter. Fleur mauve qui s'ouvre le matin "
            "et se ferme à midi. Signe de la brièveté des beaux moments, "
            "et de la force de ce qui s'ancre."
        ),
    },
    {
        "nom_creole":  "herbe chapelet",
        "nom_commun":  "Herbe chapelet / Leonotis",
        "famille":     "herbes",
        "conditions":  ["soleil", "nuageux"],
        "editions":    ["matin"],
        "savoir": (
            "Ses fleurs orangées s'étageaient en étages réguliers autour de la tige — "
            "comme les grains d'un chapelet. En décoction, contre la fièvre et la toux. "
            "Plante des jardins anciens, de plus en plus rare. Signe de ce qu'on a failli perdre."
        ),
    },
    {
        "nom_creole":  "herbe grasse",
        "nom_commun":  "Pourpier / Herbe grasse",
        "famille":     "herbes",
        "conditions":  ["chaleur", "soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Elle pousse dans les terrains secs où rien d'autre ne survit. "
            "Comestible — ses feuilles charnues en salade ou sautées à l'huile. "
            "Plante de l'endurance, de la discrète résistance à ce qui dessèche."
        ),
    },
    {
        "nom_creole":  "sénevé",
        "nom_commun":  "Sénevé pays / Cléome",
        "famille":     "herbes",
        "conditions":  ["pluie", "nuageux"],
        "editions":    ["matin"],
        "savoir": (
            "Plante des jardins vivriers — ses jeunes pousses se mangeaient en légume, "
            "ses graines entraient dans certains préparations médicinales. "
            "Odeur forte, présence discrète. Signe de ce qui nourrit sans s'imposer."
        ),
    },

    # ── Fleurs & ornementales ─────────────────────────────────────────────────

    {
        "nom_creole":  "balisier",
        "nom_commun":  "Balisier / Heliconia",
        "famille":     "fleurs",
        "conditions":  ["pluie", "nuageux"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Ses grandes feuilles servaient à envelopper et couvrir les plats des fêtes. "
            "Plante de l'abondance et du partage — on la trouve aux abords des sources "
            "et des rivières. Signe de ce qui donne sans compter, "
            "de la fête qu'on prépare en silence."
        ),
    },
    {
        "nom_creole":  "frangipanier",
        "nom_commun":  "Frangipanier / Plumeria",
        "famille":     "fleurs",
        "conditions":  ["chaleur", "soleil"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Il fleurit blanc et jaune, avec un parfum qui traverse la nuit. "
            "Planté dans les cimetières — fleur de la mort et de la renaissance. "
            "Mais aussi fleur de fête, de mariage. Signe que beauté et deuil "
            "coexistent, que le parfum ne choisit pas son moment."
        ),
    },
    {
        "nom_creole":  "bougainvillier",
        "nom_commun":  "Bougainvillier",
        "famille":     "fleurs",
        "conditions":  ["soleil", "vent"],
        "editions":    ["matin"],
        "savoir": (
            "Il grimpe sur tout — murs, grillages, arbres morts — et fleurit "
            "sans qu'on lui demande. Ses bractées colorées ne sont pas des pétales "
            "mais des feuilles modifiées. La beauté peut être une illusion bien construite. "
            "Signe de la tenacité qui habille les ruines."
        ),
    },
    {
        "nom_creole":  "hibiscus",
        "nom_commun":  "Hibiscus / Foulsapate",
        "famille":     "fleurs",
        "conditions":  ["soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Sa fleur ne dure qu'un jour — ouverte le matin, tombée le soir. "
            "En tisane, ses fleurs séchées donnent une boisson rouge acidulée "
            "qui fait baisser la tension. Signe de la beauté éphémère "
            "et de ce qui a quand même de la valeur parce qu'il a existé."
        ),
    },
    {
        "nom_creole":  "anthurium",
        "nom_commun":  "Anthurium",
        "famille":     "fleurs",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["matin"],
        "savoir": (
            "Fleur de l'accueil et de l'hospitalité en Guadeloupe — "
            "on l'offre aux visiteurs, aux cérémonies. Sa spathe laquée rouge "
            "ne fane presque pas. Signe de la chaleur du seuil, "
            "de ce qu'on tend à l'autre en guise de bienvenue."
        ),
    },
    {
        "nom_creole":  "oiseau de paradis",
        "nom_commun":  "Oiseau de paradis / Strelitzia",
        "famille":     "fleurs",
        "conditions":  ["soleil", "chaleur"],
        "editions":    ["matin"],
        "savoir": (
            "Sa fleur imite exactement un oiseau en vol — bec orange, ailes bleues. "
            "Pollinisée par les oiseaux-mouches qui se posent sur la spathe. "
            "Signe de la beauté fonctionnelle, de la forme qui naît du besoin."
        ),
    },
    {
        "nom_creole":  "alamanda",
        "nom_commun":  "Alamanda jaune",
        "famille":     "fleurs",
        "conditions":  ["soleil", "chaleur"],
        "editions":    ["matin"],
        "savoir": (
            "Fleur jaune vif, liane vigoureuse — elle s'installe et ne part plus. "
            "Toutes ses parties sont toxiques si ingérées, malgré sa beauté affichée. "
            "Signe d'admirer sans tout toucher, de respecter ce qui dit clairement ses limites."
        ),
    },
    {
        "nom_creole":  "ixora",
        "nom_commun":  "Ixora / Bois de perdrix",
        "famille":     "fleurs",
        "conditions":  ["soleil"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Ses fleurs rouge vif poussent en boules denses — les enfants en suçaient "
            "le nectar sucré. Plante des haies et des cérémonies, "
            "associée au feu sacré dans plusieurs traditions hindoues présentes aux Antilles. "
            "Signe de la petite douceur accessible à tous."
        ),
    },
    {
        "nom_creole":  "brunfelsia",
        "nom_commun":  "Hier, aujourd'hui, demain",
        "famille":     "fleurs",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["soir"],
        "savoir": (
            "Elle porte ce nom parce que ses fleurs changent de couleur — "
            "violettes le premier jour, mauves le deuxième, blanches le troisième. "
            "Ce qui était intense hier s'apaise. Signe du temps qui transforme "
            "sans effacer, de la beauté dans chaque étape."
        ),
    },
    {
        "nom_creole":  "gloire du matin",
        "nom_commun":  "Belle de jour / Ipomée",
        "famille":     "fleurs",
        "conditions":  ["soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Elle s'ouvre à l'aube et se ferme avant midi — fleur du lever, "
            "pas du plein jour. Liane légère qui monte sur n'importe quel support. "
            "Signe du commencement, de la beauté des premières heures "
            "avant que la journée s'installe."
        ),
    },
    {
        "nom_creole":  "liane papillon",
        "nom_commun":  "Patte de vache / Bauhinie",
        "famille":     "fleurs",
        "conditions":  ["nuageux"],
        "editions":    ["matin"],
        "savoir": (
            "Sa feuille est découpée en deux lobes — comme l'empreinte d'un sabot, "
            "ou les ailes d'un papillon posé. Fleur rose tendre, légère. "
            "Son écorce en décoction régulait le diabète selon la médecine traditionnelle. "
            "Signe de la douceur qui soigne."
        ),
    },
    {
        "nom_creole":  "corail",
        "nom_commun":  "Russelia / Corail végétal",
        "famille":     "fleurs",
        "conditions":  ["soleil", "chaleur"],
        "editions":    ["matin"],
        "savoir": (
            "Ses tiges retombantes et ses petites fleurs tubulaires rouge vif "
            "imitent le corail des fonds marins. Elle fleurit presque toute l'année "
            "sans s'épuiser. Signe de la constance, de l'effort qui ne fait pas de bruit."
        ),
    },
    {
        "nom_creole":  "poinsettia",
        "nom_commun":  "Poinsettia / Étoile de Noël",
        "famille":     "fleurs",
        "conditions":  ["nuageux", "vent"],
        "editions":    ["soir"],
        "savoir": (
            "Il fleurit quand les nuits s'allongent — plante du court du jour, "
            "de la saison sèche. Ses bractées rouges sont des feuilles transformées. "
            "Signe de la générosité dans la contrainte, de l'éclat qu'on garde "
            "même quand la lumière diminue."
        ),
    },
    {
        "nom_creole":  "pervenche pays",
        "nom_commun":  "Pervenche de Madagascar / Catharanthus",
        "famille":     "fleurs",
        "conditions":  ["chaleur", "soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Petite fleur rose ou blanche des bords de route — personne ne la remarque. "
            "Pourtant ses alcaloïdes ont révolutionné le traitement de certains cancers. "
            "Signe que la science vient parfois de ce qu'on piétine sans regarder."
        ),
    },
    {
        "nom_creole":  "plumbago",
        "nom_commun":  "Plumbago / Dentelaire",
        "famille":     "fleurs",
        "conditions":  ["soleil", "nuageux"],
        "editions":    ["matin"],
        "savoir": (
            "Fleurs bleu pâle en grappes légères — couleur rare dans la flore antillaise. "
            "Plante des haies discrètes, qui dure sans attention particulière. "
            "Signe de la modestie qui persiste, de la beauté qui ne réclame pas de témoin."
        ),
    },
    {
        "nom_creole":  "noni",
        "nom_commun":  "Noni / Morinda",
        "famille":     "fleurs",
        "conditions":  [],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Son fruit fermenté sent fort — très fort. "
            "Pourtant la médecine polynésienne et caribéenne en faisait un tonique universel. "
            "Signe que ce qui guérit ne cherche pas à plaire, "
            "que l'efficacité n'a pas besoin d'être agréable."
        ),
    },
    {
        "nom_creole":  "cactus raquette",
        "nom_commun":  "Raquette / Opuntia",
        "famille":     "fleurs",
        "conditions":  ["chaleur", "vent"],
        "editions":    ["matin"],
        "savoir": (
            "Il pousse dans les zones les plus arides du littoral, là où rien d'autre ne tient. "
            "Sa raquette charnue stocke l'eau pour des semaines. "
            "Les oiseaux nichent entre ses épines, protégés par ce qui blesse les autres. "
            "Signe de la forteresse hospitalière."
        ),
    },
    {
        "nom_creole":  "oiseau du paradis géant",
        "nom_commun":  "Balisier blanc / Strelitzia nicolai",
        "famille":     "fleurs",
        "conditions":  ["pluie", "nuageux"],
        "editions":    ["soir"],
        "savoir": (
            "Fleur blanche et bleu nuit, architecture silencieuse dans les jardins ombragés. "
            "Moins spectaculaire que son cousin orange, mais plus stable, plus profond. "
            "Signe des beautés qui préfèrent la nuit et ne cherchent pas le soleil de plein face."
        ),
    },
    {
        "nom_creole":  "ti-nito",
        "nom_commun":  "Portulacaria / Plante grasse bord de mer",
        "famille":     "fleurs",
        "conditions":  ["vent", "soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Plante charnue des falaises et des côtes rocheuses — "
            "ses petites feuilles brillantes résistent aux embruns salés. "
            "Elle fixe les éboulis et empêche l'érosion. "
            "Signe du courage des petits — ceux qui tiennent là où les grands ne peuvent pas."
        ),
    },

    # ── Épices & cultures vivrières ───────────────────────────────────────────

    {
        "nom_creole":  "vanille",
        "nom_commun":  "Vanille",
        "famille":     "vivriers",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["matin"],
        "savoir": (
            "Chaque fleur ne s'ouvre qu'une journée — et doit être pollinisée à la main, "
            "fleur par fleur, dans les quelques heures de l'ouverture. "
            "Puis neuf mois d'attente avant la gousse. "
            "Signe de la patience totale, du travail qui ne triche pas."
        ),
    },
    {
        "nom_creole":  "cacaoyer",
        "nom_commun":  "Cacaoyer / Cacao",
        "famille":     "vivriers",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["matin"],
        "savoir": (
            "Ses fruits poussent directement sur le tronc — cauliflore, "
            "phénomène rare et étrange. Les Mayas en faisaient la boisson des dieux "
            "et une monnaie d'échange. Ici il a nourri une économie de plantation. "
            "Signe de la valeur que les autres mettent sur ce que tu portes."
        ),
    },
    {
        "nom_creole":  "igname",
        "nom_commun":  "Igname / Yam",
        "famille":     "vivriers",
        "conditions":  ["pluie"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Tubercule de l'ancrage — on l'enterre au début de la saison des pluies "
            "et on la déterre à la sèche. La Fête des cuisinières en Guadeloupe "
            "honore encore les femmes qui l'ont cuisinée pour nourrir les familles. "
            "Signe des racines, de ce qu'on garde sous la terre pour les jours durs."
        ),
    },
    {
        "nom_creole":  "giraumon",
        "nom_commun":  "Giraumon / Courge caraïbe",
        "famille":     "vivriers",
        "conditions":  ["soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Grand, lourd, orange dedans — il nourrit une famille entière. "
            "Soupe de giraumon, le plat des jours de repos et des grandes tablées. "
            "Sa tige rampe loin et couvre tout ce qu'elle trouve. "
            "Signe de l'abondance qui partage l'espace généreusement."
        ),
    },
    {
        "nom_creole":  "christophine",
        "nom_commun":  "Chayote / Christophine",
        "famille":     "vivriers",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["soir"],
        "savoir": (
            "Liane vigoureuse qui monte très haut très vite — elle couvre les tonnelles "
            "en quelques semaines. Son fruit se mange cru, cuit, gratiné. "
            "Tout se mange : le fruit, la tige, la feuille, la racine. "
            "Signe de la générosité sans reste."
        ),
    },
    {
        "nom_creole":  "gombo",
        "nom_commun":  "Gombo / Okra",
        "famille":     "vivriers",
        "conditions":  ["chaleur", "soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Il est arrivé d'Afrique dans les mains des captifs — soigneusement "
            "gardé pour garder un peu du pays. Son mucilage lie les sauces. "
            "Il lie aussi les histoires. Signe du souvenir porté malgré tout, "
            "de la culture qui traverse l'ocean dans une graine."
        ),
    },
    {
        "nom_creole":  "piment antillais",
        "nom_commun":  "Piment sept-feux / Habanero",
        "famille":     "vivriers",
        "conditions":  ["chaleur", "soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Le plus fort qui soit — quelques gouttes suffisent. "
            "Mais il contient plus de vitamine C que n'importe quel agrume. "
            "Arme et remède à la fois. Signe que ce qui vous met à l'épreuve "
            "peut aussi vous fortifier."
        ),
    },
    {
        "nom_creole":  "gingembre",
        "nom_commun":  "Gingembre / Ginger",
        "famille":     "vivriers",
        "conditions":  ["pluie", "nuageux"],
        "editions":    ["matin"],
        "savoir": (
            "Son rhizome noueux, sous la terre, accumule la chaleur. "
            "En tisane il réchauffe, stimule, chasse le rhume. "
            "En cuisine il relève sans dominer. "
            "Signe du feu intérieur, de la chaleur qu'on garde en soi par n'importe quel temps."
        ),
    },
    {
        "nom_creole":  "curcuma",
        "nom_commun":  "Curcuma / Safran pays",
        "famille":     "vivriers",
        "conditions":  ["soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Sa poudre jaune dorée teint les doigts, les tisanes, les currys. "
            "Anti-inflammatoire puissant connu depuis des millénaires en Asie et aux Antilles. "
            "Signe de l'or discret, de ce qui vaut beaucoup sans briller comme l'or."
        ),
    },
    {
        "nom_creole":  "cannelle",
        "nom_commun":  "Cannelle / Cannelier",
        "famille":     "vivriers",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["soir"],
        "savoir": (
            "On écorce le cannelier en spirales fines qui sèchent et s'enroulent. "
            "Son arôme doux et chaud était utilisé pour les bains de purification "
            "et les préparations contre le mal de tête. "
            "Signe de la douceur qui protège, de ce qui réconforte quand il fait gris."
        ),
    },
    {
        "nom_creole":  "muscade",
        "nom_commun":  "Muscadier / Noix muscade",
        "famille":     "vivriers",
        "conditions":  ["nuageux"],
        "editions":    ["soir"],
        "savoir": (
            "Deux épices en une — la noix et le macis, la membrane rouge qui l'entoure. "
            "Elle a alimenté des guerres commerciales au XVIIe siècle. "
            "Narcotique à haute dose, condiment subtil en petite quantité. "
            "Signe que la valeur des choses dépend de la mesure qu'on y met."
        ),
    },
    {
        "nom_creole":  "patate douce",
        "nom_commun":  "Patate douce",
        "famille":     "vivriers",
        "conditions":  [],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Nourriture de survie — elle pousse dans les sols les plus pauvres "
            "sans beaucoup d'eau. Les esclaves marrons en cultivaient dans les bois. "
            "Bouillée, rôtie, en soupe — elle nourrit simplement et bien. "
            "Signe de la dignité de ce qui sustente sans faire d'histoires."
        ),
    },
    {
        "nom_creole":  "manioc",
        "nom_commun":  "Manioc / Cassave",
        "famille":     "vivriers",
        "conditions":  ["chaleur"],
        "editions":    ["matin"],
        "savoir": (
            "Sa racine contient de l'acide cyanhydrique — mortelle crue, "
            "inoffensive après transformation. Les Amérindiens savaient râper, "
            "presser, cuire pour en faire la cassave. Savoir ancien, transmission exacte. "
            "Signe que certaines connaissances ne se devinent pas, elles se transmettent."
        ),
    },
    {
        "nom_creole":  "banane",
        "nom_commun":  "Bananier / Banane",
        "famille":     "vivriers",
        "conditions":  ["pluie", "vent"],
        "editions":    ["matin"],
        "savoir": (
            "Une fois qu'il a porté son régime, le bananier meurt — "
            "mais un rejet reprend à sa base. Toujours une génération pour continuer. "
            "Ses grandes feuilles servaient de nappe, d'assiette, de couverture provisoire. "
            "Signe de la générosité jusqu'au bout, et du recommencement assuré."
        ),
    },
    {
        "nom_creole":  "ananas",
        "nom_commun":  "Ananas",
        "famille":     "vivriers",
        "conditions":  ["soleil", "chaleur"],
        "editions":    ["matin"],
        "savoir": (
            "Posé devant la porte, il signifiait l'accueil dans toute la Caraïbe amérindienne. "
            "Les Européens en ont fait le symbole de l'hospitalité des grandes maisons. "
            "Son enzyme — la bromélaïne — attendrit les viandes et digère les protéines. "
            "Signe que ce qui est beau peut aussi être utile."
        ),
    },
    {
        "nom_creole":  "café",
        "nom_commun":  "Caféier / Café",
        "famille":     "vivriers",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["matin"],
        "savoir": (
            "Il pousse dans l'ombre des arbres de montagne — pas en plein soleil. "
            "Ses cerises rouges se cueillent à la main, une par une, à maturité. "
            "Ce qui éveille les autres préfère lui-même l'ombre et la lenteur. "
            "Signe de ce qui donne l'élan sans chercher les projecteurs."
        ),
    },
    {
        "nom_creole":  "canne à sucre",
        "nom_commun":  "Canne à sucre",
        "famille":     "vivriers",
        "conditions":  ["soleil", "vent"],
        "editions":    ["matin", "soir"],
        "savoir": (
            "La douceur la plus chèrement payée de l'histoire. "
            "Son jus fermente en rhum — mémoire transformée en eau-de-vie. "
            "Les champs qui ondulent sous le vent ont vu des siècles d'une histoire dure. "
            "Signe de la complexité des choses simples, de la mémoire dans chaque sillon."
        ),
    },
    {
        "nom_creole":  "maïs",
        "nom_commun":  "Maïs",
        "famille":     "vivriers",
        "conditions":  ["soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Plante du partage — on ne plante jamais un seul rang. "
            "La récolte se fait collectivement, en lévé-tèt. "
            "Grillé, bouilli, en akra — il prend toutes les formes. "
            "Signe de l'abondance qui se multiplie quand elle est partagée."
        ),
    },
    {
        "nom_creole":  "papaye",
        "nom_commun":  "Papayer / Papaye",
        "famille":     "vivriers",
        "conditions":  ["chaleur", "soleil"],
        "editions":    ["matin"],
        "savoir": (
            "Elle pousse vite, donne rapidement, vit peu. "
            "Sa sève blanche attendrit les viandes — les cuisinières l'utilisaient "
            "pour les ragoûts des jours de fête. Sa feuille en tisane régulait la fièvre. "
            "Signe de la générosité courte mais intense."
        ),
    },
    {
        "nom_creole":  "café pays",
        "nom_commun":  "Café marron / Psychotria",
        "famille":     "vivriers",
        "conditions":  ["nuageux", "pluie"],
        "editions":    ["soir"],
        "savoir": (
            "Cousin sauvage du caféier, sans caféine, qui pousse en sous-bois. "
            "Ses petites fleurs blanches parfument discrètement la forêt humide. "
            "Ses baies rouges nourrissaient les oiseaux de montagne. "
            "Signe de ce qui ressemble à ce qu'on connaît mais est autre chose — "
            "l'invitation à regarder de plus près."
        ),
    },
    {
        "nom_creole":  "ti-noni",
        "nom_commun":  "Noni des Antilles",
        "famille":     "vivriers",
        "conditions":  [],
        "editions":    ["matin", "soir"],
        "savoir": (
            "Arbre robuste des zones côtières sèches — son fruit bulleux et malodorant "
            "était pourtant consommé en période de disette. "
            "Ses feuilles larges servaient d'emplâtre sur les plaies. "
            "Signe de la ressource là où on ne l'attend pas, de l'utile dans le repoussant."
        ),
    },
]
