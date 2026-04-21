"""Tests unitaires des 14 fonctions de normalisation TTS.

Lancement :
    python -m unittest tests.test_normalize -v

Les tests documentent le comportement *actuel* (y compris ses quirks). Si
vous corrigez un bug dans une fonction `_norm_*`, mettez le test à jour
en même temps.
"""

import importlib.util
import os
import sys
import unittest
from pathlib import Path

# ── Chargement du module principal (nom avec tiret → importlib.util) ─────────

_PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT))

# Valeurs factices au cas où .env ne serait pas présent (CI, clean clone…).
# _load_env utilise setdefault donc les vraies valeurs gagnent si .env existe.
for _key in (
    "MISTRAL_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
    "BUZZSPROUT_API_TOKEN", "BUZZSPROUT_PODCAST_ID",
    "X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET",
):
    os.environ.setdefault(_key, "dummy_for_tests")

_spec = importlib.util.spec_from_file_location(
    "flash_info_gwada", _PROJECT / "flash-info-gwada.py"
)
fi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fi)


# ── 0. Prononciations locales ────────────────────────────────────────────────

class TestPronunciations(unittest.TestCase):
    def test_lyannaj_substitue(self):
        self.assertEqual(
            fi._norm_pronunciations("Un Lyannaj à Vieux-Habitants"),
            "Un Lyan naje à Vieux Zabitan",
        )

    def test_lyannaj_minuscule(self):
        self.assertEqual(fi._norm_pronunciations("lyannaj"), "Lyan naje")

    def test_delgres_force_le_s_final(self):
        self.assertIn("Delgrèsse", fi._norm_pronunciations("hommage à Delgrès"))

    def test_henri_iv_est_developpe(self):
        self.assertEqual(
            fi._norm_pronunciations("cité Henri IV"),
            "cité Henri Quatre",
        )

    def test_henri_4_est_developpe(self):
        self.assertEqual(fi._norm_pronunciations("Henri 4"), "Henri Quatre")

    def test_971_filet_de_securite(self):
        self.assertEqual(fi._norm_pronunciations("971"), "quatre-vingt-dix-sept-un")

    def test_sdis_developpe(self):
        self.assertIn(
            "Service Départemental d'Incendie et de Secours",
            fi._norm_pronunciations("le SDIS est intervenu"),
        )

    def test_sigles_locaux_developpes(self):
        out = fi._norm_pronunciations("UNAR vs JSVH")
        self.assertIn("Union Athlétique de Rivière-des-Pères", out)
        self.assertIn("Jeunesse Sportive de Vieux Zabitan", out)

    def test_clubs_athletisme(self):
        cases = {
            "ACBM":  "Athlétic Club de Baie-Mahault",
            "ARA":   "Athletic Racing des Abymes",
            "BPA":   "Bik Pointois d'Athlétisme de Pointe-à-Pitre",
            "GAC":   "Gosier Athlétic Club du Gosier",
            "JSA":   "Jeunesse Sportive Abymienne des Abymes",
            "NGTAC": "Nord Grande-Terre Athlétic Club de Port-Louis",
            "USBM":  "Union Sportive de Baie-Mahault",
        }
        for sigle, nom in cases.items():
            with self.subTest(sigle=sigle):
                self.assertIn(nom, fi._norm_pronunciations(sigle))

    def test_clubs_cyclisme(self):
        cases = {
            "CRCIG": "Comité Régional de Cyclisme des Îles de Guadeloupe",
            "VCN":   "Vélo Club du Nord d'Anse-Bertrand",
            "VO2C":  "Vélo d'Or du Centre et de la Caraïbe",
        }
        for sigle, nom in cases.items():
            with self.subTest(sigle=sigle):
                self.assertIn(nom, fi._norm_pronunciations(sigle))

    def test_instances_federales(self):
        self.assertIn("Ligue Guadeloupéenne d'Athlétisme",
                      fi._norm_pronunciations("LGA"))
        self.assertIn("Ligue Régionale d'Athlétisme de la Guadeloupe",
                      fi._norm_pronunciations("LRAG"))
        self.assertIn("Ligue Guadeloupéenne de Football",
                      fi._norm_pronunciations("LGF"))


# ── 1. Typographie ──────────────────────────────────────────────────────────

