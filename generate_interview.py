#!/usr/bin/env python3
"""
generate_interview.py

Génère l'interview radio "Creole Resistance Symbols" en anglais.
  - Texte produit par LLM Mistral à partir de kreyol_resistance_symbol.md
  - TTS Voxtral bilingue : Jane (journaliste) + Paul (chercheur)
  - Ton adapté au contenu de chaque réplique
  - Sortie : docs/audio/Emissions/interview_YYYYMMDD.mp3 + .json

Usage:
    python generate_interview.py
    python generate_interview.py --verbose
    python generate_interview.py --dry-run   # texte seul, pas de TTS
"""

import argparse
import json
import os
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

# ── Dépendances locales ───────────────────────────────────────────────────────

sys.path.insert(0, str(Path(__file__).parent))
from tts_utils import tts_call

# ── Config ────────────────────────────────────────────────────────────────────

PROMPTS_DIR  = Path(__file__).parent / "private" / "prompts"
SOURCE_FILE  = PROMPTS_DIR / "kreyol_resistance_symbol.md"
OUTPUT_DIR   = Path("docs/audio/Emissions")

MISTRAL_MODEL = "mistral-large-latest"

# Voix Voxtral anglaises : base_name + tone = voice_id
VOICE_JOURNALIST_BASE = "en_jane"
VOICE_EXPERT_BASE     = "en_paul"

# Tons Voxtral disponibles (fallback → neutral si le ton demandé n'existe pas)
VALID_TONES = {"neutral", "happy", "excited", "sad", "angry", "curious"}

# Silence entre répliques (secondes)
SILENCE_BETWEEN = 0.35

# ── LLM ──────────────────────────────────────────────────────────────────────

def _mistral_chat(system: str, user: str) -> str:
    import urllib.request, urllib.error
    import time

    key     = os.environ["MISTRAL_API_KEY"]
    payload = json.dumps({
        "model":    MISTRAL_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "temperature": 0.8,
        "max_tokens":  2048,
        "response_format": {"type": "json_object"},
    }).encode()

    req = urllib.request.Request(
        "https://api.mistral.ai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type":  "application/json",
        },
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
    raise RuntimeError("LLM : trop de tentatives échouées")


# ── Génération du dialogue ─────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a scriptwriter for a Caribbean cultural radio station.
Write a 3-minute radio interview in English between a journalist (Jane) and a cultural researcher (Paul)
about the living symbols of Creole resistance in Guadeloupe: animals, plants, and trees used by
Arawaks, Maroons, and enslaved people as emblems of survival, freedom, and identity.

The interview must:
- Be warm, captivating, and educational — aimed at a general audience
- Last approximately 3 minutes (around 420-450 words total across all turns)
- Feel natural and spontaneous, not like a lecture
- Begin with Jane's introduction and end with a closing exchange
- Include at least 6 exchanges (alternating Jane / Paul)

Return a JSON object with a single key "dialogue", containing an array of turns.
Each turn must have:
  "speaker": "journalist" or "expert"
  "text": the spoken line (plain text, no stage directions, no markdown)
  "tone": one of neutral, happy, excited, sad, angry, curious — matching the emotional register of the line

