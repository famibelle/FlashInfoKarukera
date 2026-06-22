#!/usr/bin/env python3
"""
generate_emission.py

Génère une émission radio culturelle de 3 minutes en français (monologue).
  - Sélectionne 1 élément de chacun des 5 fichiers _ref.md
  - Utilise un morceau de la playlist comme inspiration
  - Texte généré par LLM Mistral (monologue structuré en 5 paragraphes)
  - TTS Voxtral (fr_marie_*) avec tons variés par paragraphe
  - Sortie : docs/audio/Emissions/emission-YYYY-MM-DD.mp3 + .json

Usage:
    python generate_emission.py
    python generate_emission.py --verbose
    python generate_emission.py --dry-run          # texte seul, pas de TTS
"""

import argparse
import json
import os
import random
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import date, datetime
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent))
from tts_utils import tts_call, normalize_for_tts

# ── Config Mistral ────────────────────────────────────────────────────────────
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
MISTRAL_CHAT_MODEL = "mistral-large-latest"
MISTRAL_CHAT_URL = "https://api.mistral.ai/v1/chat/completions"

# ── Config ──────────────────────────────────────────────────────────────────

PROMPTS_DIR        = Path(__file__).parent / "private" / "prompts"
INDEX_CULTUREL_DIR = Path(__file__).parent / "private" / "index_culturel"
SOURCE_FILES = [
    INDEX_CULTUREL_DIR / "kreyol_resistance_symbol_ref.md",
    INDEX_CULTUREL_DIR / "faune_guadeloupe_ref.md",
    INDEX_CULTUREL_DIR / "flore_guadeloupe_ref.md",
    INDEX_CULTUREL_DIR / "lieux_spirituels_ref.md",
    INDEX_CULTUREL_DIR / "histoire_guadeloupe_ref.md",
]
OUTPUT_DIR = Path("docs/audio/Emissions")
SELECTION_CACHE_PATH = Path(".dream_radio_cache") / "emission_selections.json"
CACHE_MEMORY = 7  # évite les répétitions sur les 7 dernières sélections par catégorie
PODCAST_RSS_PATH = Path("docs/podcast.xml")
EMISIONS_RSS_PATH = Path("docs/emissions.xml")

# ── Fonction call_mistral ────────────────────────────────────────────────────

