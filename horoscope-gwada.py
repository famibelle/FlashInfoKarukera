#!/usr/bin/env python3
"""
Horoscope Karukera — segment horoscope quotidien autonome
Fetch API → Rédaction Maryse (Mistral) → TTS (Voxtral) → Vidéo TikTok → Telegram → Buzzsprout
"""

import os
import re as _re
import sys
import json
import time
import random
import base64
import argparse
import subprocess
import urllib.request
import urllib.parse
import urllib.error
from datetime import date as Date, datetime as DateTime
from pathlib import Path

# ── Chargement du .env ────────────────────────────────────────────────────────

def _load_env(env_path: Path) -> None:
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())

_load_env(Path(__file__).parent / ".env")

# ── Config ────────────────────────────────────────────────────────────────────

MISTRAL_API_KEY     = os.environ["MISTRAL_API_KEY"]
TELEGRAM_BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID    = os.environ["TELEGRAM_CHAT_ID"]

BUZZSPROUT_API_TOKEN  = os.environ.get("BUZZSPROUT_API_TOKEN", "")
BUZZSPROUT_PODCAST_ID = os.environ.get("BUZZSPROUT_PODCAST_ID", "")

TTS_MODEL           = "voxtral-mini-tts-2603"
STT_MODEL           = "voxtral-mini-latest"
TTS_VOICE_DEFAULT   = "fr_marie_neutral"
TTS_VOICES = {
    "neutral":  "fr_marie_neutral",
    "happy":    "fr_marie_happy",
    "excited":  "fr_marie_excited",
    "sad":      "fr_marie_sad",
    "angry":    "fr_marie_angry",
    "curious":  "fr_marie_curious",
}

MISTRAL_CHAT_MODEL = "mistral-large-latest"
MISTRAL_CHAT_URL   = "https://api.mistral.ai/v1/chat/completions"

OUTPUT_DIR   = Path("/tmp")
STINGERS_DIR = Path(__file__).parent / "Stingers"
PROMPTS_DIR  = Path(__file__).parent / "prompts"
DATA_DIR     = Path(__file__).parent / "data"
USED_FLORA_PATH = DATA_DIR / "used_flora.json"
FLORA_MEMORY_DAYS = 7  # fenêtre glissante d'anti-répétition
MEDIA_DIR    = Path(__file__).parent / "Media"

HOROSCOPE_API = "https://freehoroscopeapi.com/api/v1/get-horoscope/daily"
WEATHER_LAT   = 16.17
WEATHER_LON   = -61.58
WEATHER_API   = "https://api.open-meteo.com/v1/forecast"

TELEGRAM_VIDEO_MAX_MB = 49

TIKTOK_COLORS = {
    "neutral":  "#FFFFFF",
    "happy":    "#FFD700",
    "excited":  "#FF4500",
    "sad":      "#6495ED",
    "angry":    "#FF0000",
    "curious":  "#00CED1",
}
INTERSTITIAL_STYLES: dict[str, tuple[str, str]] = {
    "horoscope": ("HOROSCOPE", "#6C3483"),
}
SUBTITLE_FONTSIZE       = 130
TRIM_SILENCE            = False
INTERSTITIAL_CTA        = "Si j'ai mal prononcé certains mots, dites-le moi en commentaire"
INTERSTITIAL_CAT_FONTSIZE = 170
INTERSTITIAL_HT_FONTSIZE  = 110
_FONT_BOLD    = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BUZZSPROUT_TAGS = "Guadeloupe, actualité, flash info, Antilles, Caraïbes, France-Antilles, info locale"

# ── Imports données locales ───────────────────────────────────────────────────

from data.marroniers import get_marroniers_du_jour as _get_marroniers_du_jour
from data.tts_normalize import (
    PRONONCIATIONS_LOCALES as _PRONONCIATIONS_LOCALES,
    SIGLES_MOT as _SIGLES_MOT,
    ABBREVS as _ABBREVS,
)
from data.weather_codes import WMO_CODES as _WMO

# ── Date & heure Paris ────────────────────────────────────────────────────────

_FR_MONTHS = {
    "January": "janvier", "February": "février", "March": "mars",
    "April": "avril", "May": "mai", "June": "juin",
    "July": "juillet", "August": "août", "September": "septembre",
    "October": "octobre", "November": "novembre", "December": "décembre",
}
_FR_DAYS = {
    "Monday": "lundi", "Tuesday": "mardi", "Wednesday": "mercredi",
    "Thursday": "jeudi", "Friday": "vendredi", "Saturday": "samedi", "Sunday": "dimanche",
}


def _now_paris_str(fmt: str) -> str:
    return subprocess.check_output(
        ["date", f"+{fmt}"],
        env={**os.environ, "TZ": "Europe/Paris"},
    ).decode().strip()


def _date_fr(d: Date) -> str:
    s = d.strftime("%A %-d %B %Y")
    for en, fr in {**_FR_DAYS, **_FR_MONTHS}.items():
        s = s.replace(en, fr)
    return s


def _moment_du_jour() -> str:
    h = DateTime.now().hour
    if 5 <= h < 12:  return "ce matin"
    if 12 <= h < 18: return "cet après-midi"
    if 18 <= h < 22: return "ce soir"
    return "cette nuit"