Example:
{
  "dialogue": [
    {"speaker": "journalist", "text": "Good morning everyone...", "tone": "neutral"},
    {"speaker": "expert",     "text": "Thank you Jane...",        "tone": "happy"}
  ]
}"""


def generate_dialogue(source_text: str, verbose: bool = False) -> list[dict]:
    user_prompt = (
        "Here is the reference material about the living symbols of Creole resistance:\n\n"
        + source_text
    )

    if verbose:
        print("\n── SYSTEM PROMPT ─────────────────────────────────────────────")
        print(SYSTEM_PROMPT)
        print("\n── USER PROMPT ───────────────────────────────────────────────")
        print(user_prompt[:400], "…")
        print()

    print("🤖 Génération du dialogue (LLM)…")
    raw = _mistral_chat(SYSTEM_PROMPT, user_prompt)

    if verbose:
        print("\n── RAW LLM OUTPUT ────────────────────────────────────────────")
        print(raw[:800], "…" if len(raw) > 800 else "")
        print()

    data = json.loads(raw)
    dialogue = data.get("dialogue", data) if isinstance(data, dict) else data
    if not isinstance(dialogue, list):
        raise ValueError(f"Format inattendu — 'dialogue' doit être une liste : {type(dialogue)}")

    for turn in dialogue:
        if turn.get("tone") not in VALID_TONES:
            turn["tone"] = "neutral"

    return dialogue


# ── TTS par réplique ──────────────────────────────────────────────────────────

def voice_id_for(turn: dict) -> str:
    base = VOICE_JOURNALIST_BASE if turn["speaker"] == "journalist" else VOICE_EXPERT_BASE
    tone = turn.get("tone", "neutral")
    return f"{base}_{tone}"


def synthesise_turn(turn: dict, seg_path: Path, verbose: bool = False) -> None:
    vid  = voice_id_for(turn)
    text = turn["text"]
    if verbose:
        speaker = "Jane" if turn["speaker"] == "journalist" else "Paul"
        print(f"   🎙️  {speaker} [{turn['tone']}] → {vid}")
        print(f"      {text[:80]}{'…' if len(text) > 80 else ''}")
    tts_call(text, seg_path, voice_id=vid)


# ── Assemblage FFmpeg ─────────────────────────────────────────────────────────

def _silence_mp3(duration: float, path: Path) -> Path:
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={duration}",
        "-c:a", "libmp3lame", "-q:a", "4",
        str(path),
    ], check=True)
    return path


def concat_segments(seg_paths: list[Path], output_path: Path) -> None:
    all_files: list[Path] = []
    for i, sp in enumerate(seg_paths):
        all_files.append(sp)
        if i < len(seg_paths) - 1:
            all_files.append(sp.parent / f"_silence_{i:02d}.mp3")

    inputs = []
    for f in all_files:
        inputs += ["-i", str(f)]

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
    parser = argparse.ArgumentParser(description="Génère l'interview radio Créole Résistance")
    parser.add_argument("--verbose",  action="store_true", help="Affiche prompts et sorties LLM")
    parser.add_argument("--dry-run",  action="store_true", help="Génère le texte seulement, pas de TTS")
    parser.add_argument("--dialogue", help="Fichier JSON dialogue existant (saute l'étape LLM)")
    args = parser.parse_args()

    if not SOURCE_FILE.exists():
        sys.exit(f"❌ Source introuvable : {SOURCE_FILE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today     = date.today().isoformat()
    out_mp3   = OUTPUT_DIR / f"interview-resistance-creole-{today}.mp3"
    out_json  = OUTPUT_DIR / f"interview-resistance-creole-{today}.json"

    # ── Dialogue ──────────────────────────────────────────────────────────────

    if args.dialogue:
        print(f"📂 Chargement dialogue : {args.dialogue}")
        dialogue = json.loads(Path(args.dialogue).read_text(encoding="utf-8"))
    else:
        source_text = SOURCE_FILE.read_text(encoding="utf-8")
        dialogue    = generate_dialogue(source_text, verbose=args.verbose)

    total_words = sum(len(t["text"].split()) for t in dialogue)
    print(f"✅ Dialogue : {len(dialogue)} répliques · {total_words} mots")

    # ── JSON ──────────────────────────────────────────────────────────────────

    output_data = {
        "date":     today,
        "title":    "Creole Resistance Symbols — Radio Interview",
        "duration": "~3 minutes",
        "speakers": {
            "journalist": {"name": "Jane", "voice_base": VOICE_JOURNALIST_BASE},
            "expert":     {"name": "Paul", "voice_base": VOICE_EXPERT_BASE},
        },
        "dialogue": dialogue,
    }
    out_json.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾 JSON → {out_json}")

    if args.dry_run:
        print("\n── DRY RUN — Dialogue complet ───────────────────────────────")
        for turn in dialogue:
            speaker = "Jane" if turn["speaker"] == "journalist" else "Paul"
            print(f"\n[{speaker} / {turn['tone']}]")
            print(turn["text"])
        print(f"\n⏭️  TTS ignoré (--dry-run)")
        return

    # ── TTS + assemblage ──────────────────────────────────────────────────────

    with tempfile.TemporaryDirectory(prefix="interview_") as tmpdir:
        tmp = Path(tmpdir)
        seg_paths: list[Path] = []

        print(f"\n🔊 TTS ({len(dialogue)} répliques)…")
        for i, turn in enumerate(dialogue):
            seg_path = tmp / f"seg_{i:02d}.mp3"
            print(f"   [{i+1}/{len(dialogue)}] ", end="", flush=True)
            synthesise_turn(turn, seg_path, verbose=args.verbose)
            if not args.verbose:
                speaker = "Jane" if turn["speaker"] == "journalist" else "Paul"
                print(f"{speaker} [{turn['tone']}] ✓")
            seg_paths.append(seg_path)

            if i < len(dialogue) - 1:
                _silence_mp3(SILENCE_BETWEEN, tmp / f"_silence_{i:02d}.mp3")

        print("   🔗 Assemblage FFmpeg…")
        concat_segments(seg_paths, out_mp3)

    size_kb = out_mp3.stat().st_size // 1024
    print(f"✅ MP3 → {out_mp3} ({size_kb} Ko)")


if __name__ == "__main__":
    main()
