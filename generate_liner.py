#!/usr/bin/env python3
"""
Liner Generator — Flash Info Karukera

Génère les liners (annonces vocales) et capsules culturelles en MP3.
Utilise Mistral LLM pour le texte et Voxtral TTS pour la voix.

Les fichiers générés sont sauvegardés dans :
  - docs/liners/   (pour les liners)
  - docs/capsules/ (pour les capsules culturelles)
"""

import os
import re
import json
import argparse
import unicodedata
import logging
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from tts_utils import tts_call, normalize_for_tts

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

PROMPTS_DIR        = Path(__file__).parent / "private" / "prompts"
INDEX_CULTUREL_DIR = Path(__file__).parent / "private" / "index_culturel"
LINERS_DIR     = Path("docs/liners")
CAPSULES_DIR   = Path("docs/capsules")
CACHE_FILE     = Path("playlists/youtube_cache.json")  # Gardé pour compatibilité

MISTRAL_CHAT_URL   = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_CHAT_MODEL = "mistral-large-latest"

# Mapping des blocs pour les annonces
ANNOUNCE_BLOC_LABEL = {
    "morning": "matin",
    "midday":  "midi", 
    "evening": "soir",
}

_mistral_last_call: float = 0.0
_MISTRAL_MIN_INTERVAL = 4.0  # secondes minimum entre deux appels Mistral


# ── Cache ─────────────────────────────────────────────────────────────────────

def load_cache() -> dict:
    """Charge le cache depuis le fichier JSON."""
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict):
    """Sauvegarde le cache dans le fichier JSON."""
    CACHE_FILE.parent.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Prompts ──────────────────────────────────────────────────────────────────

def _load_prompt(filename: str) -> str:
    """Charge un fichier de prompt depuis INDEX_CULTUREL_DIR ou PROMPTS_DIR."""
    for base in (INDEX_CULTUREL_DIR, PROMPTS_DIR):
        path = base / filename
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    raise FileNotFoundError(f"Prompt introuvable : {filename}")


def _select_random_ref_lines(num_per_file: int = 3) -> str:
    """Sélectionne aléatoirement des lignes de référence depuis les fichiers _ref.md."""
    import random
    ref_files = [
        INDEX_CULTUREL_DIR / "kreyol_resistance_symbol_ref.md",
        INDEX_CULTUREL_DIR / "faune_guadeloupe_ref.md",
        INDEX_CULTUREL_DIR / "flore_guadeloupe_ref.md",
        INDEX_CULTUREL_DIR / "lieux_spirituels_ref.md",
        INDEX_CULTUREL_DIR / "histoire_guadeloupe_ref.md",
    ]
    result_lines = []
    for filepath in ref_files:
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8")
            data_lines = []
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
                        result_lines.append(clean_line.replace('|', '\t'))
            random.shuffle(data_lines)
    random.shuffle(result_lines)
    return "\n".join(result_lines[:num_per_file])


# ── LLM Mistral ───────────────────────────────────────────────────────────────