def call_mistral(
    system: str,
    user: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 1500,
    json_mode: bool = False,
    timeout: int = 60,
    _retries: int = 4,
    model: str = MISTRAL_CHAT_MODEL,
) -> str:
    """Appelle l'API Mistral chat completions avec retry exponentiel."""
    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY non configurée")
    
    payload: dict = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    
    req = urllib.request.Request(
        MISTRAL_CHAT_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    
    for attempt in range(_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                result = json.loads(r.read())
            return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < _retries:
                wait = 15 * 2 ** attempt
                print(f"   ⏳ Mistral {e.code} — attente {wait}s (tentative {attempt + 1}/{_retries})…")
                time.sleep(wait)
            else:
                raise
        except (TimeoutError, OSError) as e:
            if attempt < _retries:
                wait = 15 * 2 ** attempt
                print(f"   ⏳ Mistral timeout réseau — attente {wait}s (tentative {attempt + 1}/{_retries})…")
                time.sleep(wait)
            else:
                raise


def _generate_metadata_with_llm(text: str, title: str) -> tuple[str, str]:
    """Génère un teaser (itunes:summary) et des keywords (itunes:keywords) via Mistral.
    
    Args:
        text: Description ou texte de l'émission
        title: Titre de l'émission
        
    Returns:
        tuple: (summary, keywords)
    """
    prompt = f"""Tu es un expert en podcasts culturels guadeloupéens.
À partir du texte suivant, génère :
1. Un RÉSUMÉ COURT (1 phrase, max 100 caractères) pour itunes:summary — doit être accrocheur et informatif
2. Une liste de MOTS-CLÉS (5-8 mots, séparés par des virgules, SANS espaces) pour itunes:keywords — doivent être pertinents pour la recherche sur Apple Podcasts

Texte : {text[:1500]}{'...' if len(text) > 1500 else ''}
Titre : {title}

Réponds UNIQUEMENT au format exact suivant (sans autre texte) :
RESUME: <ton résumé ici>
KEYWORDS: <tes,mots,clés,ici>"""
    
    try:
        response = call_mistral(
            system="Tu es un assistant strict. Réponds UNIQUEMENT avec le format RESUME:...\nKEYWORDS:...",
            user=prompt,
            temperature=0.3,
            max_tokens=300,
            model="mistral-small-latest",
        )
        
        # Parser la réponse
        summary = "Émission culturelle quotidienne sur la Guadeloupe."
        keywords = "Guadeloupe,culture,histoire,nature,symboles"
        
        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('RESUME:'):
                summary = line.replace('RESUME:', '').strip()[:100]  # Limiter à 100 caractères
            elif line.startswith('KEYWORDS:'):
                keywords = line.replace('KEYWORDS:', '').strip()
        
        # Nettoyage : supprimer les espaces dans les keywords
        keywords = keywords.replace(' ', '')
        
        # Fallback si vide
        if not summary:
            summary = "Émission culturelle quotidienne sur la Guadeloupe."
        if not keywords:
            keywords = "Guadeloupe,culture,histoire,nature,symboles"
            
        return summary, keywords
        
    except Exception as e:
        print(f"   ⚠️  Génération LLM des métadonnées échouée : {e}")
        # Valeurs par défaut
        return (
            "Émission culturelle quotidienne sur la Guadeloupe.",
            "Guadeloupe,culture,histoire,nature,symboles"
        )


# Voix Marie avec tons variés (disponibles dans Voxtral)
TTS_VOICE_BASE = "fr_marie_"

MISTRAL_MODEL = "mistral-large-latest"

# ── Sélection aléatoire ────────────────────────────────────────────────────

def _load_selection_cache() -> dict:
    try:
        return json.loads(SELECTION_CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_selection_cache(cache: dict) -> None:
    try:
        SELECTION_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        SELECTION_CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _select_random_lines_from_file(
    filepath: Path,
    num_lines: int = 1,
    exclude_names: set[str] | None = None,
    recent: list[str] | None = None,
) -> list[str]:
    """Sélectionne aléatoirement N lignes de tableau Markdown d'un fichier _ref.md."""
    header_keywords = ['famille', 'nom créole', 'nom français', 'nom scientifique',
                       'sacré', 'dimension culturelle', 'usage', 'catégorie', 'nom du lieu',
                       'commune', 'localisation']

    data_lines = []
    content = filepath.read_text(encoding="utf-8")

    for line in content.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        pipe_count = stripped.count('|')
        if pipe_count >= 2 and '---' not in stripped:
            clean_line = stripped[1:-1].strip()
            cells = [c.strip() for c in clean_line.split('|')]
            non_empty_cells = [c for c in cells if c]
            if len(non_empty_cells) >= 2:
                line_lower = clean_line.lower()
                if not any(keyword in line_lower for keyword in header_keywords):
                    clean_line = clean_line.replace('|', '\t')
                    data_lines.append(clean_line)

    # Déduplication cross-fichiers : exclure les noms déjà sélectionnés dans ce run
    if exclude_names:
        filtered = []
        for l in data_lines:
            cells = l.split('\t')
            name_cells = {cells[i].strip() for i in (1, 2) if i < len(cells) and cells[i].strip()}
            if not name_cells & exclude_names:
                filtered.append(l)
        data_lines = filtered if filtered else data_lines  # fallback si tout exclu

    # Anti-répétition inter-runs : mettre les récents en fin de liste
    if recent:
        recent_set = set(recent)
        fresh = [l for l in data_lines if l not in recent_set]
        used  = [l for l in data_lines if l in recent_set]
        random.shuffle(fresh)
        random.shuffle(used)
        data_lines = fresh + used
    else:
        random.shuffle(data_lines)

    return data_lines[:min(num_lines, len(data_lines))]


def _load_preceding_track(edition: str) -> dict:
    """Retourne le morceau de musique qui précède l'émission dans radio_sequence.json."""
    fallback = {"title": "la musique caribéenne", "artist": "nos artistes", "genre": "variés"}
    try:
        with open(Path("docs") / "radio_sequence.json", encoding="utf-8") as f:
            seq = json.load(f)["sequence"]

        # Chercher la position de l'émission pour cette édition
        emission_pos = None
        for i, item in enumerate(seq):
            if item.get("type") == "transition" and item.get("subtype") == "emission":
                if f"— {edition} —" in item.get("label", ""):
                    emission_pos = i
                    break

        if emission_pos is None:
            # Séquence pas encore régénérée pour aujourd'hui : prendre le dernier music
            print(f"⚠️  Slot émission {edition} absent de la séquence, dernier morceau utilisé", file=sys.stderr)
            search_range = range(len(seq) - 1, -1, -1)
        else:
            # Remonter depuis la position de l'émission
            search_range = range(emission_pos - 1, -1, -1)

        for i in search_range:
            if seq[i].get("type") == "music":
                t = seq[i]
                return {
                    "title":  t.get("title",  "Morceau inconnu"),
                    "artist": t.get("artist", "Artiste inconnu"),
                    "genre":  t.get("genre",  "N/A"),
                }
    except Exception as e:
        print(f"⚠️  Séquence radio non disponible : {e}", file=sys.stderr)
    return fallback


def _select_elements(edition: str = "matin", save_cache: bool = True) -> dict:
    """Sélectionne 1 élément par fichier + le morceau qui précède l'émission."""
    elements = {}
    file_titles = {
        "kreyol_resistance_symbol_ref.md": "Symboles de la résistance créole",
        "faune_guadeloupe_ref.md": "Faune de Guadeloupe",
        "flore_guadeloupe_ref.md": "Flore de Guadeloupe",
        "lieux_spirituels_ref.md": "Lieux spirituels de Guadeloupe",
        "histoire_guadeloupe_ref.md": "Histoire de Guadeloupe",
    }

    cache = _load_selection_cache()
    new_cache = dict(cache)
    selected_names: set[str] = set()  # déduplication cross-fichiers dans ce run

    for filepath in SOURCE_FILES:
        if not filepath.exists():
            continue
        key = filepath.name
        recent = cache.get(key, [])[-CACHE_MEMORY:]
        lines = _select_random_lines_from_file(filepath, 1, exclude_names=selected_names, recent=recent)
        if lines:
            # Enregistrer les noms (cols 1 et 2) pour éviter les doublons dans ce run
            cells = lines[0].split('\t')
            for col_idx in (1, 2):
                if col_idx < len(cells) and len(cells[col_idx].strip()) > 2:
                    selected_names.add(cells[col_idx].strip())
            new_cache[key] = (cache.get(key, []) + [lines[0]])[-(CACHE_MEMORY * 2):]
            elements[key] = {
                "title": file_titles.get(key, key),
                "content": lines[0]
            }

    if save_cache:
        _save_selection_cache(new_cache)

    elements["inspiration"] = _load_preceding_track(edition)
    return elements


# ── LLM ──────────────────────────────────────────────────────────────────────

def _mistral_chat(system: str, user: str) -> str:
    """Appel à l'API Mistral pour générer le texte."""
    import urllib.request, urllib.error, time
    
    key = os.environ["MISTRAL_API_KEY"]
    payload = json.dumps({
        "model": MISTRAL_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": 0.8,
        "max_tokens": 2048,
        "response_format": {"type": "text"}
    }).encode()
    
    req = urllib.request.Request(
        "https://api.mistral.ai/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code in (429, 500, 502, 503) and attempt < 3:
                wait = 15 * 2 ** attempt
                print(f"   ⏳ LLM {e.code} — attente {wait}s…")
                time.sleep(wait)
            else:
                raise RuntimeError(f"LLM HTTP {e.code}: {body}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < 3:
                wait = 15 * 2 ** attempt
                print(f"   ⏳ LLM réseau ({e}) — attente {wait}s…")
                time.sleep(wait)
            else:
                raise RuntimeError(f"LLM réseau: {e}") from None
    raise RuntimeError("LLM : trop de tentatives")


# ── Génération du monologue ───────────────────────────────────────────────

def _load_prompt(filename: str) -> str:
    """Charge un fichier de prompt depuis PROMPTS_DIR ou INDEX_CULTUREL_DIR."""
    for base in (INDEX_CULTUREL_DIR, PROMPTS_DIR):
        path = base / filename
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    raise FileNotFoundError(f"Prompt introuvable : {filename}")

# Charger le prompt Monique pour les émissions
SYSTEM_PROMPT = _load_prompt("monique_ame.md") + "\n\n" + _load_prompt("monique.md") + "\n\n" + _load_prompt("emission_instruction.md")


def _generate_title_llm(text: str) -> str | None:
    """Génère un titre poétique via Mistral à partir du texte de l'émission."""
    import re, urllib.request, urllib.error, time as _time
    try:
        key = os.environ["MISTRAL_API_KEY"]
    except KeyError:
        return None

    system = (
        "Tu es un rédacteur poétique pour Radio Karukera, une radio de la diaspora guadeloupéenne. "
        "Tu crées des titres d'émissions culturelles évocateurs, inspirants, avec une touche créole et caraïbéenne. "
        "Tu réponds TOUJOURS par une seule phrase courte — jamais de liste, jamais de tirets."
    )
    user = (
        f"Voici le texte d'une émission culturelle sur la Guadeloupe :\n\n{text}\n\n"
        "Génère UN SEUL titre poétique et évocateur (max 65 caractères) qui capture l'essence culturelle de cette émission. "
        "Le titre doit parler de la Guadeloupe, de ses traditions, de sa nature ou de son histoire. "
        "N'utilise PAS de titres de chansons, de noms d'artistes ou de références musicales. "
        "Pas de guillemets, pas de ponctuation finale."
    )
    payload = json.dumps({
        "model": "mistral-small-latest",
        "temperature": 0.85,
        "max_tokens": 80,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://api.mistral.ai/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = json.loads(r.read())["choices"][0]["message"]["content"].strip()
                title = re.sub(r'[\[\]\*\`\"\n\r]', "", raw)
                title = title.strip("'")  # guillemets entourants seulement
                title = re.sub(r"\s+", " ", title).strip().rstrip(".")
                return title or None
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 2:
                _time.sleep(10 * 2 ** attempt)
            else:
                print(f"   ⚠️  Titre LLM émission échoué (HTTP {e.code})")
                return None
        except Exception as e:
            print(f"   ⚠️  Titre LLM émission échoué : {e}")
            return None
    return None


def generate_catchy_title(elements: dict, text: str = "") -> str:
    """Génère un titre accrocheur pour l'émission basé sur LE CONTENU uniquement.
    
    Exemples:
    - "Roucou & Grenn-bwa : La terre qui murmure"
    - "Fromager & Foumi manyok : L'intelligence des Antilles"
    - "Piman bondaman jak : Le feu de la Guadeloupe"
    """
    import re
    
    # Emojis par catégorie
    category_emojis = {
        "kreyol_resistance_symbol_ref.md": "🌿",
        "faune_guadeloupe_ref.md": "🐸",
        "flore_guadeloupe_ref.md": "🌺",
        "lieux_spirituels_ref.md": "💧",
        "histoire_guadeloupe_ref.md": "🔥",
    }
    
    # Thèmes poétiques par catégorie
    category_themes = {
        "kreyol_resistance_symbol_ref.md": ["La terre qui résiste", "Le souffle créole", "L’âme antillaise", "L’héritage qui perdure"],
        "faune_guadeloupe_ref.md": ["Le chant de la forêt", "Les gardiens de la nuit", "La vie qui murmure", "Les voix de la nature"],
        "flore_guadeloupe_ref.md": ["Les couleurs de l’île", "La terre qui nourrit", "Les parfums du pays", "La nature généreuse"],
        "lieux_spirituels_ref.md": ["L’eau qui purifie", "L’esprit des lieux", "Le sacré qui coule", "La mémoire des ancêtres"],
        "histoire_guadeloupe_ref.md": ["Le combat qui continue", "La flamme de la liberté", "L’histoire qui vit", "La lutte qui inspire"],
    }
    
    # Extraire tous les sujets abordés
    subjects = []
    categories = []
    for file_key in category_emojis.keys():
        if file_key in elements:
            content = elements[file_key].get("content", "")
            if content:
                # Extraire le nom principal (premier element du tableau markdown)
                lines = content.strip().split('\n')
                if lines:
                    first_line = lines[0].strip()
                    if first_line:
                        # Format: "Plante / Résistance            \t Woucou / Roucou          \t ..."
                        parts = first_line.split('\t')
                        if len(parts) > 1:
                            # Prendre la deuxième partie (nom créole / nom scientifique)
                            subject_part = parts[1].strip()
                            # Extraire le premier nom avant " / "
                            subject = subject_part.split(' / ')[0].strip()
                        else:
                            # Fallback: prendre après " / " dans la première partie
                            subject = first_line.split(' / ')[1].strip() if ' / ' in first_line else first_line
                        
                        # Nettoyer le sujet (enlever les ** et autres marqueurs markdown)
                        subject = re.sub(r'[\*_~`]', '', subject).strip()
                        
                        if subject and subject not in ["Plante", "Insecte", "Cap", "1815", "1848", "Amphibien", "Légume", "Cascade", "Histoire"]:
                            subjects.append(subject)
                            categories.append(file_key)
    
    # Si on a au moins 2 sujets, créer un titre combiné
    if len(subjects) >= 2:
        # Prendre les 2 premiers sujets
        subject1 = subjects[0]
        subject2 = subjects[1]
        
        # Choisir un thème basé sur la première catégorie
        first_cat = categories[0]
        themes = category_themes.get(first_cat, ["La terre qui vit"])
        theme = themes[0]  # Prendre le premier thème
        
        # Choisir un emoji basé sur la première catégorie
        emoji = category_emojis.get(first_cat, "🌟")
        
        return f"{emoji} **{subject1} & {subject2} : {theme}**"
    
    # Si un seul sujet
    if len(subjects) == 1:
        subject = subjects[0]
        first_cat = categories[0]
        themes = category_themes.get(first_cat, ["La terre qui vit"])
        theme = themes[0]
        emoji = category_emojis.get(first_cat, "🌟")
        return f"{emoji} **{subject} : {theme}**"
    
    # Fallback : analyser le texte généré pour trouver des mots-clés
    if text:
        # Chercher des mots en gras **mot**
        bold_words = re.findall(r'\*\*(.*?)\*\*', text)
        if bold_words:
            return f"🌟 **{bold_words[0]} : Découverte culturelle de la Guadeloupe**"
        
        # Chercher des mots-clés guadeloupéens dans le texte
        keywords = ['fromager', 'foumi', 'piman', 'roucou', 'woucou', 'gwoka', 'biguine', 
                   'zandoli', 'manguier', 'morne', 'ka', 'résistance', 'créole', 'antilles',
                   'igwann', 'awokasié', 'bonda', 'manioc', 'vaniy', 'crabier']
        for kw in keywords:
            if kw.lower() in text.lower():
                kw_display = kw.capitalize() if kw.islower() else kw
                return f"🌟 **{kw_display} : Découverte culturelle de la Guadeloupe**"
    
    # Fallback générique
    return "🌟 Découverte culturelle de la Guadeloupe"


def generate_monologue(elements: dict, verbose: bool = False) -> str:
    """Genere le texte du monologue via LLM."""
    track = elements.get("inspiration", {})
    track_desc = f"'{track['title']}' par {track['artist']} ({track['genre']})"
    
    # Formater les éléments pour le LLM
    formatted_elements = ""
    category_order = [
        ("kreyol_resistance_symbol_ref.md", "Symboles de résistance créole"),
        ("faune_guadeloupe_ref.md", "Faune"),
        ("flore_guadeloupe_ref.md", "Flore"),
        ("lieux_spirituels_ref.md", "Lieux spirituels"),
        ("histoire_guadeloupe_ref.md", "Histoire"),
    ]
    
    for file_key, category in category_order:
        if file_key in elements:
            formatted_elements += f"- {category} : {elements[file_key]['content']}\n"
    
    # Charger le template de user prompt
    try:
        user_template = _load_prompt("emission_user_template.md")
    except Exception:
        user_template = """Contexte : Ton émission est inspirée par {track_desc}.
Éléments à intégrer :
{elements}
Structure ton monologue en 5 paragraphes."""
    
    user_prompt = user_template.format(
        track_desc=track_desc,
        elements=formatted_elements
    )
    
    if verbose:
        print("\n── SYSTEM PROMPT ─────────────────────────────────────────────")
        print(SYSTEM_PROMPT)
        print("\n── USER PROMPT ─────────────────────────────────────────────────")
        print(user_prompt)
        print()
    
    print("🤖 Génération du monologue (LLM)…")
    text = _mistral_chat(SYSTEM_PROMPT, user_prompt).strip()
    
    # Vérifier qu'on a bien 5 paragraphes
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) < 5:
        # Si pas assez, on essaye de séparer manuellement
        print(f"⚠️  Seuls {len(paragraphs)} paragraphes générés, tentative de correction…")
        # Séparer par phrases longues
        sentences = [s.strip() for s in text.split('. ') if s.strip()]
        if len(sentences) >= 5:
            # Regrouper en 5 paragraphes
            chunk_size = len(sentences) // 5
            paragraphs = []
            for i in range(5):
                chunk = sentences[i*chunk_size:(i+1)*chunk_size]
                paragraphs.append('. '.join(chunk) + '.')
            text = '\n\n'.join(paragraphs)
    
    return text


# ── Détermination du ton par LLM ────────────────────────────────────────

TONE_CLASSIFIER_MODEL = "mistral-small-latest"  # Modèle léger pour la classification
AVAILABLE_TONES = ["neutral", "happy", "excited", "curious", "sad"]

def _determine_tone(paragraph: str) -> str:
    """Utilise le LLM pour déterminer le ton optimal d'un paragraphe."""
    try:
        system_prompt = _load_prompt("tone_classifier_system.md")
    except Exception:
        system_prompt = """Tu es un expert en analyse de texte. Choisis UN ton parmi : neutral, happy, excited, curious, sad. Réponds UNIQUEMENT avec le nom du ton."""
    
    try:
        user_template = _load_prompt("tone_classifier_user_template.md")
    except Exception:
        user_template = "Paragraphe à analyser :\n\n{paragraph}\n\nTon adapté :"
    
    user_prompt = user_template.format(paragraph=paragraph)
    
    try:
        response = _mistral_chat_classifier(system_prompt, user_prompt)
        # Nettoyer la réponse et vérifier qu'elle est valide
        tone = response.strip().lower()
        if tone in AVAILABLE_TONES:
            return tone
        # Fallback : neutral
        return "neutral"
    except Exception as e:
        print(f"   ⚠️  Classification du ton échouée : {e}, fallback sur neutral")
        return "neutral"


def _mistral_chat_classifier(system: str, user: str) -> str:
    """Appel à l'API Mistral pour la classification de ton (modèle léger)."""
    import urllib.request, urllib.error, time
    
    key = os.environ["MISTRAL_API_KEY"]
    payload = json.dumps({
        "model": TONE_CLASSIFIER_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": 0.2,  # Plus déterministe pour la classification
        "max_tokens": 16,
        "response_format": {"type": "text"}
    }).encode()
    
    req = urllib.request.Request(
        "https://api.mistral.ai/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code in (429, 500, 502, 503) and attempt < 3:
                wait = 10 * 2 ** attempt
                print(f"   ⏳ Tone classifier {e.code} — attente {wait}s…")
                time.sleep(wait)
            else:
                raise RuntimeError(f"Tone classifier HTTP {e.code}: {body}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < 3:
                wait = 10 * 2 ** attempt
                print(f"   ⏳ Tone classifier réseau ({e}) — attente {wait}s…")
                time.sleep(wait)
            else:
                raise RuntimeError(f"Tone classifier réseau: {e}") from None
    raise RuntimeError("Tone classifier: trop de tentatives")


# ── TTS avec tons variés ───────────────────────────────────────────────────

def _concat_mp3(files: list[Path], output_path: Path) -> None:
    """Concatène plusieurs fichiers MP3 en un seul."""
    all_files: list[Path] = []
    for i, f in enumerate(files):
        all_files.append(f)
        if i < len(files) - 1:
            # Ajouter un petit silence entre les paragraphes
            silence_path = f.parent / f"_sil_{i:02d}.mp3"
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d=0.3",
                "-c:a", "libmp3lame", "-q:a", "4", str(silence_path),
            ], check=True)
            all_files.append(silence_path)
    
    inputs = [arg for f in all_files for arg in ("-i", str(f))]
    n = len(all_files)
    filter_str = "".join(f"[{i}:a]" for i in range(n)) + f"concat=n={n}:v=0:a=1[out]"
    
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[out]",
        "-c:a", "libmp3lame", "-q:a", "2",
        str(output_path),
    ], check=True)
    
    # Nettoyer les fichiers temporaires
    for f in all_files:
        if f.name.startswith("_sil_"):
            f.unlink(missing_ok=True)


def generate_audio(text: str, output_path: Path) -> None:
    """Génère l'audio avec tons déterminés par LLM pour chaque paragraphe."""
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    
    # Déterminer le ton optimal pour chaque paragraphe via LLM
    print("🎭 Détermination des tons par LLM…")
    tones = []
    for i, para in enumerate(paragraphs):
        tone = _determine_tone(para)
        tones.append(tone)
        print(f"   [{i+1}] ton: {tone}")
    
    temp_files = []
    with tempfile.TemporaryDirectory(prefix="emission_") as tmpdir:
        tmp = Path(tmpdir)
        
        print(f"🔊 TTS ({len(paragraphs)} paragraphes)…")
        for i, (para, tone) in enumerate(zip(paragraphs, tones)):
            temp_path = tmp / f"para_{i:02d}.mp3"
            voice_id = f"{TTS_VOICE_BASE}{tone}"
            print(f"   [{i+1}/{len(paragraphs)}] ton: {tone} → {voice_id}…", flush=True)
            tts_call(normalize_for_tts(para), temp_path, voice_id=voice_id)
            temp_files.append(temp_path)
        
        print("   🔗 Concatenation FFmpeg…")
        _concat_mp3(temp_files, output_path)


# ── Pipeline principal ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Émission culturelle quotidienne — 3 min monologue")
    parser.add_argument("--verbose", action="store_true", help="Affiche prompts et sorties LLM")
    parser.add_argument("--dry-run", action="store_true", help="Texte seul, sans TTS")
    parser.add_argument("--edition", choices=["matin", "soir"], default="matin",
                        help="Édition du jour (matin ou soir)")
    parser.add_argument("--overwrite", action="store_true", help="Écrase les fichiers existants")
    parser.add_argument("--sources", action="store_true",
                        help="Affiche uniquement les éléments sélectionnés sans générer l'émission")
    parser.add_argument("--import-existing", action="store_true",
                        help="Importe toutes les émissions existantes (JSON) vers emissions.xml")
    args = parser.parse_args()

    # Mode import : importer les émissions existantes et quitter
    if args.import_existing:
        _create_emissions_xml()  # S'assurer que le fichier existe
        count = _import_existing_emissions()
        print(f"\n✨ {count} émissions importées. Vérifiez {EMISIONS_RSS_PATH}")
        return

    if args.sources:
        import re as _re, textwrap
        edition = args.edition
        elements = _select_elements(edition, save_cache=False)

        ENTRIES = [
            ("kreyol_resistance_symbol_ref.md", "🌿", "Symboles de résistance créole"),
            ("faune_guadeloupe_ref.md",         "🐸", "Faune"),
            ("flore_guadeloupe_ref.md",         "🌺", "Flore"),
            ("lieux_spirituels_ref.md",         "💧", "Lieux spirituels"),
            ("histoire_guadeloupe_ref.md",      "🔥", "Histoire"),
        ]

        WIDTH = 72
        BAR   = "─" * WIDTH

        # Header
        from datetime import date as _date
        d = _date.today()
        MONTH = {"01":"janvier","02":"février","03":"mars","04":"avril","05":"mai",
                 "06":"juin","07":"juillet","08":"août","09":"septembre",
                 "10":"octobre","11":"novembre","12":"décembre"}
        date_fr = f"{d.day} {MONTH[d.strftime('%m')]} {d.year}"
        print()
        print(BAR)
        print(f"  Émission {edition} — {date_fr}")
        print(BAR)

        for key, emoji, label in ENTRIES:
            if key not in elements:
                continue
            raw = elements[key]["content"]
            cells = [_re.sub(r'\*+', '', c).strip() for c in raw.split('\t') if c.strip()]

            print()
            print(f"  {emoji}  {label}")

            # Titre : 2–3 premières cellules non-étoile
            title_cells = [c for c in cells[:4] if c and not c.startswith('⭐')][:3]
            if title_cells:
                print(f"     {'  ·  '.join(title_cells)}")

            # Sacralité
            sacre = next((c for c in cells if c.startswith('⭐')), None)
            if sacre:
                print(f"     {sacre}")

            # Description : dernière cellule substantielle
            desc = next((c for c in reversed(cells)
                         if len(c) > 30 and not c.startswith('⭐')), None)
            if desc:
                for line in textwrap.wrap(desc, width=WIDTH - 5):
                    print(f"     {line}")

        # Morceau
        insp = elements.get("inspiration", {})
        print()
        print(f"  🎵  Morceau précédant")
        print(f"     {insp.get('title','?')}  ·  {insp.get('artist','?')}")
        print()
        print(BAR)
        print()
        return

    edition = args.edition

    # Avertir si des fichiers sources manquent (mais continuer)
    missing = [f for f in SOURCE_FILES if not f.exists()]
    if missing:
        for f in missing:
            print(f"⚠️  Fichier introuvable : {f}", file=sys.stderr)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    out_mp3  = OUTPUT_DIR / f"emission-{today}-{edition}.mp3"
    out_json = OUTPUT_DIR / f"emission-{today}-{edition}.json"

    if out_mp3.exists() and not args.overwrite and not args.dry_run:
        print(f"⚠️  {out_mp3.name} existe déjà. Utilisez --overwrite pour régénérer.")
        return
    
    # 1. Sélection des éléments + morceau précédant l'émission
    print("🎲 Sélection des éléments…")
    elements = _select_elements(edition)
    print(f"   ✅ {len(elements) - 1} éléments + morceau précédant ({elements['inspiration']['title']})")
    
    # 2. Génération du monologue
    text = generate_monologue(elements, verbose=args.verbose)
    
    word_count = len(text.split())
    print(f"✅ Monologue généré : {word_count} mots")
    
    # 2.5. Générer un titre accrocheur (LLM, fallback rule-based)
    print("✨ Génération du titre (LLM)…")
    catchy_title = _generate_title_llm(text) or generate_catchy_title(elements, text)
    print(f"✅ Titre : {catchy_title}")
    
    # 3. Sauvegarde JSON
    output_data = {
        "date": today,
        "edition": edition,
        "type": "emission",
        "title": catchy_title,
        "duration": "~3 minutes",
        "word_count": word_count,
        "voice": f"{TTS_VOICE_BASE}* (tons variés)",
        "inspiration": elements.get("inspiration", {}),
        "elements": {k: v for k, v in elements.items() if k != "inspiration"},
        "text": text,
        "audio_url": f"https://famibelle.github.io/FlashInfoKarukera/audio/Emissions/emission-{today}-{edition}.mp3"
    }
    out_json.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾 JSON → {out_json}")

    # Archive texte pour analyse par dream_radio
    archives_dir = Path("archives/emissions")
    archives_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archives_dir / f"emission-{today}-{edition}.txt"
    archive_path.write_text(text, encoding="utf-8")
    print(f"📝 Archive → {archive_path}")
    
    # Afficher le texte en mode verbose
    if args.verbose:
        print("\n── Monologue complet ────────────────────────────────────────")
        paragraphs = text.split('\n\n')
        for i, para in enumerate(paragraphs, 1):
            print(f"   [{i}] {para.strip()}")
        print("────────────────────────────────────────────────────────────────")
        print(f"💾 Fichier MP3 : {out_mp3}")
    
    if args.dry_run:
        print("\n── Monologue complet ────────────────────────────────────────")
        paragraphs = text.split('\n\n')
        # Déterminer les tons via LLM même en dry-run pour montrer le résultat
        print("🎭 Détermination des tons par LLM…")
        tones = []
        for i, para in enumerate(paragraphs):
            tone = _determine_tone(para)
            tones.append(tone)
            print(f"   [{i+1}] ton: {tone}")
        for i, (para, tone) in enumerate(zip(paragraphs, tones), 1):
            print(f"\n[{i} — ton: {tone}]")
            print(para)
        print(f"\n⏭️  TTS ignoré (--dry-run)")
        return
    
    # 4. Génération audio
    generate_audio(text, out_mp3)
    size_kb = out_mp3.stat().st_size // 1024
    print(f"✅ MP3 → {out_mp3} ({size_kb} Ko)")

    # 5. Mise à jour du podcast.xml
    _update_podcast_xml(out_mp3, title=catchy_title)
    # 5b. Mise à jour du emissions.xml (podcast dédié aux émissions culturelles)
    _update_emissions_xml(out_mp3, title=catchy_title, desc=text)
    
    # 6. Lecture automatique du fichier
    print("\n🔊 Lecture du fichier audio...")
    try:
        # Essaye mpg123 d'abord
        subprocess.run(["mpg123", str(out_mp3)], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            # Fallback sur afplay (macOS)
            subprocess.run(["afplay", str(out_mp3)], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Fallback sur ffplay
                subprocess.run(["ffplay", "-autoexit", "-nodisp", str(out_mp3)], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("   ⚠️  Aucun lecteur audio disponible (mpg123/afplay/ffplay). Installez-en un pour la lecture automatique.")


# ── Mise à jour podcast.xml ───────────────────────────────────────────────

def _indent_xml(elem, level=0):
    """Indente correctement l'XML."""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _indent_xml(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def _update_podcast_xml(mp3_path: Path, title: str = "Émission culturelle") -> None:
    """Ajoute l'émission au fichier podcast.xml avec un titre personnalise."""
    if not PODCAST_RSS_PATH.exists():
        print("⚠️  podcast.xml introuvable")
        return

    today = date.today()
    # Déduire l'édition depuis le nom du fichier MP3
    stem = mp3_path.stem  # e.g. "emission-2026-05-09-matin"
    edition = stem.rsplit("-", 1)[-1] if stem.rsplit("-", 1)[-1] in ("matin", "soir") else ""
    guid = f'emission-{today.isoformat()}-{edition}' if edition else f'emission-{today.isoformat()}'
    mp3_url = f"https://famibelle.github.io/FlashInfoKarukera/audio/Emissions/{mp3_path.name}"

    # Vérifier si cette émission existe déjà
    existing_content = PODCAST_RSS_PATH.read_text(encoding='utf-8')
    if f'<guid>{guid}</guid>' in existing_content or mp3_url in existing_content:
        print(f"⚠️  Émission {guid} déjà dans podcast.xml, ignorée")
        return

    mp3_size = mp3_path.stat().st_size
    pub_date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    # Parse XML
    try:
        tree = ET.parse(PODCAST_RSS_PATH)
        root = tree.getroot()
        channel = root.find('channel')
        if channel is None:
            print("⚠️  Balise <channel> introuvable dans podcast.xml")
            return

        # Namespace itunes
        NS_ITUNES = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
        
        # Créer le nouvel item
        item = ET.Element('item')
        ET.SubElement(item, 'title').text = title
        desc = ET.SubElement(item, 'description')
        desc.text = "Émission culturelle quotidienne sur les symboles, l'histoire et la nature de la Guadeloupe."
        ET.SubElement(item, 'pubDate').text = pub_date
        enc = ET.SubElement(item, 'enclosure')
        enc.set('url', mp3_url)
        enc.set('length', str(mp3_size))
        enc.set('type', 'audio/mpeg')
        ET.SubElement(item, 'guid', {'isPermaLink': 'false'}).text = guid
        # itunes:duration
        ET.SubElement(item, f'{{{NS_ITUNES}}}duration').text = '180'
        
        # Ajouter l'item au channel (à la fin, convention RSS)
        channel.append(item)

        # S'assurer que le namespace itunes est déclaré sur la racine avec le préfixe 'itunes'
        if 'xmlns:itunes' not in root.attrib:
            # Conserver la déclaration existante du fichier original
            # ElementTree peut avoir ajouté xmlns:ns0, on va la remplacer
            for attr in list(root.attrib.keys()):
                if attr.startswith('xmlns:') and root.attrib[attr] == NS_ITUNES:
                    del root.attrib[attr]
            root.set('xmlns:itunes', NS_ITUNES)
        
        # Sauvegarder avec bonne indentation
        _indent_xml(root)
        
        # Écrire dans un buffer pour corriger les préfixes
        import io
        xml_buffer = io.StringIO()
        tree.write(xml_buffer, encoding='unicode', xml_declaration=True)
        xml_content = xml_buffer.getvalue()
        
        # Remplacer les préfixes nsX: par itunes:
        xml_content = xml_content.replace('ns0:', 'itunes:')
        xml_content = xml_content.replace('ns1:', 'itunes:')
        xml_content = xml_content.replace('ns2:', 'itunes:')
        
        PODCAST_RSS_PATH.write_text(xml_content, encoding='utf-8')
        print(f"✅ {PODCAST_RSS_PATH.name} mis à jour avec l'émission")
    except Exception as e:
        print(f"⚠️  Erreur mise à jour {PODCAST_RSS_PATH.name}: {e}")


def _create_emissions_xml() -> None:
    """Crée emissions.xml avec la structure de base si le fichier n'existe pas."""
    if EMISIONS_RSS_PATH.exists():
        return
    
    # Utiliser ElementTree pour un échappement XML correct
    NS_ITUNES = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
    
    rss = ET.Element('rss', version='2.0')
    rss.set('xmlns:itunes', NS_ITUNES)
    
    channel = ET.SubElement(rss, 'channel')
    
    ET.SubElement(channel, 'title').text = 'Émissions Culturelles Karukera'
    ET.SubElement(channel, 'link').text = 'https://famibelle.github.io/FlashInfoKarukera/'
    ET.SubElement(channel, 'description').text = (
        'Découvrez les symboles, l\'histoire et la nature de la Guadeloupe à travers '
        'des émissions culturelles quotidiennes de 3 minutes. Chaque épisode explore '
        'un aspect unique de la culture guadeloupéenne, des traditions aux paysages, '
        'en passant par les figures historiques et les symboles de résistance.'
    )
    ET.SubElement(channel, 'language').text = 'fr'
    ET.SubElement(channel, 'copyright').text = '© 2026 Botiran'
    ET.SubElement(channel, 'itunes:author').text = 'Botiran'
    
    # ✨ Fréquence de publication
    ET.SubElement(channel, 'itunes:updateFrequency').text = 'daily'
    ET.SubElement(channel, 'itunes:updatePeriod').text = 'day'
    
    owner = ET.SubElement(channel, 'itunes:owner')
    ET.SubElement(owner, 'itunes:name').text = 'Botiran'
    ET.SubElement(owner, 'itunes:email').text = 'medhi.famibelle@outlook.fr'
    
    ET.SubElement(channel, 'itunes:image').set('href', 'https://famibelle.github.io/FlashInfoKarukera/artwork-emissions.jpg')
    
    # ✨ TEASER (itunes:summary)
    ET.SubElement(channel, 'itunes:summary').text = (
        'Des émissions culturelles quotidiennes de 3 minutes sur la Guadeloupe, '
        'explorant symboles, histoire et nature.'
    )
    
    # ✨ KEYWORDS
    ET.SubElement(channel, 'itunes:keywords').text = (
        'Guadeloupe,culture,histoire,nature,symboles,Antilles,Caraïbes,tradition,patrimoine'
    )
    
    image = ET.SubElement(channel, 'image')
    ET.SubElement(image, 'url').text = 'https://famibelle.github.io/FlashInfoKarukera/artwork-emissions.jpg'
    ET.SubElement(image, 'title').text = 'Émissions Culturelles Karukera'
    ET.SubElement(image, 'link').text = 'https://famibelle.github.io/FlashInfoKarukera/'
    
    cat1 = ET.SubElement(channel, 'itunes:category', text='Arts')
    ET.SubElement(cat1, 'itunes:category', text='Performing Arts')
    
    cat2 = ET.SubElement(channel, 'itunes:category', text='Society & Culture')
    ET.SubElement(cat2, 'itunes:category', text='History')
    
    ET.SubElement(channel, 'itunes:explicit').text = 'no'
    ET.SubElement(channel, 'itunes:type').text = 'episodic'
    
    # Écrire avec indentation
    _indent_xml(rss)
    
    from io import BytesIO
    xml_buffer = BytesIO()
    ET.ElementTree(rss).write(xml_buffer, encoding='utf-8', xml_declaration=True)
    xml_content = xml_buffer.getvalue().decode('utf-8')
    
    # Corriger les préfixes nsX: en itunes:
    xml_content = xml_content.replace('ns0:', 'itunes:')
    
    EMISIONS_RSS_PATH.parent.mkdir(parents=True, exist_ok=True)
    EMISIONS_RSS_PATH.write_text(xml_content, encoding='utf-8')
    print(f"✅ {EMISIONS_RSS_PATH.name} créé avec la structure de base")


def _import_existing_emissions() -> int:
    """Importe toutes les émissions existantes depuis docs/audio/Emissions/ vers emissions.xml.
    
    Returns:
        int: Nombre d'émissions importées
    """
    emissions_dir = Path("docs/audio/Emissions")
    if not emissions_dir.exists():
        print("⚠️  Dossier docs/audio/Emissions/ introuvable")
        return 0
    
    # Trouver tous les fichiers JSON d'émission
    json_files = sorted(emissions_dir.glob("emission-2026-*.json"), reverse=True)
    
    if not json_files:
        print("⚠️  Aucune émission existante trouvée dans docs/audio/Emissions/")
        return 0
    
    print(f"📂 Import de {len(json_files)} émissions existantes...")
    imported_count = 0
    
    for json_file in json_files:
        # Charger les métadonnées
        try:
            data = json.loads(json_file.read_text(encoding='utf-8'))
            title = data.get('title', 'Émission culturelle')
            text = data.get('text', '')
            date_str = data.get('date', '')
            
            # Trouver le fichier MP3 correspondant
            mp3_files = list(emissions_dir.glob(f"emission-{date_str}*.mp3"))
            if not mp3_files:
                print(f"   ⚠️  MP3 introuvable pour {json_file.name}")
                continue
            
            mp3_path = mp3_files[0]
            
            # Vérifier si déjà dans emissions.xml
            guid_pattern = f'emission-{date_str}'
            if EMISIONS_RSS_PATH.exists():
                existing = EMISIONS_RSS_PATH.read_text(encoding='utf-8')
                if guid_pattern in existing:
                    print(f"   ⏭️  {json_file.name} déjà dans emissions.xml")
                    continue
            
            # Importer l'émission
            _update_emissions_xml(mp3_path, title=title, desc=text, emission_date=date_str)
            imported_count += 1
            
        except Exception as e:
            print(f"   ⚠️  Erreur import {json_file.name} : {e}")
    
    print(f"✅ {imported_count} émissions importées dans emissions.xml")
    return imported_count


def _update_emissions_xml(mp3_path: Path, title: str = "Émission culturelle", desc: str = "", emission_date: str = None) -> None:
    """Ajoute l'émission au fichier emissions.xml (podcast dédié aux émissions culturelles).
    
    Args:
        mp3_path: Chemin du fichier MP3
        title: Titre de l'émission
        desc: Description complète (pour générer summary et keywords via LLM)
        emission_date: Date de l'émission au format YYYY-MM-DD (si None, utilise aujourd'hui)
    """
    if not EMISIONS_RSS_PATH.exists():
        _create_emissions_xml()
        if not EMISIONS_RSS_PATH.exists():
            print("⚠️  Impossible de créer emissions.xml")
            return

    # Utiliser la date fournie ou la date du fichier MP3 ou aujourd'hui
    if emission_date:
        pub_date_obj = datetime.strptime(emission_date, "%Y-%m-%d")
    else:
        # Essayer d'extraire la date du nom de fichier (emission-2026-05-04-matin.mp3)
        stem = mp3_path.stem
        parts = stem.split("-")
        date_part = None
        for part in parts:
            if len(part) == 10 and part[4] == "-" and part[7] == "-":
                date_part = part
                break
        if date_part:
            pub_date_obj = datetime.strptime(date_part, "%Y-%m-%d")
        else:
            pub_date_obj = datetime.utcnow()
    
    pub_date_str = pub_date_obj.strftime("%a, %d %b %Y %H:%M:%S +0000")
    date_iso = pub_date_obj.strftime("%Y-%m-%d")
    
    stem = mp3_path.stem
    edition = stem.rsplit("-", 1)[-1] if stem.rsplit("-", 1)[-1] in ("matin", "soir") else ""
    guid = f'emission-{date_iso}-{edition}' if edition else f'emission-{date_iso}'
    mp3_url = f"https://famibelle.github.io/FlashInfoKarukera/audio/Emissions/{mp3_path.name}"

    # Vérifier si cette émission existe déjà
    existing_content = EMISIONS_RSS_PATH.read_text(encoding='utf-8')
    if f'<guid>{guid}</guid>' in existing_content or mp3_url in existing_content:
        print(f"⚠️  Émission {guid} déjà dans emissions.xml, ignorée")
        return

    mp3_size = mp3_path.stat().st_size

    # ✨ Générer teaser et keywords via LLM si description disponible
    if desc:
        summary, keywords = _generate_metadata_with_llm(desc, title)
        print(f"   ✨ Teaser LLM : {summary}")
        print(f"   ✨ Keywords LLM : {keywords}")
    else:
        summary = "Émission culturelle quotidienne sur la Guadeloupe."
        keywords = "Guadeloupe,culture,histoire,nature,symboles"

    # Parse XML
    try:
        tree = ET.parse(EMISIONS_RSS_PATH)
        root = tree.getroot()
        channel = root.find('channel')
        if channel is None:
            print("⚠️  Balise <channel> introuvable dans emissions.xml")
            return

        # Namespace itunes
        NS_ITUNES = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
        
        # Créer le nouvel item
        item = ET.Element('item')
        # Nettoyer le titre (supprimer markdown, emojis et caractères spéciaux)
        import re
        clean_title = re.sub(r'[\*_~`]', '', title)  # Supprimer * _ ~ `
        clean_title = re.sub(r'[#@]', '', clean_title)  # Supprimer # @
        clean_title = re.sub(r'[🌿🎧✨🔥💬📢🎤🎶🌍🌎🌴🌊🌅🌙⭐]', '', clean_title)  # Supprimer emojis courants
        clean_title = clean_title.strip()  # Supprimer espaces en début/fin
        ET.SubElement(item, 'title').text = clean_title
        description_elem = ET.SubElement(item, 'description')
        description_elem.text = summary
        ET.SubElement(item, 'pubDate').text = pub_date_str
        enc = ET.SubElement(item, 'enclosure')
        enc.set('url', mp3_url)
        enc.set('length', str(mp3_size))
        enc.set('type', 'audio/mpeg')
        ET.SubElement(item, 'guid', {'isPermaLink': 'false'}).text = guid
        ET.SubElement(item, f'{{{NS_ITUNES}}}duration').text = '180'
        
        # ✨ NOUVEAU : Ajouter teaser et keywords dans l'item
        ET.SubElement(item, f'{{{NS_ITUNES}}}summary').text = summary
        ET.SubElement(item, f'{{{NS_ITUNES}}}keywords').text = keywords
        
        # Ajouter l'item au channel
        channel.append(item)

        # S'assurer que le namespace itunes est déclaré
        if 'xmlns:itunes' not in root.attrib:
            for attr in list(root.attrib.keys()):
                if attr.startswith('xmlns:') and root.attrib[attr] == NS_ITUNES:
                    del root.attrib[attr]
            root.set('xmlns:itunes', NS_ITUNES)
        
        # Indenter et sauvegarder
        _indent_xml(root)
        
        from io import BytesIO
        xml_buffer = BytesIO()
        tree.write(xml_buffer, encoding='utf-8', xml_declaration=True)
        xml_content = xml_buffer.getvalue().decode('utf-8')
        
        # Remplacer les préfixes nsX: par itunes:
        xml_content = xml_content.replace('ns0:', 'itunes:')
        xml_content = xml_content.replace('ns1:', 'itunes:')
        xml_content = xml_content.replace('ns2:', 'itunes:')
        
        EMISIONS_RSS_PATH.write_text(xml_content, encoding='utf-8')
        print(f"✅ emissions.xml mis à jour avec l'émission")
    except Exception as e:
        print(f"⚠️  Erreur mise à jour emissions.xml: {e}")


if __name__ == "__main__":
    main()