class TestTypography(unittest.TestCase):
    def test_apostrophe_typographique(self):
        self.assertEqual(fi._norm_typography("aujourd’hui"), "aujourd'hui")

    def test_guillemets_typographiques(self):
        self.assertEqual(fi._norm_typography("“hello”"), '"hello"')

    def test_en_dash_devient_tiret(self):
        self.assertEqual(fi._norm_typography("a – b"), "a - b")

    def test_em_dash_devient_espace(self):
        # em-dash est remplacé par espace, les espaces autour sont préservés
        self.assertEqual(fi._norm_typography("a — b"), "a   b")

    def test_emoji_hors_latin_devient_espace(self):
        self.assertEqual(fi._norm_typography("hello 🌴"), "hello  ")

    def test_accents_francais_preserves(self):
        self.assertEqual(fi._norm_typography("école à Pointe-à-Pitre"),
                         "école à Pointe-à-Pitre")

    def test_degre_et_euro_ne_sont_PAS_dans_les_plages_latines(self):
        # Quirk documenté : ° (U+00B0) et € (U+20AC) sont hors des plages
        # conservées → ils sont effacés AVANT que _norm_units / _norm_currencies
        # aient pu les traiter (quand la pipeline tourne complète).
        # Testés isolément ici pour documenter le comportement.
        self.assertEqual(fi._norm_typography("25°C"), "25 C")
        self.assertEqual(fi._norm_typography("100€"), "100 ")


# ── 2. n° / N° → numéro ─────────────────────────────────────────────────────

class TestNumero(unittest.TestCase):
    def test_minuscule(self):
        self.assertEqual(fi._norm_numero("n° 5"), "numéro 5")

    def test_sans_espace(self):
        self.assertEqual(fi._norm_numero("n°42"), "numéro 42")

    def test_IGNORECASE_ramene_en_minuscule(self):
        # Quirk : la première sub() est IGNORECASE et intercepte aussi "N°",
        # donc la seconde sub() (qui viserait "Numéro" avec majuscule) est
        # dead code. Résultat : "N°" devient "numéro" (minuscule), pas "Numéro".
        self.assertEqual(fi._norm_numero("N° 5"), "numéro 5")
        self.assertEqual(fi._norm_numero("Le N°1 mondial"), "Le numéro 1 mondial")


# ── 3. Ordinaux ─────────────────────────────────────────────────────────────

class TestOrdinals(unittest.TestCase):
    def test_1er(self):
        self.assertEqual(fi._norm_ordinals("1er rang"), "premier rang")

    def test_1re(self):
        self.assertEqual(fi._norm_ordinals("1re place"), "première place")

    def test_2e(self):
        self.assertEqual(fi._norm_ordinals("2e position"), "deuxième position")

    def test_3eme(self):
        self.assertEqual(fi._norm_ordinals("3ème tour"), "troisième tour")

    def test_4eme_sans_accent(self):
        self.assertEqual(fi._norm_ordinals("4eme étage"), "quatrième étage")

    def test_21eme(self):
        self.assertEqual(fi._norm_ordinals("21ème siècle"), "vingt et unième siècle")


# ── 4. Monnaies ─────────────────────────────────────────────────────────────

class TestCurrencies(unittest.TestCase):
    def test_euro_simple(self):
        self.assertEqual(fi._norm_currencies("15€"), "quinze euros")

    def test_euro_avec_espace(self):
        self.assertEqual(fi._norm_currencies("100 €"), "cent euros")

    def test_millions_euros(self):
        self.assertEqual(fi._norm_currencies("2M€"), "deux millions d'euros")

    def test_millions_euros_decimal(self):
        self.assertEqual(
            fi._norm_currencies("3,5M€"),
            "trois virgule cinq millions d'euros",
        )

    def test_dollar(self):
        self.assertEqual(fi._norm_currencies("20$"), "vingt dollars")

    def test_3_millions_sans_symbole_inchange(self):
        # Pas de pattern pour "3 millions" (sans €/$) → inchangé ici
        self.assertEqual(fi._norm_currencies("3 millions"), "3 millions")


# ── 5. Scores sportifs ──────────────────────────────────────────────────────

class TestScores(unittest.TestCase):
    def test_score_simple(self):
        self.assertEqual(fi._norm_scores("3-1"), "trois à un")

    def test_score_nul(self):
        self.assertEqual(fi._norm_scores("0-0"), "zéro à zéro")

    def test_score_dans_phrase(self):
        self.assertEqual(fi._norm_scores("victoire 3-1"), "victoire trois à un")

    def test_score_deux_chiffres(self):
        self.assertEqual(fi._norm_scores("10-15"), "dix à quinze")


# ── 6. Codes départementaux DOM ─────────────────────────────────────────────

class TestDomCodes(unittest.TestCase):
    def test_971(self):
        self.assertEqual(fi._norm_dom_codes("971"), "quatre-vingt-dix-sept-un")

    def test_972(self):
        self.assertEqual(fi._norm_dom_codes("972"), "quatre-vingt-dix-sept-deux")

    def test_973(self):
        self.assertEqual(fi._norm_dom_codes("973"), "quatre-vingt-dix-sept-trois")

    def test_974(self):
        self.assertEqual(fi._norm_dom_codes("974"), "quatre-vingt-dix-sept-quatre")

    def test_976(self):
        self.assertEqual(fi._norm_dom_codes("976"), "quatre-vingt-dix-sept-six")

    def test_970_inchange(self):
        self.assertEqual(fi._norm_dom_codes("970"), "970")

    def test_dans_phrase(self):
        self.assertEqual(
            fi._norm_dom_codes("Département 971."),
            "Département quatre-vingt-dix-sept-un.",
        )


