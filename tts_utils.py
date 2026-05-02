#!/usr/bin/env python3
"""
tts_utils — pipeline TTS/STT partagé (Voxtral / Mistral API)
Utilisé par flash-info-gwada.py, horoscope-gwada.py et youtube_uploader.py
"""

import os
import re as _re
import json
import base64
import time
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

TTS_MODEL         = "voxtral-mini-tts-2603"
STT_MODEL         = "voxtral-mini-latest"
TTS_VOICE_DEFAULT = "fr_marie_neutral"
TTS_VOICES = {
    "neutral":  "fr_marie_neutral",
    "happy":    "fr_marie_happy",
    "excited":  "fr_marie_excited",
    "sad":      "fr_marie_sad",
    "angry":    "fr_marie_angry",
    "curious":  "fr_marie_curious",
}

STINGERS_DIR = Path(__file__).parent / "Stingers"

# ── Données locales ───────────────────────────────────────────────────────────

from data.tts_normalize import (
    PRONONCIATIONS_LOCALES as _PRONONCIATIONS_LOCALES,
    SIGLES_MOT as _SIGLES_MOT,
    ABBREVS as _ABBREVS,
)

# ── num2words helpers ─────────────────────────────────────────────────────────

try:
    from num2words import num2words as _n2w

    def _num_fr(n: str) -> str:
        s = n.replace(" ", "").replace(" ", "").replace(",", ".")
        try:
            return _n2w(float(s) if "." in s else int(s), lang="fr")
        except Exception:
            return n

    def _ordinal_fr(n: str) -> str:
        try:
            return _n2w(int(n), lang="fr", to="ordinal")
        except Exception:
            return n

except ImportError:
    print("   ⚠️  num2words manquant — pip install num2words")

    def _num_fr(n: str) -> str: return n
    def _ordinal_fr(n: str) -> str: return n

# ── Données de normalisation ──────────────────────────────────────────────────

_DOM_CODES = {
    "971": "quatre-vingt-dix-sept-un",
    "972": "quatre-vingt-dix-sept-deux",
    "973": "quatre-vingt-dix-sept-trois",
    "974": "quatre-vingt-dix-sept-quatre",
    "976": "quatre-vingt-dix-sept-six",
}

_UNIT_PATTERNS = [
    (r"(\d+(?:[,\.]\d+)?)\s*°C",   lambda m: f"{_num_fr(m.group(1))} degrés"),
    (r"(\d+(?:[,\.]\d+)?)\s*km/h", lambda m: f"{_num_fr(m.group(1))} kilomètres par heure"),
    (r"(\d+(?:[,\.]\d+)?)\s*km\b", lambda m: f"{_num_fr(m.group(1))} kilomètres"),
    (r"(\d+(?:[,\.]\d+)?)\s*mm\b", lambda m: f"{_num_fr(m.group(1))} millimètres"),
    (r"(\d+(?:[,\.]\d+)?)\s*%",    lambda m: f"{_num_fr(m.group(1))} pour cent"),
    (r"(\d+(?:[,\.]\d+)?)\s*m²",   lambda m: f"{_num_fr(m.group(1))} mètres carrés"),
]


# ── Normalisation texte pour TTS ──────────────────────────────────────────────

def _norm_pronunciations(text: str) -> str:
    for ecrit, oral in _PRONONCIATIONS_LOCALES.items():
        text = _re.sub(r"\b" + _re.escape(ecrit) + r"\b", oral, text)
    return text