def _load_prompt(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8").rstrip()

# ── Météo (contexte local) ────────────────────────────────────────────────────

def _rain_label(mm: float) -> str:
    if mm == 0: return "pas de pluie"
    if mm < 5:  return "légère pluie"
    if mm < 20: return "pluie modérée"
    return "fortes pluies"


def _wind_label(kmh: float) -> str:
    if kmh < 20: return "vent faible"
    if kmh < 40: return "vent modéré"
    if kmh < 60: return "vent fort"
    return "vent violent"


def fetch_weather(target_date: Date) -> str:
    params = urllib.parse.urlencode({
        "latitude": WEATHER_LAT, "longitude": WEATHER_LON,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode",
        "timezone": "America/Guadeloupe",
        "start_date": target_date.isoformat(),
        "end_date": target_date.isoformat(),
    })
    with urllib.request.urlopen(f"{WEATHER_API}?{params}", timeout=15) as r:
        data = json.loads(r.read())
    d = data.get("daily", {})
    if not d.get("time"):
        return ""
    tmax = d["temperature_2m_max"][0]
    tmin = d["temperature_2m_min"][0]
    rain = d["precipitation_sum"][0]
    wind = d["windspeed_10m_max"][0]
    code = int(d["weathercode"][0])
    desc = _WMO.get(code, {}).get("day", {}).get("description", "")
    return (
        f"{desc}, {tmin:.0f}–{tmax:.0f}°C, "
        f"{_rain_label(rain)}, {_wind_label(wind)} ({wind:.0f} km/h)"
    )

# ── Signes astrologiques ──────────────────────────────────────────────────────

_SIGNS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]
_SIGN_FR = {
    "aries": "Bélier", "taurus": "Taureau", "gemini": "Gémeaux",
    "cancer": "Cancer", "leo": "Lion", "virgo": "Vierge",
    "libra": "Balance", "scorpio": "Scorpion", "sagittarius": "Sagittaire",
    "capricorn": "Capricorne", "aquarius": "Verseau", "pisces": "Poissons",
}
_SIGN_FR_TO_EN = {v.lower(): k for k, v in _SIGN_FR.items()}


def _resolve_sign(name: str) -> str | None:
    key = name.strip().lower()
    if key in _SIGNS:
        return key
    return _SIGN_FR_TO_EN.get(key)


def _sign_for_date(d: Date) -> str:
    m, day = d.month, d.day
    if (m == 3 and day >= 21) or (m == 4 and day <= 19): return "aries"
    if (m == 4 and day >= 20) or (m == 5 and day <= 20): return "taurus"
    if (m == 5 and day >= 21) or (m == 6 and day <= 20): return "gemini"
    if (m == 6 and day >= 21) or (m == 7 and day <= 22): return "cancer"
    if (m == 7 and day >= 23) or (m == 8 and day <= 22): return "leo"
    if (m == 8 and day >= 23) or (m == 9 and day <= 22): return "virgo"
    if (m == 9 and day >= 23) or (m == 10 and day <= 22): return "libra"
    if (m == 10 and day >= 23) or (m == 11 and day <= 21): return "scorpio"
    if (m == 11 and day >= 22) or (m == 12 and day <= 21): return "sagittarius"
    if (m == 12 and day >= 22) or (m == 1 and day <= 19): return "capricorn"
    if (m == 1 and day >= 20) or (m == 2 and day <= 18): return "aquarius"
    return "pisces"