# ── 7. Heures ───────────────────────────────────────────────────────────────

class TestHours(unittest.TestCase):
    def test_heure_zero_padded(self):
        self.assertEqual(fi._norm_hours("07h30"), "sept heures trente")

    def test_heure_sans_zero(self):
        self.assertEqual(fi._norm_hours("9h05"), "neuf heures cinq")

    def test_heure_pleine_donne_zero(self):
        # Quirk : 18h00 → "dix-huit heures zéro" (num2words de 00 = "zéro"),
        # pas juste "dix-huit heures". C'est lu tel quel à l'antenne.
        self.assertEqual(fi._norm_hours("18h00"), "dix-huit heures zéro")

    def test_heure_tardive(self):
        self.assertEqual(fi._norm_hours("23h59"), "vingt-trois heures cinquante-neuf")


# ── 7bis. Nombres avec unités ───────────────────────────────────────────────

class TestUnits(unittest.TestCase):
    def test_temperature(self):
        self.assertEqual(fi._norm_units("25°C"), "vingt-cinq degrés")

    def test_vitesse(self):
        self.assertEqual(fi._norm_units("80km/h"), "quatre-vingts kilomètres par heure")

    def test_distance_km(self):
        self.assertEqual(fi._norm_units("10km"), "dix kilomètres")

    def test_distance_mm(self):
        self.assertEqual(fi._norm_units("45mm"), "quarante-cinq millimètres")

    def test_pourcentage(self):
        self.assertEqual(fi._norm_units("50%"), "cinquante pour cent")

    def test_surface(self):
        self.assertEqual(fi._norm_units("100m²"), "cent mètres carrés")

    def test_decimal(self):
        self.assertEqual(fi._norm_units("3,5mm"), "trois virgule cinq millimètres")


# ── 8. Nombres isolés ───────────────────────────────────────────────────────

class TestPlainNumbers(unittest.TestCase):
    def test_nombre_simple(self):
        self.assertEqual(fi._norm_plain_numbers("12"), "douze")

    def test_annee(self):
        self.assertEqual(fi._norm_plain_numbers("2026"), "deux mille vingt-six")

    def test_decimal(self):
        self.assertEqual(fi._norm_plain_numbers("3,5"), "trois virgule cinq")

    def test_texte_sans_nombre_inchange(self):
        self.assertEqual(fi._norm_plain_numbers("abc"), "abc")

    def test_nombre_dans_phrase(self):
        self.assertEqual(
            fi._norm_plain_numbers("le 7 avril"),
            "le sept avril",
        )

    def test_espace_insecable_groupe_les_chiffres(self):
        # Avec NBSP (U+00A0), les milliers sont groupés correctement.
        self.assertEqual(
            fi._norm_plain_numbers("12 500"),
            "douze mille cinq cents",
        )

    def test_espace_normal_ne_groupe_PAS(self):
        # Quirk : la regex ne connaît que NBSP pour grouper les milliers.
        # "12 500" avec espace normal → deux nombres distincts.
        self.assertEqual(
            fi._norm_plain_numbers("12 500"),
            "douze cinq cents",
        )


# ── 9. Sigles / acronymes ───────────────────────────────────────────────────

class TestAcronyms(unittest.TestCase):
    def test_rci_pointille_devient_compact(self):
        self.assertEqual(fi._norm_acronyms("R.C.I"), "RCI")

    def test_rci_pointille_avec_point_final(self):
        self.assertEqual(fi._norm_acronyms("R.C.I."), "RCI")

    def test_rci_compact_inchange(self):
        self.assertEqual(fi._norm_acronyms("RCI"), "RCI")

    def test_nasa_inchange(self):
        self.assertEqual(fi._norm_acronyms("NASA"), "NASA")

    def test_unesco_inchange(self):
        self.assertEqual(fi._norm_acronyms("UNESCO"), "UNESCO")

    def test_chu_est_epele(self):
        self.assertEqual(fi._norm_acronyms("CHU"), "C. H. U.")

    def test_chu_dans_phrase(self):
        self.assertEqual(
            fi._norm_acronyms("le CHU de Pointe-à-Pitre"),
            "le C. H. U. de Pointe-à-Pitre",
        )

    def test_sdis_pointille_sans_point_final(self):
        self.assertEqual(fi._norm_acronyms("S.D.I.S"), "S. D. I. S.")

    def test_sdis_pointille_avec_point_final_produit_double_point(self):
        # Quirk : la regex 9b capture "S.D.I.S" sans consommer le "." final,
        # ajoute son propre "." → "S. D. I. S." + "." restant = "S. D. I. S..".
        self.assertEqual(fi._norm_acronyms("S.D.I.S."), "S. D. I. S..")