def _norm_typography(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", " ")
    return _re.sub(r"[^\x00-\x7FÀ-ɏḀ-ỿ\n]", " ", text)


def _norm_numero(text: str) -> str:
    text = _re.sub(r"\bn°\s*", "numéro ", text, flags=_re.IGNORECASE)
    text = _re.sub(r"\bN°\s*", "Numéro ", text)
    return text


def _norm_ordinals(text: str) -> str:
    text = _re.sub(r"\b1er\b", "premier", text)
    text = _re.sub(r"\b1re\b", "première", text)
    return _re.sub(r"\b(\d+)(?:e|ème|eme)\b",
                   lambda m: _ordinal_fr(m.group(1)), text)


def _norm_currencies(text: str) -> str:
    text = _re.sub(r"(\d+(?:[,\.]\d+)?)\s*[Mm](?:illions?)?\s*€",
                   lambda m: f"{_num_fr(m.group(1))} millions d'euros", text)
    text = _re.sub(r"(\d+(?:[,\.]\d+)?)\s*€",
                   lambda m: f"{_num_fr(m.group(1))} euros", text)
    text = _re.sub(r"(\d+(?:[,\.]\d+)?)\s*\$",
                   lambda m: f"{_num_fr(m.group(1))} dollars", text)
    return text


def _norm_scores(text: str) -> str:
    return _re.sub(r"\b(\d+)-(\d+)\b",
                   lambda m: f"{_num_fr(m.group(1))} à {_num_fr(m.group(2))}", text)


def _norm_dom_codes(text: str) -> str:
    for code, spoken in _DOM_CODES.items():
        text = _re.sub(r"\b" + code + r"\b", spoken, text)
    return text


def _norm_hours(text: str) -> str:
    def _expand(m):
        h, minute = m.group(1), m.group(2)
        if minute and minute != "00":
            return f"{_num_fr(h)} heures {_num_fr(minute)}"
        return f"{_num_fr(h)} heures"
    text = _re.sub(r"\b(\d{1,2})h(\d{2})?\b", _expand, text)
    return _re.sub(r"\b(\d{1,2}):(\d{2})\b",
                   lambda m: f"{_num_fr(m.group(1))} heures {_num_fr(m.group(2))}", text)


def _norm_units(text: str) -> str:
    for pattern, repl in _UNIT_PATTERNS:
        text = _re.sub(pattern, repl, text, flags=_re.IGNORECASE)
    return text


def _norm_plain_numbers(text: str) -> str:
    return _re.sub(r"\b(\d[\d ]*(?:[,\.]\d+)?)\b",
                   lambda m: _num_fr(m.group(1)), text)


def _norm_acronyms(text: str) -> str:
    for sm in _SIGLES_MOT:
        dotted = ".".join(sm)
        text = text.replace(dotted + ".", sm).replace(dotted, sm)
    text = _re.sub(
        r"\b([A-Z](?:\.[A-Z]){1,4})\.?\b",
        lambda m: m.group(1).replace(".", ". ") + ".",
        text,
    )
    return _re.sub(
        r"\b([A-Z]{2,5})\b",
        lambda m: m.group(1) if m.group(1) in _SIGLES_MOT else ". ".join(m.group(1)) + ".",
        text,
    )


def _norm_abbreviations(text: str) -> str:
    for abbr, full in _ABBREVS.items():
        if abbr[0].isalpha():
            escaped = _re.escape(abbr)
            pattern = r"\b" + escaped + (r"\b" if abbr[-1].isalnum() else "")
            text = _re.sub(pattern, full, text)
        else:
            text = text.replace(abbr, full)
    return text


def _norm_honorifics(text: str) -> str:
    return _re.sub(r"\bMe\b(?=\s+[A-ZÀ-Ü])", "Maître", text)


def _norm_residual(text: str) -> str:
    text = _re.sub(r"[#*\[\]_~`|\\^@]", " ", text)
    text = _re.sub(r"/", " sur ", text)
    text = _re.sub(r" {2,}", " ", text)
    text = _re.sub(r"\n{2,}", "\n", text)
    return text


_NORMALIZATION_PIPELINE = (
    _norm_pronunciations,
    _norm_typography,
    _norm_numero,
    _norm_ordinals,
    _norm_currencies,
    _norm_scores,
    _norm_dom_codes,
    _norm_hours,
    _norm_units,
    _norm_plain_numbers,
    _norm_acronyms,
    _norm_abbreviations,
    _norm_honorifics,
    _norm_residual,
)


def normalize_for_tts(text: str) -> str:
    for step in _NORMALIZATION_PIPELINE:
        text = step(text)
    return text.strip()


# ── TTS ───────────────────────────────────────────────────────────────────────

def tts_call(
    text: str,
    output_path: Path,
    voice_id: str = TTS_VOICE_DEFAULT,
    *,
    api_key: str | None = None,
    _retries: int = 4,
) -> None:
    if not text.strip():
        raise RuntimeError("tts_call: texte vide")
    _key = api_key or os.environ["MISTRAL_API_KEY"]
    payload = json.dumps({
        "input": text,
        "model": TTS_MODEL,
        "response_format": "mp3",
        "voice_id": voice_id,
    }).encode()
    req = urllib.request.Request(
        "https://api.mistral.ai/v1/audio/speech",
        data=payload,
        headers={
            "Authorization": f"Bearer {_key}",
            "Content-Type": "application/json",
        },
    )
    for attempt in range(_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                response = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code in (429, 500, 502, 503, 504) and attempt < _retries:
                wait = 15 * 2 ** attempt
                print(f"   ⏳ TTS {e.code} — attente {wait}s (tentative {attempt + 1}/{_retries})…")
                time.sleep(wait)
            else:
                raise RuntimeError(f"TTS HTTP {e.code} ({e.reason}): {body}") from None
    if "audio_data" not in response:
        raise RuntimeError(f"TTS error: {response}")
    output_path.write_bytes(base64.b64decode(response["audio_data"]))


# ── STT ───────────────────────────────────────────────────────────────────────

def _stt_raw(audio_path: Path, word_timestamps: bool = False, *, api_key: str | None = None) -> dict:
    _key = api_key or os.environ["MISTRAL_API_KEY"]
    boundary = "----TranscriptBoundary"
    audio_data = audio_path.read_bytes()
    fields = [("model", STT_MODEL)]
    if word_timestamps:
        fields.append(("timestamp_granularities", "word"))
    body = b""
    for name, value in fields:
        body += (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        ).encode()
    body += (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{audio_path.name}"\r\n'
        f"Content-Type: audio/mpeg\r\n\r\n"
    ).encode() + audio_data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        "https://api.mistral.ai/v1/audio/transcriptions",
        data=body,
        headers={
            "Authorization": f"Bearer {_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                wait = 10 * 2 ** attempt
                print(f"   ⏳ STT 429 — attente {wait}s (tentative {attempt + 1}/5)…")
                time.sleep(wait)
            else:
                body_err = e.read().decode(errors="replace")
                raise RuntimeError(f"STT HTTP {e.code}: {body_err}") from None


def transcribe_audio(audio_path: Path, *, api_key: str | None = None) -> str:
    return _stt_raw(audio_path, api_key=api_key)["text"]


def transcribe_with_words(audio_path: Path, *, api_key: str | None = None) -> list[dict]:
    segments = _stt_raw(audio_path, word_timestamps=True, api_key=api_key).get("segments", [])
    return [
        {"word": s["text"].strip(), "start": s["start"], "end": s["end"]}
        for s in segments
        if s.get("text", "").strip()
    ]


# ── Audio ─────────────────────────────────────────────────────────────────────

def resolve_stinger(name: str | None = None) -> Path:
    STINGERS_DIR.mkdir(exist_ok=True)
    available = sorted(STINGERS_DIR.glob("*.mp3")) + sorted(STINGERS_DIR.glob("*.wav"))
    if name:
        candidate = STINGERS_DIR / name
        if not candidate.exists():
            candidate = Path(name)
        if not candidate.exists():
            avail_names = [f.name for f in available]
            raise FileNotFoundError(
                f"Stinger '{name}' introuvable dans {STINGERS_DIR}.\n"
                f"Disponibles : {', '.join(avail_names) or '(aucun)'}"
            )
        return candidate
    if available:
        chosen = available[0]
        print(f"🎵 Stinger : {chosen.name}  (--stinger pour choisir parmi : {', '.join(f.name for f in available)})")
        return chosen
    synthetic = STINGERS_DIR / "stinger_synthetique.mp3"
    print("🎵 Génération du stinger synthétique...")
    expr = "0.55*sin(2*PI*(900-700*t)*t)*exp(-t*14)+0.3*sin(2*PI*(450-350*t)*t)*exp(-t*10)"
    proc = subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", f"aevalsrc={expr}:s=44100:d=0.5",
        "-af", "afade=t=out:st=0.3:d=0.2",
        "-c:a", "libmp3lame", "-q:a", "4",
        str(synthetic),
    ], capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg stinger error: {proc.stderr.decode()}")
    return synthetic


def generate_audio(
    segments: list[str],
    output_path: Path,
    stinger: Path,
    tones: list[str] | None = None,
    keep_segments: bool = False,
) -> tuple[Path, list[Path]]:
    print(f"🔊 Génération TTS : {len(segments)} segments...")
    tmp_dir = output_path.parent
    seg_paths: list[Path] = []

    if tones is None or len(tones) != len(segments):
        tones = ["neutral"] * len(segments)

    for i, (text, tone) in enumerate(zip(segments, tones)):
        seg_path = tmp_dir / f"_seg_{i:02d}.mp3"
        voice_id = TTS_VOICES.get(tone, TTS_VOICE_DEFAULT)
        word_count = len(text.split())
        if word_count > 300:
            print(f"   ⚠️  Segment {i+1} : {word_count} mots > 300 (Voxtral recommande < 300 mots par appel)")
        print(f"   [{i+1}/{len(segments)}] TTS segment ({tone} → {voice_id}, {word_count} mots)…")
        tts_call(normalize_for_tts(text), seg_path, voice_id=voice_id)
        padded = tmp_dir / f"_seg_{i:02d}_p.mp3"
        proc = subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(seg_path),
            "-af", "apad=pad_dur=0.15",
            "-c:a", "libmp3lame", "-q:a", "2",
            str(padded),
        ], capture_output=True)
        if proc.returncode == 0:
            seg_path.unlink()
            seg_path = padded
        seg_paths.append(seg_path)

    all_files: list[Path] = []
    for i, sp in enumerate(seg_paths):
        all_files.append(sp)
        if i < len(seg_paths) - 1:
            all_files.append(stinger)

    inputs = []
    for f in all_files:
        inputs += ["-i", str(f)]

    n = len(all_files)
    filter_str = "".join(f"[{i}:a]" for i in range(n)) + f"concat=n={n}:v=0:a=1[out]"

    print("   🔗 Assemblage FFmpeg…")
    proc = subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[out]",
        "-c:a", "libmp3lame", "-q:a", "2",
        str(output_path),
    ], capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg concat error: {proc.stderr.decode()}")

    if not keep_segments:
        for sp in seg_paths:
            sp.unlink(missing_ok=True)

    print(f"   Fichier final : {output_path} ({output_path.stat().st_size:,} bytes)")
    return output_path, seg_paths if keep_segments else []
