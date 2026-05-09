#!/usr/bin/env python3
"""
generate_interview.py

Génère l'interview radio "Creole Resistance Symbols" en anglais.
  - Texte produit par LLM Mistral à partir de kreyol_resistance_symbol.md
  - TTS Voxtral (en_paul_*, gb_oliver_*) : ton ajusté au contenu de chaque réplique
  - Sortie : docs/audio/Emissions/interview-resistance-creole-YYYY-MM-DD.mp3 + .json

Usage:
    python generate_interview.py
    python generate_interview.py --verbose
    python generate_interview.py --dry-run          # texte seul, pas de TTS
    python generate_interview.py --dialogue foo.json # réutilise un dialogue existant
"""

import argparse
import json
import os
import random
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent))
from tts_utils import tts_call, normalize_for_tts
from datetime import date as Date

# Import dynamique de flash-info-gwada (fichier avec tirets)
import importlib.util
spec = importlib.util.spec_from_file_location("flash_info_gwada", str(Path(__file__).parent / "flash-info-gwada.py"))
flash_info_gwada = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flash_info_gwada)
fetch_weather = flash_info_gwada.fetch_weather
fetch_horoscope = flash_info_gwada.fetch_horoscope
_sign_for_date = flash_info_gwada._sign_for_date

# ── Config ────────────────────────────────────────────────────────────────────

PROMPTS_DIR       = Path(__file__).parent / "private" / "prompts"
INDEX_CULTUREL_DIR = Path(__file__).parent / "private" / "index_culturel"
SOURCE_FILES = [
    INDEX_CULTUREL_DIR / "kreyol_resistance_symbol_ref.md",
    INDEX_CULTUREL_DIR / "faune_guadeloupe_ref.md",
    INDEX_CULTUREL_DIR / "flore_guadeloupe_ref.md",
    INDEX_CULTUREL_DIR / "lieux_spirituels_ref.md",
    INDEX_CULTUREL_DIR / "histoire_guadeloupe_ref.md",
]
OUTPUT_DIR  = Path("docs/audio/Emissions")

MISTRAL_MODEL = "mistral-large-latest"

# Utilisation des voix Paul (journalist) et Oliver (expert)
SPEAKER_BASE_TONE = {
    "journalist": "neutral",   # Paul (en_paul_*)
    "expert":     "neutral",   # Oliver (gb_oliver_*)
}

# Tons autorisés par Voxtral
VALID_TONES = {"neutral", "happy", "excited", "sad", "angry", "frustrated", "confident", "cheerful", "curious"}

# Contraintes par locuteur (fallback pour les tons non disponibles)
SPEAKER_TONE_CAP = {
    "journalist": {"curious": "happy"},  # Paul n'a pas de ton "curious"
    "expert":     {},
}

SILENCE_BETWEEN = 0.4  # secondes entre répliques

# ── LLM ──────────────────────────────────────────────────────────────────────