# ── 10. Abréviations ────────────────────────────────────────────────────────

class TestAbbreviations(unittest.TestCase):
    def test_monsieur(self):
        self.assertEqual(fi._norm_abbreviations("M. Dupont"), "Monsieur Dupont")

    def test_madame_avec_point(self):
        self.assertEqual(fi._norm_abbreviations("Mme. Smith"), "Madame Smith")

    def test_madame_sans_point(self):
        self.assertEqual(fi._norm_abbreviations("Mme Smith"), "Madame Smith")

    def test_docteur(self):
        self.assertEqual(fi._norm_abbreviations("Dr. Martin"), "Docteur Martin")

    def test_professeur_sans_point(self):
        self.assertEqual(fi._norm_abbreviations("Pr Louis"), "Professeur Louis")

    def test_km_developpe(self):
        self.assertEqual(fi._norm_abbreviations("km"), "kilomètres")

    def test_ampersand_developpe(self):
        self.assertEqual(fi._norm_abbreviations("&"), "et")

    def test_saint(self):
        self.assertEqual(fi._norm_abbreviations("St. Louis"), "Saint Louis")

    def test_ampersand_substring_quirk(self):
        # Quirk : str.replace() n'est pas word-boundary-aware ; "&" dans "R&D"
        # est remplacé aussi → "RetD". Acceptable en pratique (rare en flux RSS).
        self.assertEqual(fi._norm_abbreviations("R&D Dupont"), "RetD Dupont")


# ── 10bis. Titres honorifiques ──────────────────────────────────────────────

class TestHonorifics(unittest.TestCase):
    def test_me_devant_nom_propre(self):
        self.assertEqual(fi._norm_honorifics("Me Dupont"), "Maître Dupont")

    def test_me_devant_minuscule_inchange(self):
        # Le lookahead exige une majuscule après → "Me martin" est préservé.
        self.assertEqual(fi._norm_honorifics("Me martin"), "Me martin")

    def test_meme_preserve(self):
        # "Même" commence par M mais la frontière de mot évite le faux-positif.
        self.assertEqual(fi._norm_honorifics("Même chose"), "Même chose")

    def test_me_dans_phrase(self):
        self.assertEqual(
            fi._norm_honorifics("au cabinet Me Smith"),
            "au cabinet Maître Smith",
        )


# ── 11. Caractères spéciaux résiduels ───────────────────────────────────────

class TestResidual(unittest.TestCase):
    def test_crochets_deviennent_espaces(self):
        self.assertEqual(fi._norm_residual("[foo]"), " foo ")

    def test_slash_devient_sur(self):
        self.assertEqual(fi._norm_residual("a/b"), "a sur b")

    def test_double_espace_collapse(self):
        self.assertEqual(fi._norm_residual("double  space"), "double space")

    def test_triple_newline_collapse(self):
        self.assertEqual(fi._norm_residual("triple\n\n\nnewlines"), "triple\nnewlines")

    def test_markdown_bold_italic_retires(self):
        # Les * et _ sont remplacés par des espaces, puis la règle " {2,}" → " "
        # collapse les doubles espaces.
        self.assertEqual(fi._norm_residual("*gras* _italic_"), " gras italic ")

    def test_hashtag(self):
        self.assertEqual(fi._norm_residual("hash#tag"), "hash tag")


# ── Pipeline complet ────────────────────────────────────────────────────────

class TestNormalizeForTtsPipeline(unittest.TestCase):
    def test_bulletin_typique(self):
        out = fi._normalize_for_tts("Bulletin du 21 avril 2026 à 07h30.")
        self.assertEqual(
            out,
            "Bulletin du vingt et un avril deux mille vingt-six à sept heures trente.",
        )

    def test_score_multiple(self):
        self.assertEqual(
            fi._normalize_for_tts("Score : 3-1. Score : 2-0."),
            "Score : trois à un. Score : deux à zéro.",
        )

    def test_pipeline_ordre_sdis_puis_971(self):
        out = fi._normalize_for_tts("Le SDIS de Pointe-à-Pitre (971) intervient.")
        self.assertIn("Service Départemental d'Incendie et de Secours", out)
        self.assertIn("quatre-vingt-dix-sept-un", out)

    def test_chaine_vide_reste_vide(self):
        self.assertEqual(fi._normalize_for_tts(""), "")

    def test_espaces_seuls_sont_strippes(self):
        self.assertEqual(fi._normalize_for_tts("   "), "")


if __name__ == "__main__":
    unittest.main()