def fetch_horoscope(
    n_signs: int = 7,
    include_signs: "list[str] | None" = None,
) -> "list[tuple[str, str, str]] | None":
    """Retourne [(sign_en, sign_fr, raw_text), …] ou None si l'API est indisponible."""
    forced = list(dict.fromkeys(include_signs or []))
    pool = [s for s in _SIGNS if s not in forced]
    n_random = max(0, n_signs - len(forced))
    signs = forced + random.sample(pool, min(n_random, len(pool)))
    print(f"🔮  Collecte horoscope ({len(signs)} signe{'s' if len(signs) > 1 else ''}" +
          (f", dont {', '.join(_SIGN_FR[s] for s in forced)} imposé{'s' if len(forced) > 1 else ''}" if forced else "") + ")...")
    entries = []
    for sign in signs:
        try:
            qs = urllib.parse.urlencode({"sign": sign})
            req = urllib.request.Request(
                f"{HOROSCOPE_API}?{qs}",
                headers={"User-Agent": "Mozilla/5.0 (compatible; FlashInfoKarukera/1.0)"},
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
            text = (
                data.get("horoscope")
                or data.get("data", {}).get("horoscope", "")
                or data.get("description", "")
            )
            if text:
                entries.append((sign, _SIGN_FR[sign], text))
                print(f"   {_SIGN_FR[sign]} ✅")
        except Exception as e:
            print(f"   ⚠️  Horoscope {sign} : {e}")
    if not entries:
        print("   ⚠️  Horoscope indisponible — rubrique omise.")
        return None
    return entries

# ── Mistral ───────────────────────────────────────────────────────────────────

def call_mistral(
    system: str,
    user: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 1500,
    json_mode: bool = False,
    timeout: int = 60,
    _retries: int = 4,
) -> str:
    payload: dict = {
        "model": MISTRAL_CHAT_MODEL,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
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
            if e.code == 429 and attempt < _retries:
                wait = 10 * 2 ** attempt
                print(f"   ⏳ Mistral 429 — attente {wait}s (tentative {attempt + 1}/{_retries})…")
                time.sleep(wait)
            else:
                raise


HOROSCOPE_TEMPLATE = _load_prompt("horoscope.md")

# Noms-clés de la flore et faune guadeloupéennes pour détecter les répétitions inter-signes
_FLORA_KEYWORDS = [
    # Flore
    "malomé", "zanno", "jasmin de nuit", "flanbwayan", "gommier", "palétuwyé",
    "manglier", "kalbas", "calebasse", "patchouli", "roucou", "woucou",
    "figuiye", "figuier maudit", "balizié", "piman", "marakoudja",
    "fruit de la passion", "manyòk", "manioc", "chadon béni", "brizée",
    "zeb a pik", "mimosa", "alowes", "aloès", "zeb a femme", "dachine",
    "vaniy", "vanille", "mango", "mangue", "gombo", "cacao",
    "grenad", "grenade", "kanaié", "canne à sucre", "jenjanm", "gingembre",
    "zanmann", "amandier", "érytrin", "bwa flotant", "ibiskis", "oseille pays",
    "kokoye", "coco", "gwayav", "goyave", "sapotiy", "kannel", "cannelle",
    "antwiriyòm", "anthurium", "pòm malaka", "manguié", "friyapen", "fruit à pain",
    # Faune
    "fwou-fwou", "kolibri", "colibri", "soukouyan", "sucrier",
    "pélikan", "frégat", "frégate", "pic de gwadloup", "yòlò", "siffleur",
    "jakòt", "perroquet", "urakan", "ouragan",
    "igwann", "iguane", "zandoli", "anoli", "mabouya", "koures", "couresse",
    "gouti", "agouti", "guimbo", "chauve-souris", "balèn", "baleine",
    "manman dlo", "lamantin", "raton laveur",
    "tòti", "tortue",
    "grenn-bwa", "hylode", "krapo", "crapaud",
    "krab tè", "crabe", "touloulou", "wasou", "ouassou", "langous", "langouste",
    "myèl", "abeille", "foumi", "fourmi", "kabribo", "grillon", "cabrit-bois",
    "luciole", "ti flambeau", "papillon nwè", "papillon noir", "papillon transparent",
    "myg", "mygale", "ravèt", "cafard",
    "poul nwè", "poule noire", "kab nwè", "cabri noir", "chatou", "chatrou", "poulpe",
]


def _extract_used_flora(text: str) -> list[str]:
    text_lower = text.lower()
    return [kw for kw in _FLORA_KEYWORDS if kw in text_lower]


def _load_recent_flora(window_days: int = FLORA_MEMORY_DAYS, exclude_date: "Date | None" = None) -> list[str]:
    """Retourne la liste dédoublonnée des éléments de flore utilisés sur les `window_days` derniers jours."""
    if not USED_FLORA_PATH.exists():
        return []
    try:
        data: dict = json.loads(USED_FLORA_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    cutoff = Date.today().toordinal() - window_days
    recent: list[str] = []
    for date_str, flora in data.items():
        try:
            d = Date.fromisoformat(date_str)
        except ValueError:
            continue
        if d.toordinal() >= cutoff and d != exclude_date:
            recent.extend(flora)
    return list(dict.fromkeys(recent))


def _save_used_flora(target_date: Date, flora: list[str]) -> None:
    """Ajoute ou met à jour l'entrée du jour dans used_flora.json (fusion avec l'existant)."""
    data: dict = {}
    if USED_FLORA_PATH.exists():
        try:
            data = json.loads(USED_FLORA_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing = data.get(target_date.isoformat(), [])
    data[target_date.isoformat()] = list(dict.fromkeys(existing + flora))
    # Purge des entrées trop anciennes (> 2 * window pour ne pas grossir indéfiniment)
    cutoff = Date.today().toordinal() - FLORA_MEMORY_DAYS * 2
    data = {k: v for k, v in data.items() if Date.fromisoformat(k).toordinal() >= cutoff}
    USED_FLORA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾  Anti-répétition flore : {len(flora)} éléments sauvegardés ({USED_FLORA_PATH.name})")
LIEUX_SPIRITUELS   = (
    "\n\n" + _load_prompt("lieux_spirituels.md") +
    "\n\n" + _load_prompt("flore_guadeloupe.md") +
    "\n\n" + _load_prompt("faune_guadeloupe.md")
)

def _strip_markdown(text: str) -> str:
    text = _re.sub(r"\*+([^*]+)\*+", r"\1", text)
    text = _re.sub(r"\[.*?\]", "", text)
    text = _re.sub(r"^\s*[-#>]+\s*", "", text, flags=_re.MULTILINE)
    text = _re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

# ── TTS normalisation ─────────────────────────────────────────────────────────

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
    return _re.sub(r"\b(\d+)(?:e|ème|eme)\b", lambda m: _ordinal_fr(m.group(1)), text)


def _norm_currencies(text: str) -> str:
    text = _re.sub(r"(\d[\d\s]*(?:[.,]\d+)?)\s*€", lambda m: f"{_num_fr(m.group(1).strip())} euros", text)
    text = _re.sub(r"(\d[\d\s]*(?:[.,]\d+)?)\s*\$", lambda m: f"{_num_fr(m.group(1).strip())} dollars", text)
    return text


def _norm_scores(text: str) -> str:
    return _re.sub(r"\b(\d+)\s*[-–]\s*(\d+)\b", lambda m: f"{_num_fr(m.group(1))} à {_num_fr(m.group(2))}", text)


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
    return _re.sub(r"\b(\d{1,2}):(\d{2})\b", lambda m: f"{_num_fr(m.group(1))} heures {_num_fr(m.group(2))}", text)


def _norm_units(text: str) -> str:
    for pattern, repl in _UNIT_PATTERNS:
        text = _re.sub(pattern, repl, text)
    return text


def _norm_plain_numbers(text: str) -> str:
    return _re.sub(r"\b(\d[\d\s]*(?:[.,]\d+)?)\b", lambda m: _num_fr(m.group(1).strip()), text)


def _norm_acronyms(text: str) -> str:
    # _SIGLES_MOT = set de sigles prononcés comme des mots — on laisse tel quel
    # Les autres acronymes tout-majuscules sont épelés lettre par lettre
    def _spell(m):
        word = m.group(0)
        if word in _SIGLES_MOT:
            return word
        return " ".join(word)
    return _re.sub(r"\b[A-Z]{2,}\b", _spell, text)


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
    return _re.sub(r"\bMe\b(?=\s+[A-ZÀÂÉÈÊËÎÏÔÙÛÜ])", "Maître", text)


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


def _normalize_for_tts(text: str) -> str:
    for step in _NORMALIZATION_PIPELINE:
        text = step(text)
    return text.strip()

# ── TTS ───────────────────────────────────────────────────────────────────────

def _tts_call(text: str, output_path: Path, voice_id: str = TTS_VOICE_DEFAULT) -> None:
    if not text.strip():
        raise RuntimeError("_tts_call: texte vide, rien à synthétiser")
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
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            response = json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"TTS HTTP {e.code} ({e.reason}): {body}") from None
    if "audio_data" not in response:
        raise RuntimeError(f"TTS error: {response}")
    output_path.write_bytes(base64.b64decode(response["audio_data"]))


def resolve_stinger(name: str | None) -> Path:
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
        print(f"🎵 Stinger : {chosen.name}")
        return chosen
    synthetic = STINGERS_DIR / "stinger_synthetique.mp3"
    print("🎵 Génération du stinger goutte d'eau (synthétique)...")
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

# ── STT (transcription pour TikTok) ──────────────────────────────────────────

def _mistral_stt(audio_path: Path, word_timestamps: bool = False) -> dict:
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
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
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


def transcribe_with_words(audio_path: Path) -> list[dict]:
    segments = _mistral_stt(audio_path, word_timestamps=True).get("segments", [])
    return [
        {"word": s["text"].strip(), "start": s["start"], "end": s["end"]}
        for s in segments
        if s.get("text", "").strip()
    ]

# ── Vidéo TikTok ──────────────────────────────────────────────────────────────

def _ass_time(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"


def _ass_color(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"&H00{b:02X}{g:02X}{r:02X}&"


def _make_ass(words: list[dict], tone: str) -> str:
    tone_col = _ass_color(TIKTOK_COLORS.get(tone, "#FFFFFF"))
    dim_col  = "&H80FFFFFF&"
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 1\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,Arial,{round(SUBTITLE_FONTSIZE * 0.74)},&H00FFFFFF,&H00FFFFFF,&H00000000,"
        "&HA0000000,0,0,0,0,100,100,0,0,1,5,2,5,80,80,0,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    events = []
    for i, word in enumerate(words):
        start = word["start"]
        end   = max(word["end"], start + 0.05)
        parts = []
        fs_curr = SUBTITLE_FONTSIZE
        fs_adj  = round(SUBTITLE_FONTSIZE * 0.74)
        if i > 0:
            parts.append(f"{{\\c{dim_col}\\fs{fs_adj}}}{words[i - 1]['word']}")
        parts.append(f"{{\\c{tone_col}\\fs{fs_curr}\\b1}}{word['word']}{{\\b0}}")
        if i < len(words) - 1:
            parts.append(f"{{\\c{dim_col}\\fs{fs_adj}}}{words[i + 1]['word']}")
        events.append(
            f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},"
            f"Default,,0,0,0,,{{\\an5\\pos(540,1210)}}{' '.join(parts)}"
        )
    return header + "\n".join(events) + "\n"


def _trim_silence(seg_path: Path) -> Path:
    trimmed = seg_path.with_suffix(".trimmed.mp3")
    proc = subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(seg_path),
        "-af", "silenceremove=stop_periods=-1:stop_duration=0.2:stop_threshold=-45dB",
        "-c:a", "libmp3lame", "-q:a", "2",
        str(trimmed),
    ], capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg trim error: {proc.stderr.decode()}")
    return trimmed


def _stinger_duration(stinger: Path) -> float:
    proc = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(stinger),
    ], capture_output=True, text=True)
    return float(proc.stdout.strip())


def _tiktok_segment_video(seg_path: Path, ass_path: Path, tone: str, output_path: Path) -> None:
    color_hex = TIKTOK_COLORS.get(tone, "#FFFFFF").lstrip("#")
    audio_path = _trim_silence(seg_path) if TRIM_SILENCE else seg_path
    filter_complex = (
        f"color=c=black:s=1080x1920:r=30[bg];"
        f"[0:a]showwaves=s=1080x500:mode=cline:colors=0x{color_hex}:scale=sqrt:rate=30[waves];"
        f"[bg][waves]overlay=0:0[v];"
        f"[v]ass={ass_path}[vout]"
    )
    proc = subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(audio_path),
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_path),
    ], capture_output=True)
    if TRIM_SILENCE:
        audio_path.unlink(missing_ok=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg tiktok error: {proc.stderr.decode()}")


def _make_cta_interstitial(output_path: Path, stinger: Path) -> Path:
    cta_text = INTERSTITIAL_CTA.rstrip()
    duration = _stinger_duration(stinger)
    words = cta_text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= 20:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    tmp = output_path.parent
    line_files = []
    for i, line in enumerate(lines):
        f = tmp / f"cta_line{i}.txt"
        f.write_text(line, encoding="utf-8")
        line_files.append(f)
    wm_file = tmp / "cta_watermark.txt"
    wm_file.write_text("Flash Info Karukera par Botiran", encoding="utf-8")
    fontsize, line_h = 62, 80
    block_h = len(lines) * line_h
    y_start = (1920 - block_h) // 2 - 40
    filter_parts = [
        f"color=c=black:s=1080x1920:r=30:d={duration}",
        f"drawbox=x=0:y=0:w=1080:h=1920:color=0x1A1A2E@1:t=fill",
    ]
    for i, f in enumerate(line_files):
        y = y_start + i * line_h
        filter_parts.append(
            f"drawtext=textfile={f}:fontsize={fontsize}:fontcolor=white:"
            f"fontfile={_FONT_BOLD}:x=(w-tw)/2:y={y}:"
            f"shadowcolor=black@0.6:shadowx=2:shadowy=2"
        )
    y_wm = y_start + len(lines) * line_h + 40
    filter_parts.append(
        f"drawtext=textfile={wm_file}:fontsize=36:fontcolor=white@0.4:"
        f"fontfile={_FONT_REGULAR}:x=(w-tw)/2:y={y_wm}"
    )
    proc = subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", ",".join(filter_parts),
        "-i", str(stinger),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_path),
    ], capture_output=True)
    for f in line_files:
        f.unlink(missing_ok=True)
    wm_file.unlink(missing_ok=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg CTA error: {proc.stderr.decode()}")
    return output_path


def _assemble_audio(seg_paths: list[Path], stinger: Path, output_path: Path) -> None:
    """Concatène des segments MP3 avec le stinger entre chaque → output_path."""
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
    print("   🔗 Assemblage audio FFmpeg…")
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


def _make_horoscope_interstitial(output_path: Path, stinger: Path, sign_fr: str) -> Path:
    """Écran titre pour un signe : HOROSCOPE + nom du signe."""
    label, color = INTERSTITIAL_STYLES["horoscope"]
    color_hex = color.lstrip("#")
    duration = _stinger_duration(stinger)
    cat_fontsize = INTERSTITIAL_CAT_FONTSIZE
    cat_line_h   = round(cat_fontsize * 1.1)
    sign_fontsize = 90
    sign_line_h   = round(sign_fontsize * 1.3)
    gap      = 50
    block_h  = cat_line_h + gap + sign_line_h
    cat_y    = (1920 - block_h) // 2
    sign_y   = cat_y + cat_line_h + gap
    wm_y     = sign_y + sign_line_h + 40
    sign_file = output_path.parent / f"inter_sign_{output_path.stem}.txt"
    sign_file.write_text(sign_fr, encoding="utf-8")
    filter_parts = [
        f"color=c=black:s=1080x1920:r=30:d={duration}",
        f"drawtext=text='{label}':"
        f"fontsize={cat_fontsize}:fontcolor=0x{color_hex}:fontfile={_FONT_BOLD}:"
        f"x=(w-tw)/2:y={cat_y}:"
        f"shadowcolor=black@0.6:shadowx=3:shadowy=3",
        f"drawtext=textfile={sign_file}:"
        f"fontsize={sign_fontsize}:fontcolor=white:fontfile={_FONT_BOLD}:"
        f"x=(w-tw)/2:y={sign_y}:"
        f"shadowcolor=black@0.5:shadowx=2:shadowy=2",
        f"drawtext=text='Flash Info Karukera par @Botiran':"
        f"fontsize=38:fontcolor=white@0.5:fontfile={_FONT_REGULAR}:"
        f"x=(w-tw)/2:y={wm_y}",
    ]
    proc = subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", ",".join(filter_parts),
        "-i", str(stinger),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_path),
    ], capture_output=True)
    sign_file.unlink(missing_ok=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg interstitiel error: {proc.stderr.decode()}")
    return output_path


def _make_segment_video(audio_path: Path, output_path: Path, output_dir: Path, tone: str, label: str) -> "Path | None":
    """STT + ASS + waveform video pour un segment audio. Retourne le chemin vidéo ou None."""
    print(f"   {label} — STT timestamps…")
    words = transcribe_with_words(audio_path)
    if not words:
        print(f"   ⚠️  STT sans mots pour {label} — segment ignoré")
        return None
    ass_path = output_path.with_suffix(".ass")
    ass_path.write_text(_make_ass(words, tone), encoding="utf-8")
    print(f"   {label} — FFmpeg → {output_path.name}…")
    _tiktok_segment_video(audio_path, ass_path, tone, output_path)
    print(f"   ✅ {label} ({output_path.stat().st_size:,} bytes)")
    return output_path


def generate_tiktok(
    intro_path: Path,
    seg_paths: list[Path],
    outro_path: Path,
    signs_fr: list[str],
    output_dir: Path,
    stinger: Path,
) -> "Path | None":
    """Génère : intro → (inter_signe + signe) × N → outro → CTA puis concatène."""
    output_dir.mkdir(parents=True, exist_ok=True)
    n_signs = len(seg_paths)
    print(f"🎬 Génération vidéos TikTok (intro + {n_signs} signes + outro) → {output_dir}")

    tone = "curious"
    all_parts: list[Path] = []

    # Intro
    intro_video = _make_segment_video(
        intro_path, output_dir / "seg_intro.mp4", output_dir, tone, "INTRO"
    )
    if intro_video:
        all_parts.append(intro_video)

    # Signes : interstitiel + vidéo
    for i, (seg_path, sign_fr) in enumerate(zip(seg_paths, signs_fr)):
        inter_path = output_dir / f"inter_{i:02d}.mp4"
        _make_horoscope_interstitial(inter_path, stinger, sign_fr)

        seg_video = _make_segment_video(
            seg_path, output_dir / f"seg_{i:02d}.mp4", output_dir, tone,
            f"[{i + 1}/{n_signs}] {sign_fr}"
        )
        if seg_video:
            all_parts.append(inter_path)
            all_parts.append(seg_video)

    if not all_parts:
        return None

    # Outro
    outro_video = _make_segment_video(
        outro_path, output_dir / "seg_outro.mp4", output_dir, tone, "OUTRO"
    )
    if outro_video:
        all_parts.append(outro_video)

    # CTA
    cta_path = output_dir / "inter_cta.mp4"
    _make_cta_interstitial(cta_path, stinger)
    all_parts.append(cta_path)

    # Concaténation finale
    concat_path = output_dir / "horoscope_full.mp4"
    inputs_args = []
    for p in all_parts:
        inputs_args += ["-i", str(p)]
    n = len(all_parts)
    filter_str = "".join(f"[{i}:v][{i}:a]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vout][aout]"
    proc = subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        *inputs_args,
        "-filter_complex", filter_str,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        str(concat_path),
    ], capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg concat error: {proc.stderr.decode()}")

    print(f"   ✅ {concat_path.name} ({concat_path.stat().st_size:,} bytes)")
    return concat_path

# ── Telegram ──────────────────────────────────────────────────────────────────

def send_telegram_video(
    video_path: Path,
    caption: str,
    timeout: int = 180,
) -> None:
    size_mb = video_path.stat().st_size / 1_048_576
    print(f"   Upload Telegram : {video_path.name} ({size_mb:.1f} Mo)…")
    if size_mb > TELEGRAM_VIDEO_MAX_MB:
        print(f"   ⚠️  Vidéo trop volumineuse ({size_mb:.1f} Mo > {TELEGRAM_VIDEO_MAX_MB} Mo) — upload ignoré.")
        return

    boundary = "----FlashInfoBoundary"

    def field(name, value):
        return (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        ).encode()

    def file_field(name, filename, content_type, data):
        return (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode() + data + b"\r\n"

    body = field("chat_id", TELEGRAM_CHAT_ID) + field("caption", caption)
    body += file_field("video", video_path.name, "video/mp4", video_path.read_bytes())
    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                result = json.loads(r.read())
            if not result.get("ok"):
                raise RuntimeError(f"Telegram video error: {result}")
            print(f"   {video_path.name} envoyé ✅")
            return
        except (urllib.error.URLError, ConnectionResetError, TimeoutError) as exc:
            if attempt < 3:
                wait = 10 * attempt
                print(f"   ⚠️  Tentative {attempt}/3 échouée ({exc}) — nouvel essai dans {wait}s…")
                time.sleep(wait)
            else:
                raise

def send_telegram_audio(
    audio_path: Path,
    caption: str,
    timeout: int = 120,
) -> None:
    size_mb = audio_path.stat().st_size / 1_048_576
    print(f"   Upload Telegram audio : {audio_path.name} ({size_mb:.1f} Mo)…")

    boundary = "----FlashInfoBoundary"

    def field(name, value):
        return (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        ).encode()

    def file_field(name, filename, content_type, data):
        return (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode() + data + b"\r\n"

    body = field("chat_id", TELEGRAM_CHAT_ID) + field("caption", caption)
    body += file_field("audio", audio_path.name, "audio/mpeg", audio_path.read_bytes())
    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendAudio",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                result = json.loads(r.read())
            if not result.get("ok"):
                raise RuntimeError(f"Telegram audio error: {result}")
            print(f"   {audio_path.name} envoyé ✅")
            return
        except (urllib.error.URLError, ConnectionResetError, TimeoutError) as exc:
            if attempt < 3:
                wait = 10 * attempt
                print(f"   ⚠️  Tentative {attempt}/3 échouée ({exc}) — nouvel essai dans {wait}s…")
                time.sleep(wait)
            else:
                raise


# ── Buzzsprout ────────────────────────────────────────────────────────────────

def publish_buzzsprout(audio_path: Path, title: str, description: str, tags: str) -> str:
    print(f"🎙️  Publication Buzzsprout (podcast {BUZZSPROUT_PODCAST_ID})...")
    cmd = [
        "curl", "-s",
        "-H", f"Authorization: Token token={BUZZSPROUT_API_TOKEN}",
        "-F", f"title={title}",
        "-F", f"description={description}",
        "-F", f"tags={tags}",
        "-F", "explicit=false",
        "-F", "private=false",
        "-F", f"audio_file=@{audio_path};type=audio/mpeg",
        f"https://www.buzzsprout.com/api/{BUZZSPROUT_PODCAST_ID}/episodes.json",
    ]
    proc = subprocess.run(cmd, capture_output=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError(f"curl error: {proc.stderr.decode()}")
    result = json.loads(proc.stdout)
    episode_url = result.get("url", "")
    episode_id  = result.get("id", "")
    print(f"   Épisode publié ✅  id={episode_id}  url={episode_url}")
    return episode_url

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Horoscope Karukera — segment horoscope quotidien\n"
            "Workflow : fetch API → Maryse (Mistral Large) → TTS (Voxtral)\n"
            "           → Vidéo TikTok → Telegram → Buzzsprout"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--date", metavar="YYYY-MM-DD",
        help="Date de l'horoscope (défaut : aujourd'hui). Exemple : --date 2026-04-18",
    )
    parser.add_argument(
        "--horoscope-signs", type=int, default=7, metavar="N",
        help="Nombre de signes astrologiques (défaut : 7).",
    )
    parser.add_argument(
        "--horoscope-include", nargs="+", action="append", default=None, metavar="SIGNE",
        help=(
            "Inclure un ou plusieurs signes de force (français ou anglais). "
            "Exemple : --horoscope-include gemini capricorn. Répétable. "
            "Signes disponibles : "
            + ", ".join(f"{fr} ({en})" for en, fr in _SIGN_FR.items())
            + "."
        ),
    )
    parser.add_argument(
        "--tiktok", action="store_true",
        help="Génère une vidéo TikTok 1080×1920 avec karaoke et l'envoie sur Telegram.",
    )
    parser.add_argument(
        "--telegram", action="store_true",
        help="Envoie l'audio MP3 final sur Telegram (indépendamment de --tiktok).",
    )
    parser.add_argument(
        "--stinger", metavar="FICHIER",
        help=f"Nom du stinger dans {STINGERS_DIR} (optionnel — premier fichier utilisé si omis).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Génère l'audio et la vidéo mais n'envoie pas sur Buzzsprout.",
    )
    parser.add_argument(
        "--no-send", action="store_true",
        help="Génère l'audio (et la vidéo si --tiktok) sans publier sur Buzzsprout.",
    )
    parser.add_argument(
        "--output", type=Path, metavar="CHEMIN",
        help="Chemin du fichier MP3 de sortie (défaut : horoscope-YYYYMMDD.mp3 dans /tmp).",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Affiche le texte brut de l'API et le texte rédigé par Maryse.",
    )
    args = parser.parse_args()

    gen_date = Date.fromisoformat(args.date) if args.date else Date.today()
    output_path = (
        Path(args.output) if args.output
        else OUTPUT_DIR / f"horoscope-{gen_date.strftime('%Y%m%d')}.mp3"
    )

    # Résolution des signes forcés
    inc: list[str] = []
    for group in (args.horoscope_include or []):
        for name in group:
            resolved = _resolve_sign(name)
            if resolved:
                if resolved not in inc:
                    inc.append(resolved)
            else:
                hint = f" (pour limiter le nombre de signes, utilisez --horoscope-signs {name})" if name.isdigit() else ""
                print(f"⚠️  Signe inconnu ignoré : '{name}' — utilisez le nom anglais ou français.{hint}", file=sys.stderr)

    date_sign = _sign_for_date(gen_date)
    if not inc:
        inc = [date_sign]
        print(f"📅 Signe déduit de la date ({gen_date}) : {_SIGN_FR[date_sign]}")

    n_signs = max(args.horoscope_signs, len(inc))

    # Fetch horoscope
    horoscope_entries = fetch_horoscope(n_signs=n_signs, include_signs=inc or None)
    if not horoscope_entries:
        print("❌ Impossible de récupérer l'horoscope.", file=sys.stderr)
        sys.exit(1)
    signs_fr = [e[1] for e in horoscope_entries]
    n_signs  = len(horoscope_entries)
    print(f"🔮 Signes retenus : {', '.join(signs_fr)}")

    if args.verbose:
        print("\n══════════════════════════════════════════════════════════")
        print("  VERBOSE — HOROSCOPE BRUT (fetch_horoscope)")
        print("══════════════════════════════════════════════════════════")
        for sign_en, sign_fr, raw in horoscope_entries:
            print(f"  {sign_fr} : {raw}")
        print("══════════════════════════════════════════════════════════\n")

    # Contexte local (météo + marroniers) — partagé par tous les signes
    weather_summary = None
    try:
        weather_summary = fetch_weather(gen_date)
    except Exception:
        pass
    marroniers = _get_marroniers_du_jour(gen_date)
    contexte_lines = []
    if weather_summary:
        contexte_lines.append(f"Météo du jour à Pointe-à-Pitre : {weather_summary}")
    if marroniers:
        contexte_lines.append(
            "Événements du jour en Guadeloupe : " +
            " ; ".join(f"{m.evenement} ({m.lieu})" for m in marroniers)
        )
    contexte_local = (
        "\n\nCONTEXTE LOCAL DU JOUR :\n" + "\n".join(contexte_lines)
        if contexte_lines else ""
    )

    # Prompts de base
    date_label   = _date_fr(gen_date)
    moment_label = _moment_du_jour()
    maryse_base = (
        _load_prompt("maryse_ame.md") + "\n\n"
        "Tu rédiges UNIQUEMENT le segment horoscope — pas de météo, pas d'actualités. "
        "Juste la lecture de l'horoscope dans ta voix.\n"
    )

    seg_dir = output_path.parent / f"horoscope-segs-{gen_date.strftime('%Y%m%d')}"
    seg_dir.mkdir(parents=True, exist_ok=True)

    # ── Intro dédiée ──────────────────────────────────────────────────────────
    print("✍️  Rédaction intro (Mistral Large)…")
    intro_system = (
        maryse_base +
        "Tu rédiges UNIQUEMENT l'introduction de l'horoscope du jour — "
        "pas de lecture de signe. Deux à trois phrases dans ta voix."
    )
    intro_user = (
        f"DATE : {date_label}\n"
        f"SIGNES DU JOUR : {', '.join(signs_fr)}\n\n"
        f"Commence OBLIGATOIREMENT par : 'Nous sommes le {date_label} et ' "
        "puis enchaîne avec ta formule ancestrale pour annoncer les signes retenus. "
        "Deux à trois phrases, pas plus."
    )
    intro_text = _strip_markdown(
        call_mistral(intro_system, intro_user, temperature=0.75, max_tokens=120)
    )
    if args.verbose:
        print(f"\n── INTRO ────────────────────────────────────────────────")
        print(intro_text)
        print("─────────────────────────────────────────────────────────\n")
    intro_path = seg_dir / "seg_intro.mp3"
    print(f"🔊 TTS intro → {intro_path.name}")
    _tts_call(_normalize_for_tts(intro_text), intro_path, TTS_VOICES["curious"])

    # ── Boucle par signe : Mistral + TTS ─────────────────────────────────────
    seg_paths: list[Path] = []

    # Anti-répétition inter-jours
    recent_flora = _load_recent_flora()
    if recent_flora:
        print(f"🌿 Flore récente ({FLORA_MEMORY_DAYS}j) exclue : {', '.join(recent_flora)}")
    used_flora: list[str] = list(recent_flora)

    sign_system = (
        maryse_base +
        "Tu rédiges UNIQUEMENT la lecture d'un signe astrologique dans ta voix — "
        "pas d'intro, pas de clôture, pas de formule de date. "
        "Juste ce signe, dans ta voix.\n"
    )

    for i, (sign_en, sign_fr, raw_text) in enumerate(horoscope_entries):
        avoid_instruction = (
            f"INTERDIT pour ce signe — ces éléments ont déjà été utilisés dans "
            f"cet horoscope, n'en reprends aucun : {', '.join(used_flora)}.\n"
            if used_flora else ""
        )
        system = sign_system + avoid_instruction

        horoscope_instruction = HOROSCOPE_TEMPLATE.format(
            segment=i + 1, n_signs=1, s="",
            lieux_spirituels=LIEUX_SPIRITUELS,
            contexte_local=contexte_local,
        )
        user_prompt = (
            f"HOROSCOPE DU JOUR — {sign_fr} ({sign_en.capitalize()}) :\n{raw_text}\n\n"
            f"MOMENT DE LA JOURNÉE : {moment_label}\n\n"
            f"INSTRUCTIONS :\n{horoscope_instruction}"
        )

        print(f"✍️  [{i + 1}/{n_signs}] Rédaction {sign_fr} (Mistral Large)…")
        segment = _strip_markdown(
            call_mistral(system, user_prompt, temperature=0.75, max_tokens=650)
        )

        newly_used = _extract_used_flora(segment)
        if newly_used and args.verbose:
            print(f"   🌿 Flore détectée : {', '.join(newly_used)}")
        used_flora = list(dict.fromkeys(used_flora + newly_used))

        if args.verbose:
            print(f"\n── {sign_fr} ──────────────────────────────────────────")
            print(segment)
            print("─────────────────────────────────────────────────────────\n")

        seg_path = seg_dir / f"seg_{i:02d}.mp3"
        print(f"🔊 [{i + 1}/{n_signs}] TTS {sign_fr} → {seg_path.name}")
        _tts_call(_normalize_for_tts(segment), seg_path, TTS_VOICES["curious"])
        seg_paths.append(seg_path)

    # ── Outro dédiée ──────────────────────────────────────────────────────────
    print("✍️  Rédaction outro (Mistral Large)…")
    outro_system = (
        maryse_base +
        "Tu rédiges UNIQUEMENT la conclusion de l'horoscope du jour — "
        "pas de signe, juste la clôture."
    )
    outro_user = (
        "Une courte formule de clôture dans ta voix — bénédiction ou congé — "
        "puis une formule de rendez-vous du type 'À demain pour un nouvel horoscope' "
        "ou une variante naturelle, jamais la même tournure. Deux phrases maximum."
    )
    outro_text = _strip_markdown(
        call_mistral(outro_system, outro_user, temperature=0.75, max_tokens=100)
    )
    if args.verbose:
        print(f"\n── OUTRO ────────────────────────────────────────────────")
        print(outro_text)
        print("─────────────────────────────────────────────────────────\n")
    outro_path = seg_dir / "seg_outro.mp3"
    print(f"🔊 TTS outro → {outro_path.name}")
    _tts_call(_normalize_for_tts(outro_text), outro_path, TTS_VOICES["curious"])

    # Sauvegarde anti-répétition flore (uniquement les nouveaux éléments de ce run)
    new_flora = [kw for kw in used_flora if kw not in recent_flora]
    if new_flora:
        _save_used_flora(gen_date, new_flora)

    # ── Assemblage audio final : intro + signes + outro ───────────────────────
    stinger = resolve_stinger(args.stinger)
    all_audio = [intro_path] + seg_paths + [outro_path]
    print(f"🔗 Assemblage intro + {n_signs} signes + outro → {output_path}")
    _assemble_audio(all_audio, stinger, output_path)
    print(f"✅ Horoscope sauvegardé : {output_path}")

    # ── Telegram audio ────────────────────────────────────────────────────────
    if args.telegram:
        try:
            signs_label = ", ".join(signs_fr)
            send_telegram_audio(output_path, f"🔮 Horoscope — {_date_fr(gen_date)}\n{signs_label}")
        except Exception as _e:
            print(f"⚠️  Telegram audio échoué (non bloquant) : {_e}")

    # ── Vidéo TikTok + Telegram ───────────────────────────────────────────────
    if args.tiktok:
        try:
            video_dir = output_path.parent / f"horoscope-{gen_date.strftime('%Y%m%d')}"
            concat_video = generate_tiktok(
                intro_path=intro_path,
                seg_paths=seg_paths,
                outro_path=outro_path,
                signs_fr=signs_fr,
                output_dir=video_dir,
                stinger=stinger,
            )
            if concat_video:
                print(f"🎬 Vidéo horoscope : {concat_video}")
                send_telegram_video(concat_video, f"🔮 Horoscope — {_date_fr(gen_date)}")
        except Exception as _e:
            print(f"⚠️  TikTok/Telegram échoué (non bloquant) : {_e}")

    # ── Buzzsprout ────────────────────────────────────────────────────────────
    if not args.dry_run and not args.no_send and BUZZSPROUT_API_TOKEN and BUZZSPROUT_PODCAST_ID:
        signs_label = ", ".join(signs_fr)
        bz_title = f"Horoscope du {_date_fr(gen_date)} — {signs_label}"
        bz_description = (
            f"Horoscope du {_date_fr(gen_date)} par Maryse.\n"
            f"Signes du jour : {signs_label}.\n\n"
            "Flash Info Karukera — actualités et horoscope de la Guadeloupe."
        )
        publish_buzzsprout(output_path, bz_title, bz_description, BUZZSPROUT_TAGS)
    elif args.dry_run or args.no_send:
        print(f"{'--dry-run' if args.dry_run else '--no-send'} : pas de publication Buzzsprout.")
    else:
        print("⚠️  BUZZSPROUT_API_TOKEN / BUZZSPROUT_PODCAST_ID manquants — publication ignorée.")


if __name__ == "__main__":
    main()