def _mistral_chat(system: str, user: str, max_retries: int = 4, label: str = "") -> str:
    """Appelle l'API Mistral chat avec throttle inter-appels."""
    import time
    global _mistral_last_call

    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY non défini")

    # Respecter l'intervalle minimum entre appels pour éviter le rate limit
    elapsed = time.time() - _mistral_last_call
    if elapsed < _MISTRAL_MIN_INTERVAL:
        wait_pre = _MISTRAL_MIN_INTERVAL - elapsed
        logger.info(f"  Mistral throttle — attente {wait_pre:.1f}s [{label}]")
        time.sleep(wait_pre)

    payload = json.dumps({
        "model": MISTRAL_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "max_tokens": 60,
        "temperature": 0.85,
    }).encode()
    req = urllib.request.Request(
        MISTRAL_CHAT_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    wait = 15
    for attempt in range(1, max_retries + 1):
        try:
            _mistral_last_call = time.time()
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            return data["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries:
                logger.warning(f"  Mistral 429 [{label}] — attente {wait}s (tentative {attempt}/{max_retries})")
                time.sleep(wait)
                wait *= 2
            else:
                raise
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < max_retries:
                logger.warning(f"  Mistral réseau [{label}] ({e}) — attente {wait}s (tentative {attempt}/{max_retries})")
                time.sleep(wait)
                wait *= 2
            else:
                raise


# ── Génération des liners ─────────────────────────────────────────────────────

def get_announcement_mp3_url(bloc: str, artists: list[str], voice: str = "corinne", verbose: bool = False) -> tuple[str | None, str | None]:
    """
    Génère un liner MP3, le sauvegarde dans docs/liners/ et retourne (url, label).
    
    Args:
        bloc: moment de la journée (matin/midi/soir)
        artists: liste des artistes à annoncer
        voice: "solitude" ou "corinne" (défaut: corinne)
    
    Returns:
        tuple: (url_publique, label_généré) ou (None, None) en cas d'erreur
    """
    if not artists:
        return None, None

    from datetime import date
    week      = date.today().strftime("%Y-W%W")
    cache_key = f"liner_mp3_{week}_{bloc}_{voice}_{'--'.join(sorted(artists[:3]))}"
    cache     = load_cache()

    # Vérifier le cache
    if cache_key in cache and cache[cache_key]:
        url      = cache[cache_key]
        filename = url.rsplit("/", 1)[-1]
        if (LINERS_DIR / filename).exists():
            logger.info(f"Liner MP3 {bloc} ({voice}) depuis cache → {url}")
            # Charger le label depuis le fichier JSON si possible
            json_path = LINERS_DIR / filename.replace('.mp3', '.json')
            if json_path.exists():
                try:
                    meta = json.loads(json_path.read_text(encoding='utf-8'))
                    return url, meta.get('label', '')
                except:
                    pass
            return url, None

    # Générer le texte via LLM
    try:
        if voice == "corinne":
            system_prompt = (
                _load_prompt("corinne_ame.md")
                + "\n\n"
                + _select_random_ref_lines(3)
                + "\n\n"
                + _load_prompt("corinne.md")
            )
        else:
            system_prompt = (
                _load_prompt("solitude_ame.md")
                + "\n\n"
                + _select_random_ref_lines(3)
                + "\n\n"
                + _load_prompt("solitude.md")
            )
    except Exception as e:
        logger.warning(f"Liner {bloc} ({voice}) ignoré : {e}")
        return None, None

    label       = ANNOUNCE_BLOC_LABEL.get(bloc, bloc)
    artists_str = ", ".join(artists)
    user_prompt = f"Moment : {label}\nArtistes : {artists_str}\nNote : ces artistes sont séparés dans la playlist, ils ne jouent PAS ensemble. Ne JAMAIS suggérer une collaboration."

    logger.info(f"  Liner {bloc} ({voice}) — 🤖 LLM ({artists_str[:40]})…")
    try:
        text = _mistral_chat(system_prompt, user_prompt, label=f"liner {bloc} / {artists_str[:30]}")
        logger.info(f"  Liner {bloc} ({voice}) — ✅ LLM OK ({len(text)} cars)")
    except Exception as e:
        logger.warning(f"Liner {bloc} ({voice}) ignoré — ❌ LLM : {e}")
        return None, None

    # Vérifier ponctuation finale et tronquer si incomplet
    punctuation_marks = ('.', '!', '?', '…')
    if not text.endswith(punctuation_marks):
        # Trouver la dernière ponctuation de fin de phrase
        last_punct = max(
            text.rfind('.'),
            text.rfind('!'),
            text.rfind('?'),
            text.rfind('…')
        )
        if last_punct > 10:  # Au moins 10 caractères avant la ponctuation
            text = text[:last_punct+1].strip()
            logger.warning(f"  Liner {bloc} ({voice}) — ⚠️  Phrase incomplète, tronquée à la dernière ponctuation")
        else:
            logger.warning(f"  Liner {bloc} ({voice}) — ⚠️  AUCUNE ponctuation trouvée, texte peut être incomplet")
    
    # Troncature intelligente : max 28 mots, respecte les phrases
    words = text.split()
    if len(words) > 28:
        truncated = []
        for word in words[:28]:
            truncated.append(word)
            if word.endswith(punctuation_marks):
                break
        if len(truncated) < len(words):
            logger.warning(f"  Liner {bloc} ({voice}) — ⚠️  Tronqué de {len(words)} à {len(truncated)} mots")
            text = " ".join(truncated)

    if verbose:
        print(f"  🗒️  Liner {bloc} texte : «{text}»", flush=True)

    # Générer le nom de fichier
    def _slug(s: str) -> str:
        n = unicodedata.normalize("NFKD", s)
        return re.sub(r"[^a-z0-9-]", "", n.encode("ascii", "ignore").decode().replace(" ", "-").lower())
    
    artists_slug = "_".join(_slug(a[:12]) for a in sorted(artists[:3]))
    filename     = f"liner-{bloc}-{week}-{artists_slug}.mp3"
    json_filename = f"liner-{bloc}-{week}-{artists_slug}.json"
    LINERS_DIR.mkdir(parents=True, exist_ok=True)
    mp3_path = LINERS_DIR / filename
    json_path = LINERS_DIR / json_filename

    # Générer le MP3 via TTS
    logger.info(f"  Liner {bloc} ({voice}) — 🔊 TTS → {filename}…")
    try:
        tts_call(normalize_for_tts(text), mp3_path, voice_id="fr_marie_happy")
        logger.info(f"  Liner {bloc} ({voice}) — ✅ TTS OK ({mp3_path.stat().st_size // 1024} Ko)")
    except Exception as e:
        logger.warning(f"Liner {bloc} ({voice}) ignoré — ❌ TTS : {e}")
        return None, None

    # Sauvegarder le label dans un fichier JSON
    json_path.write_text(
        json.dumps({"label": text, "voice": voice, "bloc": bloc, "artists": artists}, ensure_ascii=False),
        encoding="utf-8"
    )

    # Archive texte pour analyse par dream_radio
    archives_liners_dir = Path("archives/liners")
    archives_liners_dir.mkdir(parents=True, exist_ok=True)
    today_str = date.today().isoformat()
    (archives_liners_dir / f"liner-{today_str}-{bloc}-{artists_slug}.txt").write_text(text, encoding="utf-8")
    logger.info(f"  Liner {bloc} ({voice}) — 📝 Archive : archives/liners/liner-{today_str}-{bloc}-{artists_slug}.txt")
    
    public_url = f"https://famibelle.github.io/FlashInfoKarukera/liners/{filename}"
    cache[cache_key] = public_url
    save_cache(cache)
    logger.info(f"  Liner {bloc} ({voice}) — 🎙️ {public_url}")
    return public_url, text


# ── Génération des capsules culturelles ──────────────────────────────────────

def get_capsule_mp3_url(slot_id: str, verbose: bool = False) -> str | None:
    """
    Génère une capsule culturelle Guadeloupe ~15s, la sauvegarde dans docs/capsules/
    et retourne son URL publique GitHub Pages.
    Persona : Solitude (mémoire culturelle, ton solennel)
    """
    from datetime import date
    today     = date.today().isoformat()
    cache_key = f"capsule_{today}_{slot_id}"
    cache     = load_cache()

    # Construire les prompts — Persona Solitude
    try:
        system_prompt = _load_prompt("solitude_ame.md") + "\n\n" + _load_prompt("solitude_capsule.md")
    except Exception as e:
        logger.warning(f"Capsule {slot_id} ignorée : {e}")
        return None

    base_user_prompt = (
        "Génère une courte capsule audio pour une radio culturelle guadeloupéenne. "
        "Durée : environ 15 secondes (30 à 40 mots). "
        "Sujet : un élément de la flore, de la faune, de l'histoire ou de la culture de la Guadeloupe. "
        "Style : chaleureux, évocateur, comme une confidence à l'auditeur. "
        "Commence directement sans formule d'introduction. "
        "Texte brut, sans mise en forme ni titre."
    )

    # Injecter les capsules déjà générées aujourd'hui pour éviter les répétitions
    today_prefix = f"capsule_{today}_"
    previous_texts = [
        v for k, v in cache.items()
        if k.startswith(today_prefix) and k.endswith("_text") and k != cache_key + "_text"
    ]
    if previous_texts:
        context = "\n".join(f"- {t[:200]}" for t in previous_texts)
        user_prompt = (
            f"Capsules déjà diffusées aujourd'hui (choisis un sujet différent) :\n{context}\n\n"
            + base_user_prompt
        )
    else:
        user_prompt = base_user_prompt

    # Vérifier le cache
    if cache_key in cache and cache[cache_key]:
        url = cache[cache_key]
        filename = url.rsplit("/", 1)[-1]
        if (CAPSULES_DIR / filename).exists():
            logger.info(f"Capsule {slot_id} depuis cache → {url}")
            return url

    # Générer le texte via LLM
    logger.info(f"  Capsule {slot_id} — 🤖 LLM…")
    try:
        text = _mistral_chat(system_prompt, user_prompt, label=f"capsule {slot_id}")
        logger.info(f"  Capsule {slot_id} — ✅ LLM OK ({len(text)} cars)")
    except Exception as e:
        logger.warning(f"Capsule {slot_id} ignorée — ❌ LLM : {e}")
        return None

    # Sauvegarder le texte dans le cache pour éviter les répétitions
    cache[f"{cache_key}_text"] = text
    save_cache(cache)

    # Générer le slug pour le nom de fichier
    def _slug(s: str) -> str:
        n = unicodedata.normalize("NFKD", s)
        return re.sub(r"[^a-z0-9-]", "", n.encode("ascii", "ignore").decode().replace(" ", "-").lower())
    
    slot_slug = _slug(slot_id)
    filename  = f"capsule-{today}-{slot_slug}.mp3"
    
    # Créer les dossiers de sortie
    CAPSULES_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVES_CAPSULES_DIR = Path("archives/capsules")
    ARCHIVES_CAPSULES_DIR.mkdir(parents=True, exist_ok=True)

    # Sauvegarder le texte dans un fichier .txt pour analyse par le Responsable de la Programmation Musicale
    # Dans docs/capsules/ (pour référence) et archives/capsules/ (pour analyse centralisée)
    txt_filename = f"capsule-{today}-{slot_slug}.txt"
    
    # Sauvegarde principale dans archives/capsules/ (avec tous les autres journalistes)
    archives_txt_path = ARCHIVES_CAPSULES_DIR / txt_filename
    archives_txt_path.write_text(text, encoding="utf-8")
    logger.info(f"  Capsule {slot_id} — 📝 Texte sauvegardé : archives/capsules/{txt_filename}")
    
    # Sauvegarde secondaire dans docs/capsules/ (pour compatibilité)
    txt_path = CAPSULES_DIR / txt_filename
    txt_path.write_text(text, encoding="utf-8")
    mp3_path = CAPSULES_DIR / filename

    # Générer le MP3 via TTS
    logger.info(f"  Capsule {slot_id} — 🔊 TTS → {filename}…")
    try:
        tts_call(normalize_for_tts(text), mp3_path, voice_id="fr_marie_neutral")
        logger.info(f"  Capsule {slot_id} — ✅ TTS OK ({mp3_path.stat().st_size // 1024} Ko)")
    except Exception as e:
        logger.warning(f"Capsule {slot_id} ignorée — ❌ TTS : {e}")
        return None

    public_url = f"https://famibelle.github.io/FlashInfoKarukera/capsules/{filename}"
    cache[cache_key] = public_url
    save_cache(cache)
    logger.info(f"  Capsule {slot_id} — 🎙️ {public_url}")
    return public_url


# ── Entrée CLI ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Génère un liner vocal pour FlashInfoKarukera"
    )
    parser.add_argument(
        "--bloc",
        type=str,
        required=True,
        help="Type de bloc (matin/morning, midi/midday, soir/evening, etc.)"
    )
    parser.add_argument(
        "--artists",
        type=str,
        required=True,
        help="Liste d'artistes séparés par des virgules"
    )
    parser.add_argument(
        "--voice",
        type=str,
        default="corinne",
        help="Voix à utiliser (default: corinne)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mode verbeux"
    )
    
    args = parser.parse_args()
    
    # Configurer le logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler()]
    )
    
    # Parser les artistes
    artists = [a.strip() for a in args.artists.split(",") if a.strip()]
    
    if not artists:
        parser.error("Au moins un artiste est requis")
    
    # Générer le liner
    url, text = get_announcement_mp3_url(
        bloc=args.bloc,
        artists=artists,
        voice=args.voice,
        verbose=args.verbose
    )
    
    if url:
        print(f"\n✅ Liner généré : {url}")
    if text:
        print(f"📝 Texte : «{text}»")
    if not url:
        print("❌ Échec de la génération du liner")