def _mistral_chat(system: str, user: str) -> str:
    import urllib.request, urllib.error, time

    key     = os.environ["MISTRAL_API_KEY"]
    payload = json.dumps({
        "model":           MISTRAL_MODEL,
        "messages":        [{"role": "system", "content": system},
                            {"role": "user",   "content": user}],
        "temperature":     0.8,
        "max_tokens":      2048,
        "response_format": {"type": "json_object"},
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
                import time as _time
                wait = 15 * 2 ** attempt
                print(f"   ⏳ LLM {e.code} — attente {wait}s…")
                _time.sleep(wait)
            else:
                raise RuntimeError(f"LLM HTTP {e.code}: {body}") from None
    raise RuntimeError("LLM : trop de tentatives")


# ── Génération du dialogue ────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a scriptwriter for a Caribbean cultural radio station.
You understand French and Kreyol, but write in english. You use french only when needed and you give the english word equivalent when saying word in french 
Write a 3-minute radio interview STRICTLY IN ENGLISH between a journalist (Paul) and a cultural
researcher (Oliver) about the living symbols of Creole resistance AND the rich history of Guadeloupe.

IMPORTANT: Both Paul and Oliver are passionate Artifical Intelligence personalities dedicated to Guadeloupe.
They must introduce themselves as Artificial Intelligence specialized in Guadeloupean culture at the beginning of the interview.

Structure the interview in 3 parts:
1. Introduction: Both introduce themselves as Artificial Intelligence. Paul asks Oliver about the historical depth of Guadeloupe, mentioning Arawaks, colonization, and Creole heritage and Guadeloupe history.
2. Body: Alternate between Creole symbols (animals, plants, spiritual places) and their historical context. Connect each symbol to its historical significance in Guadeloupe's past.
3. Conclusion: Reflect on how history and symbols together shape modern Guadeloupean identity and resistance.

Rules:
- Approximately 400-430 words total (3 minutes at radio pace)
- At least 8 alternating turns (Paul / Oliver)
- Natural, captivating, educational — not a lecture
- Start with Paul's introduction where both identify themselves as AI assistants passionate about Guadeloupe
- End with a warm closing exchange reflecting on history and symbols
- Each turn: plain text only, no stage directions, no markdown
- CRITICAL: Generate a DIFFERENT interview each time, exploring new angles, examples, and perspectives
- CRITICAL: Never repeat the same narrative structure, examples, or phrasing from previous runs

Return a JSON object with key "dialogue": array of turns.
Each turn must have:
  "speaker": "journalist" or "expert"
  "text": the spoken line (IN ENGLISH)
  "tone": one of neutral | happy | excited | sad | angry | curious
"""


def _select_random_lines_from_file(filepath: Path, num_lines: int = 3) -> list[str]:
    """Sélectionne aléatoirement N lignes de tableau Markdown d'un fichier _ref.md.
    
    Args:
        filepath: Chemin vers le fichier _ref.md (format table Markdown)
        num_lines: Nombre de lignes à sélectionner
    
    Returns:
        Liste de lignes nettoyées (sans |, formatées pour le LLM)
    """
    # Mots à exclure (en-têtes de colonnes)
    header_keywords = ['famille', 'nom créole', 'nom français', 'nom scientifique', 
                       'sacré', 'dimension culturelle', 'usage', 'catégorie', 'nom du lieu',
                       'commune', 'localisation']
    
    data_lines = []
    content = filepath.read_text(encoding="utf-8")
    
    for line in content.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        # Une ligne de données valide a au moins 2+ pipes (3+ colonnes) et n'est pas un séparateur
        pipe_count = stripped.count('|')
        if pipe_count >= 2 and '---' not in stripped:
            # Nettoyer la ligne : enlever les | de début/fin
            clean_line = stripped[1:-1].strip()
            # Vérifier qu'il y a au moins 2 colonnes NON VIDES
            cells = [c.strip() for c in clean_line.split('|')]
            non_empty_cells = [c for c in cells if c]
            if len(non_empty_cells) >= 2:
                # Exclure les lignes d'en-tête
                line_lower = clean_line.lower()
                if not any(keyword in line_lower for keyword in header_keywords):
                    # Remplacer les | par des tabulations pour lisibilité
                    clean_line = clean_line.replace('|', '\t')
                    data_lines.append(clean_line)
    
    # Mélanger et sélectionner
    random.shuffle(data_lines)
    return data_lines[:min(num_lines, len(data_lines))]


def _get_random_spiritual_elements(num_per_file: int = 5) -> str:
    """Sélectionne aléatoirement num_per_file éléments de CHACUN des fichiers _ref.md.
    
    Args:
        num_per_file: Nombre d'éléments à sélectionner par fichier
    
    Returns:
        String formaté pour le LLM avec tous les éléments groupés par fichier
    """
    # Mapping des noms de fichiers vers des titres lisibles pour le LLM
    file_titles = {
        "kreyol_resistance_symbol_ref.md": "Creole Resistance Symbols",
        "faune_guadeloupe_ref.md": "Fauna of Guadeloupe",
        "flore_guadeloupe_ref.md": "Flora of Guadeloupe",
        "lieux_spirituels_ref.md": "Spiritual Places of Guadeloupe",
        "histoire_guadeloupe_ref.md": "History of Guadeloupe",
    }
    
    result = "Randomly selected Creole symbols from Guadeloupe (for unique inspiration):\n\n"
    ref_files = SOURCE_FILES
    counter = 1
    
    for filepath in ref_files:
        if filepath.exists():
            file_lines = _select_random_lines_from_file(filepath, num_per_file)
            if file_lines:
                # Nom du fichier sans le chemin + mapping vers titre lisible
                file_name = filepath.name
                display_title = file_titles.get(file_name, file_name)
                result += f"__ {display_title} __\n"
                for line in file_lines:
                    result += f"{counter}. {line}\n"
                    counter += 1
                result += "\n"
        else:
            print(f"⚠️  Fichier introuvable : {filepath}", file=sys.stderr)
    
    return result


def generate_dialogue(verbose: bool = False) -> list[dict]:
    # Récupère la météo et l'horoscope du jour pour un contexte unique à chaque exécution
    today = Date.today()
    print("🌍 Génération du contexte dynamique pour un dialogue unique...")
    
    weather = ""
    horoscope_text = ""
    
    try:
        weather = fetch_weather(today)
        print(f"   🌤️  Météo du jour: {weather[:60]}...")
    except Exception as e:
        print(f"   ⚠️  Météo indisponible: {e}")
    
    try:
        # Signe du jour + 2 signes aléatoires (total: 3)
        daily_sign = _sign_for_date(today)
        horoscope_result = fetch_horoscope(n_signs=3, include_signs=[daily_sign])
        if horoscope_result:
            horoscope_text, signs_list = horoscope_result
            # Si on n'a pas 3 signes, réessayer sans contrainte
            if len(signs_list) < 3:
                horoscope_result = fetch_horoscope(n_signs=3)
                if horoscope_result:
                    horoscope_text, signs_list = horoscope_result
            print(f"   🔮  Horoscope ({len(signs_list)} signes: {', '.join(signs_list)}): {horoscope_text[:80]}...")
    except Exception as e:
        print(f"   ⚠️  Horoscope indisponible: {e}")
        horoscope_text = ""
    
    # Sélection aléatoire de 3 éléments par fichier (12 total) pour varier le contenu
    source_text = _get_random_spiritual_elements(num_per_file=3)
    
    # Ajoute un identifiant unique par exécution (solution 3)
    unique_id = random.randint(10000, 99999)
    
    # Ajoute le contexte dynamique au prompt utilisateur
    context_dynamics = []
    if weather:
        context_dynamics.append(f"TODAY'S WEATHER IN GUADELOUPE: {weather}")
    if horoscope_text:
        # Séparer chaque signe par un double saut de ligne pour la lisibilité
        formatted_horoscope = horoscope_text.replace('\n', '\n\n')
        context_dynamics.append(f"TODAY'S HOROSCOPE:\n\n{formatted_horoscope}")
    
    dynamics_str = "\n\n".join(context_dynamics) + "\n\n" if context_dynamics else ""
    
    user_prompt = (
        f"{dynamics_str}UNIQUE_RUN_ID: {unique_id}\n\nReference material — living symbols of Creole resistance:\n{source_text}"
    )
    if verbose:
        print("\n── SYSTEM PROMPT ─────────────────────────────────────────────")
        print(SYSTEM_PROMPT)
        print("\n── USER PROMPT ─────────────────────────────────────────────────")
        print(user_prompt)
        print()

    print("🤖 Génération du dialogue (LLM)…")
    raw      = _mistral_chat(SYSTEM_PROMPT, user_prompt)
    data     = json.loads(raw)
    dialogue = data.get("dialogue", data) if isinstance(data, dict) else data

    if not isinstance(dialogue, list):
        raise ValueError(f"Format inattendu — 'dialogue' doit être une liste : {type(dialogue)}")

    for turn in dialogue:
        if turn.get("tone") not in VALID_TONES:
            turn["tone"] = SPEAKER_BASE_TONE.get(turn.get("speaker", "expert"), "neutral")

    return dialogue


# ── Sélection de la voix ──────────────────────────────────────────────────────

def voice_id_for(turn: dict) -> str:
    """Retourne le voice_id Voxtral pour ce locuteur et ce ton.
    - journalist (Paul) → voix en_paul_*
    - expert (Oliver) → voix gb_oliver_*
    """
    speaker = turn.get("speaker", "expert")
    tone = turn.get("tone", SPEAKER_BASE_TONE[speaker])

    # Appliquer les contraintes de registre par locuteur
    tone = SPEAKER_TONE_CAP.get(speaker, {}).get(tone, tone)

    # Mappage direct selon le locuteur
    if speaker == "journalist":
        # Voix Paul pour le journaliste
        tone_map = {
            "neutral": "en_paul_neutral",
            "happy": "en_paul_happy",
            "excited": "en_paul_excited",
            "sad": "en_paul_sad",
            "angry": "en_paul_angry",
            "frustrated": "en_paul_frustrated",
            "confident": "en_paul_confident",
            "cheerful": "en_paul_cheerful",
            "curious": "en_paul_happy",  # fallback : pas de "curious" pour Paul
        }
        return tone_map.get(tone, "en_paul_neutral")
    else:
        # Voix Oliver pour l'expert - seule neutral disponible dans les logs
        return "gb_oliver_neutral"


# ── Assemblage FFmpeg ─────────────────────────────────────────────────────────

def _silence_mp3(duration: float, path: Path) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={duration}",
        "-c:a", "libmp3lame", "-q:a", "4", str(path),
    ], check=True)


def concat_segments(seg_paths: list[Path], output_path: Path) -> None:
    all_files: list[Path] = []
    for i, sp in enumerate(seg_paths):
        all_files.append(sp)
        if i < len(seg_paths) - 1:
            all_files.append(sp.parent / f"_sil_{i:02d}.mp3")

    inputs     = [arg for f in all_files for arg in ("-i", str(f))]
    n          = len(all_files)
    filter_str = "".join(f"[{i}:a]" for i in range(n)) + f"concat=n={n}:v=0:a=1[out]"

    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[out]",
        "-c:a", "libmp3lame", "-q:a", "2",
        str(output_path),
    ], check=True)


# ── Pipeline principal ────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Interview radio — Symboles de la Résistance Créole")
    parser.add_argument("--verbose",  action="store_true", help="Affiche prompts et sorties LLM")
    parser.add_argument("--dry-run",  action="store_true", help="Texte seul, sans TTS")
    parser.add_argument("--dialogue", help="JSON dialogue existant (saute l'étape LLM)")
    args = parser.parse_args()

    for f in SOURCE_FILES:
        if not f.exists():
            sys.exit(f"❌ Source introuvable : {f}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today    = date.today().isoformat()
    out_mp3  = OUTPUT_DIR / f"interview-resistance-creole-{today}.mp3"
    out_json = OUTPUT_DIR / f"interview-resistance-creole-{today}.json"

    # ── Dialogue ──────────────────────────────────────────────────────────────
    if args.dialogue:
        print(f"📂 Dialogue chargé : {args.dialogue}")
        dialogue = json.loads(Path(args.dialogue).read_text(encoding="utf-8"))
        if isinstance(dialogue, dict):
            dialogue = dialogue.get("dialogue", dialogue)
    else:
        dialogue = generate_dialogue(verbose=args.verbose)

    total_words = sum(len(t["text"].split()) for t in dialogue)
    print(f"✅ {len(dialogue)} répliques · {total_words} mots")

    # ── JSON ──────────────────────────────────────────────────────────────────
    output_data = {
        "date":     today,
        "title":    "Creole Resistance Symbols — Radio Interview",
        "duration": "~3 minutes",
        "speakers": {
            "journalist": {"name": "Paul", "base_tone": SPEAKER_BASE_TONE["journalist"],
                           "voice": "en_paul_neutral"},
            "expert":     {"name": "Oliver", "base_tone": SPEAKER_BASE_TONE["expert"],
                           "voice": "gb_oliver_neutral"},
        },
        "dialogue": dialogue,
    }
    out_json.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾 JSON → {out_json}")

    if args.dry_run:
        print("\n── Dialogue complet ──────────────────────────────────────────")
        for turn in dialogue:
            speaker = "Paul" if turn["speaker"] == "journalist" else "Oliver"
            vid = voice_id_for(turn)
            print(f"\n[{speaker} / {turn['tone']} → {vid}]")
            print(turn["text"])
        print(f"\n⏭️  TTS ignoré (--dry-run)")
        return

    # ── TTS + assemblage ──────────────────────────────────────────────────────
    with tempfile.TemporaryDirectory(prefix="interview_") as tmpdir:
        tmp       = Path(tmpdir)
        seg_paths: list[Path] = []

        print(f"\n🔊 TTS ({len(dialogue)} répliques)…")
        for i, turn in enumerate(dialogue):
            seg_path = tmp / f"seg_{i:02d}.mp3"
            speaker  = "Paul" if turn["speaker"] == "journalist" else "Oliver"
            vid      = voice_id_for(turn)
            print(f"   [{i+1}/{len(dialogue)}] {speaker} [{turn['tone']} → {vid}]…", flush=True)
            if args.verbose:
                print(f"      {turn['text'][:90]}{'…' if len(turn['text'])>90 else ''}")
            tts_call(normalize_for_tts(turn["text"]), seg_path, voice_id=vid)
            seg_paths.append(seg_path)
            if i < len(dialogue) - 1:
                _silence_mp3(SILENCE_BETWEEN, tmp / f"_sil_{i:02d}.mp3")

        print("   🔗 Assemblage FFmpeg…")
        concat_segments(seg_paths, out_mp3)

    size_kb = out_mp3.stat().st_size // 1024
    print(f"✅ MP3 → {out_mp3} ({size_kb} Ko)")

    # Lecture automatique du MP3 si --dry-run n'est pas activé
    if not args.dry_run:
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


if __name__ == "__main__":
    main()
