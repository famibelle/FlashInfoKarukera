#!/home/medhi/SourceCode/KreyolKeyb/.venv/bin/python3
"""
Flash info Guadeloupe — workflow complet
Collecte RSS → Script → Audio TTS (Voxtral) → Envoi Telegram
"""

import os
import sys
import json
import base64
import argparse
import subprocess
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, date as Date
from email.utils import parsedate
from pathlib import Path
from zoneinfo import ZoneInfo

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

from data.sources import RSS_FEEDS, RSS_SOURCES

_FEED_CATEGORY: dict[str, str] = {s.url: s.category for s in RSS_SOURCES}
MAX_ITEMS = 7          # 7 sujets → ~2m-2m30 audio
DESC_MAX_CHARS = 400   # description tronquée pour donner assez de contexte

MISTRAL_API_KEY     = os.environ["MISTRAL_API_KEY"]
TTS_MODEL           = "voxtral-mini-tts-2603"
STT_MODEL           = "voxtral-mini-latest"
TTS_VOICE_DEFAULT   = "fr_marie_neutral"

# Mapping tonalité → voice_id Voxtral (voix Marie en français)
TTS_VOICES = {
    "neutral":  "fr_marie_neutral",
    "happy":    "fr_marie_happy",
    "excited":  "fr_marie_excited",
    "sad":      "fr_marie_sad",
    "angry":    "fr_marie_angry",
    "curious":  "fr_marie_curious",
}

TELEGRAM_BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID    = os.environ["TELEGRAM_CHAT_ID"]

BUZZSPROUT_API_TOKEN  = os.environ["BUZZSPROUT_API_TOKEN"]
BUZZSPROUT_PODCAST_ID = os.environ["BUZZSPROUT_PODCAST_ID"]

X_API_KEY            = os.environ["X_API_KEY"]
X_API_SECRET         = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN       = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]

YOUTUBE_CLIENT_ID     = os.environ.get("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")

OUTPUT_DIR      = Path("/tmp")
STINGERS_DIR    = Path(__file__).parent / "Stingers"
PROMPTS_DIR     = Path(__file__).parent / "prompts"
GUADELOUPE_TZ   = ZoneInfo("America/Guadeloupe")

WEATHER_LAT  = 16.17    # centre Guadeloupe (entre Basse-Terre et Grande-Terre)
WEATHER_LON  = -61.58
WEATHER_API  = "https://api.open-meteo.com/v1/forecast"

from data.geography import (
    LIEUX_GUADELOUPE as _LIEUX_GUADELOUPE,
    LIEUX_MONDE as _LIEUX_MONDE,
    SOURCE_NAMES as _SOURCE_NAMES,
)
from data.tts_normalize import (
    PRONONCIATIONS_LOCALES as _PRONONCIATIONS_LOCALES,
    SIGLES_MOT as _SIGLES_MOT,
    ABBREVS as _ABBREVS,
)
from data.weather_codes import WMO_CODES as _WMO

# ── Helpers ───────────────────────────────────────────────────────────────────

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

def _source_name(url: str) -> str:
    """Extrait un nom de média lisible depuis l'URL d'un flux RSS."""
    from urllib.parse import urlparse
    host = (urlparse(url).hostname or "").removeprefix("www.")
    for key, name in _SOURCE_NAMES.items():
        if key in host:
            return name
    # fallback : premier segment du domaine, capitalisé
    return host.split(".")[0].capitalize()


_LIEUX_GUADELOUPE_LOWER = {l.lower(): l for l in _LIEUX_GUADELOUPE}
_LIEUX_MONDE_LOWER = {l.lower(): l for l in _LIEUX_MONDE}

def _extract_lieu(title: str, desc: str) -> str:
    """
    Cherche un lieu géographique dans title + desc.
    Priorité : commune guadeloupéenne → pays/ville mondiale → N/A.
    """
    import re
    haystack = f"{title} {desc}".lower()

    def _match(mapping: dict) -> str | None:
        for lieu_low, lieu_orig in mapping.items():
            pat = r"(?<![a-zàâéèêëîïôùûüç])" + re.escape(lieu_low) + r"(?![a-zàâéèêëîïôùûüç])"
            if re.search(pat, haystack):
                return lieu_orig
        return None

    return _match(_LIEUX_GUADELOUPE_LOWER) or _match(_LIEUX_MONDE_LOWER) or "N/A"


def _date_fr(d: Date) -> str:
    """Retourne ex: 'samedi 19 avril 2026'."""
    s = d.strftime("%A %-d %B %Y")
    for en, fr in {**_FR_DAYS, **_FR_MONTHS}.items():
        s = s.replace(en, fr)
    return s


def _load_prompt(filename: str) -> str:
    """Charge un prompt système depuis le dossier prompts/ en retirant le trailing whitespace."""
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8").rstrip()


# ── Étape 1 : Collecte RSS ────────────────────────────────────────────────────

def _shorten_desc(text: str, max_chars: int) -> str:
    """Garde la première phrase ou tronque à max_chars caractères."""
    text = text.strip()
    for sep in (".", "!", "?"):
        idx = text.find(sep)
        if 20 < idx <= max_chars:
            return text[: idx + 1]
    return text[:max_chars].rsplit(" ", 1)[0] if len(text) > max_chars else text


def _parse_feed_items(root: ET.Element, target_date: Date) -> list[tuple]:
    """Retourne une liste de (datetime_or_None, title, pub_date_str, desc) depuis RSS ou Atom."""
    results = []
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    # RSS <item>
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        desc = _shorten_desc((item.findtext("description") or "").strip(), DESC_MAX_CHARS)
        if not title or not desc:
            continue
        parsed = parsedate(pub_date)
        if parsed:
            item_date = datetime(*parsed[:6])
            if item_date.date() != target_date:
                continue
        else:
            item_date = None
        results.append((item_date, title, pub_date, desc))

    # Atom <entry>
    for entry in root.findall(".//atom:entry", ns) or root.findall(".//entry"):
        title_el = entry.find("atom:title", ns) or entry.find("title")
        title = (title_el.text or "").strip() if title_el is not None else ""
        updated_el = entry.find("atom:updated", ns) or entry.find("updated") or entry.find("atom:published", ns) or entry.find("published")
        pub_date = (updated_el.text or "").strip() if updated_el is not None else ""
        summary_el = entry.find("atom:summary", ns) or entry.find("summary") or entry.find("atom:content", ns) or entry.find("content")
        raw_desc = (summary_el.text or "").strip() if summary_el is not None else ""
        desc = _shorten_desc(raw_desc, DESC_MAX_CHARS)
        if not title or not desc:
            continue
        item_date = None
        if pub_date:
            try:
                item_date = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                if item_date.date() != target_date:
                    continue
            except ValueError:
                pass
        results.append((item_date, title, pub_date, desc))

    return results



_LIEUX_GUADELOUPE_SET = {l.lower() for l in _LIEUX_GUADELOUPE} | {"guadeloupe", "karukera"}

def _lieu_priority(lieu: str) -> int:
    """0 = local Guadeloupe, 1 = lieu inconnu (N/A), 2 = international."""
    if lieu.lower() in _LIEUX_GUADELOUPE_SET:
        return 0
    if lieu == "N/A":
        return 1
    return 2


def fetch_news(feeds: list[str], max_items: int, target_date: Date) -> list[dict]:
    all_items = []
    for url in feeds:
        print(f"📰 Collecte : {url}")
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                content = r.read()
            root = ET.fromstring(content)
            parsed = _parse_feed_items(root, target_date)
            print(f"   {len(parsed)} actualités du jour")
            all_items.extend((dt, t, d, desc, url) for dt, t, d, desc in parsed)
        except Exception as e:
            print(f"   ⚠️  Erreur sur {url} : {e}")

    # Tri par date décroissante (None en dernier)
    all_items.sort(key=lambda x: x[0] or datetime.min, reverse=True)

    candidates = [
        {
            "title": t, "date": d, "desc": desc,
            "source": _source_name(feed_url),
            "lieu": _extract_lieu(t, desc),
            "category": _FEED_CATEGORY.get(feed_url, "general"),
        }
        for _, t, d, desc, feed_url in all_items
    ]

    # Priorité : local Guadeloupe (0) → lieu inconnu (1) → international (2)
    # À priorité égale, l'ordre chronologique (déjà trié) est conservé.
    candidates.sort(key=lambda it: _lieu_priority(it["lieu"]))
    items = candidates[:max_items]

    local_count = sum(1 for it in items if _lieu_priority(it["lieu"]) == 0)
    intl_count  = sum(1 for it in items if _lieu_priority(it["lieu"]) == 2)
    print(f"   Total retenu : {len(items)} actualités "
          f"({local_count} locales, {len(items)-local_count-intl_count} N/A, {intl_count} internationales)")
    return items


# ── Étape 1b : Bulletin météo (Open-Meteo, sans clé) ─────────────────────────

def _rain_label(mm: float) -> str:
    if mm < 0.2:  return "pas de pluie"
    if mm < 2:    return "quelques gouttes"
    if mm < 8:    return "averses légères"
    if mm < 20:   return "averses modérées"
    if mm < 40:   return "fortes pluies"
    return "très fortes pluies"

def _wind_label(kmh: float) -> str:
    if kmh < 15:  return "vent faible"
    if kmh < 30:  return "brise"
    if kmh < 50:  return "vent modéré"
    if kmh < 70:  return "vent fort"
    return "vent très fort"


def fetch_weather(target_date: Date) -> str:
    """Retourne un résumé météo pour Pointe-à-Pitre à la date donnée."""
    print("🌤️  Collecte météo (Open-Meteo)...")
    date_iso = target_date.isoformat()
    params = urllib.parse.urlencode({
        "latitude": WEATHER_LAT,
        "longitude": WEATHER_LON,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode,windspeed_10m_max",
        "timezone": "America/Guadeloupe",
        "start_date": date_iso,
        "end_date": date_iso,
    })
    with urllib.request.urlopen(f"{WEATHER_API}?{params}", timeout=15) as r:
        data = json.loads(r.read())

    daily  = data["daily"]
    code   = daily["weathercode"][0]
    t_max  = daily["temperature_2m_max"][0]
    t_min  = daily["temperature_2m_min"][0]
    rain   = daily["precipitation_sum"][0]
    wind   = daily["windspeed_10m_max"][0]

    cond      = _WMO.get(code, "temps variable")
    summary   = (
        f"{cond}, {t_min:.0f}°C / {t_max:.0f}°C, "
        f"{_wind_label(wind)}, {_rain_label(rain)}."
    )
    print(f"   {summary}")
    return summary


# ── Étape 2 : Segments rédigés par Maryse via Mistral ────────────────────────

MISTRAL_CHAT_MODEL = "mistral-large-latest"
MISTRAL_CHAT_URL   = "https://api.mistral.ai/v1/chat/completions"
SEG_SEPARATOR      = "<<<SEG>>>"


def call_mistral(
    system: str,
    user: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 1500,
    json_mode: bool = False,
    timeout: int = 60,
) -> str:
    """Appelle Mistral chat completions et retourne le contenu du message de réponse."""
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
    with urllib.request.urlopen(req, timeout=timeout) as r:
        result = json.loads(r.read())
    return result["choices"][0]["message"]["content"]


MARYSE_SYSTEM = _load_prompt("maryse.md")


def _strip_markdown(text: str) -> str:
    import re
    text = re.sub(r"\*+([^*]+)\*+", r"\1", text)
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"^\s*[-#>]+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_segments(items: list[dict], date_str: str, weather: str, sources: list[str]) -> list[str]:
    print("✍️  Rédaction des segments par Maryse (Mistral Large)...")
    articles = "\n\n".join(
        f"[{i+1}] {item['title']}\n{item['desc']}" for i, item in enumerate(items)
    )
    n_segs = len(items) + 3  # intro + météo + items + outro
    if items:
        news_block = f"Voici les {len(items)} actualités du jour :\n\n{articles}\n\n"
        sources_str = " et ".join(sources) if sources else "les médias locaux"
        outro_template = (
            f"Voilà pour ce Flash Info Guadeloupe du {date_str}. "
            f"Sources : {sources_str}. "
            f"On se retrouve [prochain rendez-vous, ex: demain matin]. "
            f"Bonne journée à toutes et à tous."
        )
        news_instructions = (
            f"- Segments 3 à {len(items)+2} : un seul sujet par segment, 60 à 90 mots chacun.\n"
            f"- Segment {n_segs} : outro. Recopie ce modèle en remplaçant uniquement "
            f"[prochain rendez-vous] :\n  \"{outro_template}\""
        )
    else:
        n_segs = 3  # intro + météo + outro seulement
        news_block = ""
        sources_str = " et ".join(sources) if sources else "les médias locaux"
        outro_template = (
            f"Voilà pour ce Flash Info Guadeloupe du {date_str}. "
            f"Sources : {sources_str}. "
            f"On se retrouve [prochain rendez-vous]. "
            f"Bonne journée à toutes et à tous."
        )
        news_instructions = (
            f"- Segment 3 : outro. Recopie ce modèle en remplaçant uniquement "
            f"[prochain rendez-vous] :\n  \"{outro_template}\""
        )

    user_prompt = (
        f"Flash info Guadeloupe du {date_str}.\n\n"
        f"MÉTÉO DU JOUR (toute la Guadeloupe) :\n{weather}\n\n"
        f"{news_block}"
        f"Rédige exactement {n_segs} segments séparés par \"{SEG_SEPARATOR}\" :\n"
        f"- Segment 1 : intro (jour + date + accroche)\n"
        f"- Segment 2 : météo du jour en style oral\n"
        f"{news_instructions}"
    )
    raw = call_mistral(MARYSE_SYSTEM, user_prompt, temperature=0.75, max_tokens=1200)

    import re as _re
    segments = [_strip_markdown(s) for s in raw.split(SEG_SEPARATOR) if s.strip()]

    # Fallback : Mistral a utilisé "---" (markdown) à la place du séparateur imposé
    if len(segments) < 2:
        print("   ⚠️  Séparateur <<<SEG>>> non trouvé — tentative de fallback sur '---'")
        segments = [_strip_markdown(s) for s in _re.split(r"\n\s*---+\s*\n", raw) if s.strip()]

    if len(segments) < 2:
        print("   ⚠️  Fallback échoué — réponse brute Mistral :")
        print(raw[:500])

    print(f"   {len(segments)} segments générés")
    return segments


# ── Étape 2b : Réviseur stylistique ──────────────────────────────────────────

STYLIST_SYSTEM = _load_prompt("styliste.md")


ANCHOR_SYSTEM = _load_prompt("ancrage.md")


def anchor_local(segments: list[str], items: list[dict]) -> list[str]:
    print("📍 Ancrage local (Mistral Large)...")
    full_script = f"\n{SEG_SEPARATOR}\n".join(segments)
    json_context = json.dumps(
        [
            {
                "titre": it["title"],
                "lieu": it.get("lieu", "N/A"),
                "source": it["source"],
                "description": it["desc"],
            }
            for it in items
        ],
        ensure_ascii=False, indent=2
    )
    user_prompt = (
        f"SCRIPT_INITIAL :\n{full_script}\n\n"
        f"JSON_EXTRACTION :\n{json_context}"
    )
    raw = call_mistral(ANCHOR_SYSTEM, user_prompt)
    anchored = [_strip_markdown(s) for s in raw.split(SEG_SEPARATOR) if s.strip()]

    if len(anchored) != len(segments):
        print(f"   ⚠️  Ancrage retourné {len(anchored)} segments au lieu de {len(segments)} — fallback sur l'original")
        return segments

    print(f"   Ancrage appliqué ({len(anchored)} segments)")
    return anchored


def _enforce_prononciations(segments: list[str]) -> list[str]:
    """Applique _PRONONCIATIONS_LOCALES sur chaque segment.
    - Insensible à la casse (Unar, unar, UNAR → même résultat)
    - Normalise les apostrophes typographiques avant matching
    - Word-boundary pour éviter les remplacements partiels
    """
    import re
    result = []
    for seg in segments:
        # Normalise apostrophes typographiques pour que \b fonctionne correctement
        seg = seg.replace("\u2019", "'").replace("\u2018", "'")
        for ecrit, oral in _PRONONCIATIONS_LOCALES.items():
            seg = re.sub(r"\b" + re.escape(ecrit) + r"\b", oral, seg, flags=re.IGNORECASE)
        result.append(seg)
    return result


def _ensure_sources_in_outro(segments: list[str], sources: list[str]) -> list[str]:
    """Injecte 'Sources : X et Y.' dans l'outro si le modèle l'a omis."""
    if not segments:
        return segments
    outro = segments[-1]
    if "Sources :" not in outro and sources:
        import re
        sources_str = " et ".join(sources)
        outro = re.sub(
            r"(Voilà pour ce Flash Info Guadeloupe[^.]*\.)",
            rf"\1 Sources : {sources_str}.",
            outro,
            count=1,
        )
        segments = segments[:-1] + [outro]
    return segments


def revise_style(segments: list[str]) -> list[str]:
    print("✏️  Révision stylistique (Mistral Large)...")
    full_script = f"\n{SEG_SEPARATOR}\n".join(segments)
    raw = call_mistral(STYLIST_SYSTEM, full_script)
    revised = [_strip_markdown(s) for s in raw.split(SEG_SEPARATOR) if s.strip()]

    if len(revised) != len(segments):
        print(f"   ⚠️  Réviseur a retourné {len(revised)} segments au lieu de {len(segments)} — fallback sur l'original")
        return segments

    print(f"   Révision appliquée ({len(revised)} segments)")
    return revised


# ── Étape 2d : Classification émotionnelle par segment ───────────────────────

TONE_SYSTEM = _load_prompt("tones.md")


def classify_tones(segments: list[str]) -> list[str]:
    """Retourne une liste de tags émotionnels, un par segment."""
    print("🎭 Classification tonale (Mistral Large)...")
    numbered = [{"idx": i, "text": s} for i, s in enumerate(segments)]
    user_payload = json.dumps({"segments": numbered}, ensure_ascii=False)
    try:
        raw = call_mistral(
            TONE_SYSTEM, user_payload,
            temperature=0.1, max_tokens=300, json_mode=True,
        )
        parsed = json.loads(raw)
        tones = parsed if isinstance(parsed, list) else parsed.get("tones") or parsed.get("tags") or next(iter(parsed.values()))
        tones = [t if t in TTS_VOICES else "neutral" for t in tones]
        if len(tones) != len(segments):
            raise ValueError(f"length mismatch: got {len(tones)} for {len(segments)} segments")
    except Exception as e:
        print(f"   ⚠️  Classification échouée ({e}) — fallback sur 'neutral' partout")
        tones = ["neutral"] * len(segments)

    for i, (tag, seg) in enumerate(zip(tones, segments)):
        preview = seg[:60].replace("\n", " ")
        print(f"   [{i+1}/{len(segments)}] {tag:8s} → {preview}…")
    return tones


# ── Étape 3 : Génération audio TTS par segment + assemblage FFmpeg ────────────

import re as _re

try:
    from num2words import num2words as _n2w

    def _num_fr(n: str) -> str:
        s = n.replace(" ", "").replace(" ", "").replace(",", ".")
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
    """Applique les prononciations locales guadeloupéennes (Lyannaj → Lyan naje, etc.)."""
    for ecrit, oral in _PRONONCIATIONS_LOCALES.items():
        text = _re.sub(r"\b" + _re.escape(ecrit) + r"\b", oral, text)
    return text


def _norm_typography(text: str) -> str:
    """Normalise apostrophes/guillemets typographiques et supprime les emojis."""
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", " ")
    return _re.sub(r"[^\x00-\x7F\u00C0-\u024F\u1E00-\u1EFF\n]", " ", text)


def _norm_numero(text: str) -> str:
    """n° / N° → numéro / Numéro."""
    text = _re.sub(r"\bn°\s*", "numéro ", text, flags=_re.IGNORECASE)
    text = _re.sub(r"\bN°\s*", "Numéro ", text)
    return text


def _norm_ordinals(text: str) -> str:
    """1er/1re → premier/première, 2e/2ème → deuxième…"""
    text = _re.sub(r"\b1er\b", "premier", text)
    text = _re.sub(r"\b1re\b", "première", text)
    return _re.sub(r"\b(\d+)(?:e|ème|eme)\b",
                   lambda m: _ordinal_fr(m.group(1)), text)


def _norm_currencies(text: str) -> str:
    """3,5M€ → millions d'euros ; 15€ → euros ; 20$ → dollars."""
    text = _re.sub(r"(\d+(?:[,\.]\d+)?)\s*[Mm](?:illions?)?\s*€",
                   lambda m: f"{_num_fr(m.group(1))} millions d'euros", text)
    text = _re.sub(r"(\d+(?:[,\.]\d+)?)\s*€",
                   lambda m: f"{_num_fr(m.group(1))} euros", text)
    text = _re.sub(r"(\d+(?:[,\.]\d+)?)\s*\$",
                   lambda m: f"{_num_fr(m.group(1))} dollars", text)
    return text


def _norm_scores(text: str) -> str:
    """Scores sportifs : 3-1 → trois à un."""
    return _re.sub(r"\b(\d+)-(\d+)\b",
                   lambda m: f"{_num_fr(m.group(1))} à {_num_fr(m.group(2))}", text)


def _norm_dom_codes(text: str) -> str:
    """Codes DOM 971-976 → lecture spécifique."""
    for code, spoken in _DOM_CODES.items():
        text = _re.sub(r"\b" + code + r"\b", spoken, text)
    return text


def _norm_hours(text: str) -> str:
    """07h30 → sept heures trente."""
    return _re.sub(
        r"\b(\d{1,2})h(\d{2})\b",
        lambda m: f"{_num_fr(m.group(1))} heures {_num_fr(m.group(2))}",
        text,
    )


def _norm_units(text: str) -> str:
    """Nombres avec unités : 25°C, 80km/h, 10mm, 50%, m²…"""
    for pattern, repl in _UNIT_PATTERNS:
        text = _re.sub(pattern, repl, text, flags=_re.IGNORECASE)
    return text


def _norm_plain_numbers(text: str) -> str:
    """Nombres isolés restants → texte."""
    return _re.sub(r"\b(\d[\d ]*(?:[,\.]\d+)?)\b",
                   lambda m: _num_fr(m.group(1)), text)


def _norm_acronyms(text: str) -> str:
    """Sigles : R.C.I → RCI ; S.D.I.S → S. D. I. S. ; CHU → C. H. U. (sauf _SIGLES_MOT)."""
    # 9a. Sigles prononcés comme des mots (R.C.I → RCI) avant épellation
    for sm in _SIGLES_MOT:
        dotted = ".".join(sm)
        text = text.replace(dotted + ".", sm).replace(dotted, sm)
    # 9b. Sigles avec points collés
    text = _re.sub(
        r"\b([A-Z](?:\.[A-Z]){1,4})\.?\b",
        lambda m: m.group(1).replace(".", ". ") + ".",
        text,
    )
    # 9c. Sigles tout-majuscules sans points (2-5 lettres)
    return _re.sub(
        r"\b([A-Z]{2,5})\b",
        lambda m: m.group(1) if m.group(1) in _SIGLES_MOT else ". ".join(m.group(1)) + ".",
        text,
    )


def _norm_abbreviations(text: str) -> str:
    """Abréviations textuelles (M. → Monsieur, etc.)."""
    for abbr, full in _ABBREVS.items():
        if abbr[0].isalpha():
            escaped = _re.escape(abbr)
            # trailing \b seulement si l'abréviation finit par un caractère de mot
            pattern = r"\b" + escaped + (r"\b" if abbr[-1].isalnum() else "")
            text = _re.sub(pattern, full, text)
        else:
            text = text.replace(abbr, full)
    return text


def _norm_honorifics(text: str) -> str:
    """Me devant un nom propre → Maître."""
    return _re.sub(r"\bMe\b(?=\s+[A-ZÀÂÉÈÊËÎÏÔÙÛÜ])", "Maître", text)


def _norm_residual(text: str) -> str:
    """Caractères spéciaux résiduels et whitespace."""
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


def _tts_call(text: str, output_path: Path, voice_id: str = TTS_VOICE_DEFAULT) -> None:
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
    with urllib.request.urlopen(req, timeout=60) as r:
        response = json.loads(r.read())
    if "audio_data" not in response:
        raise RuntimeError(f"TTS error: {response}")
    output_path.write_bytes(base64.b64decode(response["audio_data"]))


def resolve_stinger(name: str | None) -> Path:
    """Résout le stinger à utiliser : depuis STINGERS_DIR ou génère un synthétique."""
    STINGERS_DIR.mkdir(exist_ok=True)
    available = sorted(STINGERS_DIR.glob("*.mp3")) + sorted(STINGERS_DIR.glob("*.wav"))

    if name:
        candidate = STINGERS_DIR / name
        if not candidate.exists():
            # Essayer comme chemin absolu
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
        print(f"🎵 Stinger : {chosen.name}  (utilisez --stinger pour choisir parmi : {', '.join(f.name for f in available)})")
        return chosen

    # Aucun fichier → génération synthétique
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


def generate_audio(
    segments: list[str],
    output_path: Path,
    stinger: Path,
    tones: list[str] | None = None,
    keep_segments: bool = False,
) -> tuple[Path, list[Path]]:
    """Génère un MP3 par segment, insère le stinger entre chaque, concatène."""
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
        _tts_call(_normalize_for_tts(text), seg_path, voice_id=voice_id)
        # Léger padding pour éviter la troncature TTS en fin de segment
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

    # Assemblage via filter_complex concat — gère les différences de format
    # (fréquence, mono/stéréo) entre segments TTS et stinger
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


# ── Étape 3b : Transcription STT (optionnelle) ───────────────────────────────

def _mistral_stt(audio_path: Path, word_timestamps: bool = False) -> dict:
    """Appelle l'API STT Mistral et retourne le JSON brut."""
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
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body_err = e.read().decode(errors="replace")
        raise RuntimeError(f"STT HTTP {e.code}: {body_err}") from None


def transcribe_audio(audio_path: Path) -> str:
    return _mistral_stt(audio_path)["text"]


def transcribe_with_words(audio_path: Path) -> list[dict]:
    """Retourne [{word, start, end}, …] depuis les segments STT Voxtral."""
    segments = _mistral_stt(audio_path, word_timestamps=True).get("segments", [])
    return [
        {"word": s["text"].strip(), "start": s["start"], "end": s["end"]}
        for s in segments
        if s.get("text", "").strip()
    ]


# ── Étape 3c : Vidéos TikTok par segment ─────────────────────────────────────

TIKTOK_COLORS = {
    "neutral":  "#FFFFFF",
    "happy":    "#FFD700",
    "excited":  "#FF4500",
    "sad":      "#6495ED",
    "angry":    "#FF0000",
    "curious":  "#00CED1",
}

INTERSTITIAL_DURATION = 2.5  # secondes

# Mapping catégorie → (label affiché, couleur hex)
INTERSTITIAL_STYLES: dict[str, tuple[str, str]] = {
    "météo":        ("🌤  MÉTÉO",         "#4A90D9"),
    "vie locale":   ("🏘  VIE LOCALE",    "#2ECC71"),
    "sports":       ("⚽ SPORTS",        "#FF6B00"),
    "social":       ("🤝 SOCIAL",        "#9B59B6"),
    "politique":    ("🏛  POLITIQUE",     "#E74C3C"),
    "economie":     ("💼 ÉCONOMIE",      "#F39C12"),
    "environement": ("🌿 ENVIRONNEMENT", "#27AE60"),
    "en bref":      ("📰 EN BREF",       "#1ABC9C"),
    "general":      ("📡 ACTUALITÉS",    "#95A5A6"),
    "custom":       ("🎙  FLASH INFO",    "#FFFFFF"),
}


def _ass_time(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"


def _ass_color(hex_color: str) -> str:
    """#RRGGBB → &H00BBGGRR& (ordre canaux ASS)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"&H00{b:02X}{g:02X}{r:02X}&"


def _make_interstitial(category: str, output_path: Path) -> Path:
    """Génère un MP4 interstitiel 1080×1920 de INTERSTITIAL_DURATION secondes."""
    label, color = INTERSTITIAL_STYLES.get(category, INTERSTITIAL_STYLES["general"])
    color_hex = color.lstrip("#")
    duration = INTERSTITIAL_DURATION
    # Extrait uniquement le texte (sans l'emoji — FFmpeg drawtext ne supporte pas les polices couleur)
    parts = label.split(" ", 1)
    text = parts[1] if len(parts) == 2 else parts[0]
    filter_v = (
        f"color=c=black:s=1080x1920:r=30:d={duration},"
        f"drawbox=x=80:y=910:w=920:h=6:color=0x{color_hex}@1:t=fill,"
        f"drawbox=x=80:y=1050:w=920:h=6:color=0x{color_hex}@1:t=fill,"
        f"drawtext=text='{text}':"
        f"fontsize=110:fontcolor=0x{color_hex}:font=Sans:fontstyle=Bold:"
        f"x=(w-tw)/2:y=960:"
        f"shadowcolor=black@0.6:shadowx=3:shadowy=3,"
        f"drawtext=text='Flash Info Karukera par Botiran':"
        f"fontsize=38:fontcolor=white@0.5:font=Sans:"
        f"x=(w-tw)/2:y=1080"
    )
    proc = subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", filter_v,
        "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={duration}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration),
        "-shortest",
        str(output_path),
    ], capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg interstitiel error: {proc.stderr.decode()}")
    return output_path


def _make_ass(words: list[dict], tone: str) -> str:
    """Génère un fichier ASS karaoke : mot courant coloré, précédent/suivant atténués."""
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
        "Style: Default,Arial,96,&H00FFFFFF,&H00FFFFFF,&H00000000,"
        "&HA0000000,0,0,0,0,100,100,0,0,1,5,2,5,80,80,0,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    events = []
    for i, word in enumerate(words):
        start = word["start"]
        end   = max(word["end"], start + 0.05)
        parts = []
        if i > 0:
            parts.append(f"{{\\c{dim_col}\\fs80}}{words[i - 1]['word']}")
        parts.append(f"{{\\c{tone_col}\\fs108\\b1}}{word['word']}{{\\b0}}")
        if i < len(words) - 1:
            parts.append(f"{{\\c{dim_col}\\fs80}}{words[i + 1]['word']}")
        # \an5 = centré horizontalement et verticalement dans la zone texte
        # \pos(540,1210) = centre horizontal, milieu de la zone sous le spectre (500px + 710px restants / 2)
        events.append(
            f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},"
            f"Default,,0,0,0,,{{\\an5\\pos(540,1210)}}{' '.join(parts)}"
        )

    return header + "\n".join(events) + "\n"


def _tiktok_segment_video(seg_path: Path, ass_path: Path, tone: str, output_path: Path) -> None:
    color_hex = TIKTOK_COLORS.get(tone, "#FFFFFF").lstrip("#")
    # spectrogramme 500 px en haut, sous-titres centrés verticalement (an=5 dans ASS)
    filter_complex = (
        f"color=c=black:s=1080x1920:r=30[bg];"
        f"[0:a]showwaves=s=1080x500:mode=cline:colors=0x{color_hex}:scale=sqrt:rate=30[waves];"
        f"[bg][waves]overlay=0:0[v];"
        f"[v]ass={ass_path}[vout]"
    )
    proc = subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(seg_path),
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_path),
    ], capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg tiktok error: {proc.stderr.decode()}")


def generate_tiktok(
    seg_paths: list[Path],
    segments: list[str],
    tones: list[str],
    output_dir: Path,
) -> list[tuple[int, Path]]:
    """Retourne [(index_segment, chemin_mp4), …]."""
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"🎬 Génération vidéos : {len(seg_paths)} segments → {output_dir}")

    videos: list[tuple[int, Path]] = []
    for i, (seg_path, _text, tone) in enumerate(zip(seg_paths, segments, tones)):
        label = "INTRO" if i == 0 else "MÉTÉO" if i == 1 else f"SEG{i - 1:02d}"
        print(f"   [{i + 1}/{len(seg_paths)}] {label} ({tone}) — STT timestamps…")

        words = transcribe_with_words(seg_path)
        if not words:
            print(f"   ⚠️  STT sans mots pour le segment {i + 1} — ignoré")
            continue

        ass_path = output_dir / f"seg_{i:02d}.ass"
        ass_path.write_text(_make_ass(words, tone), encoding="utf-8")

        video_path = output_dir / f"seg_{i:02d}.mp4"
        print(f"   [{i + 1}/{len(seg_paths)}] FFmpeg → {video_path.name}…")
        _tiktok_segment_video(seg_path, ass_path, tone, video_path)
        videos.append((i, video_path))
        print(f"   ✅ {video_path.name} ({video_path.stat().st_size:,} bytes)")

    return videos


# ── Étape 4 : Envoi Telegram ──────────────────────────────────────────────────

def send_telegram(audio_path: Path, caption: str) -> None:
    print(f"📤 Envoi Telegram (chat_id={TELEGRAM_CHAT_ID})...")
    boundary = "----FlashInfoBoundary"
    body_parts = []

    def field(name, value):
        return (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        ).encode()

    body = b""
    body += field("chat_id", TELEGRAM_CHAT_ID)
    body += field("caption", caption)
    body += field("title", "Flash info Guadeloupe")
    body += field("performer", "Équipe Toutmoun")

    audio_data = audio_path.read_bytes()
    body += (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="audio"; filename="{audio_path.name}"\r\n'
        f"Content-Type: audio/mpeg\r\n\r\n"
    ).encode() + audio_data + b"\r\n"
    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendAudio",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read())

    if not result.get("ok"):
        raise RuntimeError(f"Telegram error: {result}")
    print("   Envoyé ✅")


def send_telegram_video(video_path: Path, caption: str) -> None:
    boundary = "----FlashInfoBoundary"

    def field(name, value):
        return (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        ).encode()

    body = field("chat_id", TELEGRAM_CHAT_ID) + field("caption", caption)
    body += (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="video"; filename="{video_path.name}"\r\n'
        f"Content-Type: video/mp4\r\n\r\n"
    ).encode() + video_path.read_bytes() + b"\r\n"
    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        result = json.loads(r.read())
    if not result.get("ok"):
        raise RuntimeError(f"Telegram video error: {result}")
    print(f"   {video_path.name} envoyé ✅")


# ── Étape 5 : Publication Buzzsprout → Spotify ───────────────────────────────

BUZZSPROUT_TAGS = "Guadeloupe, actualité, flash info, Antilles, Caraïbes, France-Antilles, info locale"

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
    episode_id = result.get("id", "")
    print(f"   Épisode publié ✅  id={episode_id}  url={episode_url}")
    return episode_url


# ── Étape 6 : Post X/Twitter ─────────────────────────────────────────────────

def post_x(text: str) -> None:
    import tweepy

    print("🐦 Post X/Twitter...")
    client = tweepy.Client(
        consumer_key=X_API_KEY,
        consumer_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_TOKEN_SECRET,
    )
    response = client.create_tweet(text=text)
    tweet_id = response.data["id"]
    print(f"   Tweet publié ✅  id={tweet_id}")


# ── Descriptions et hashtags par plateforme ──────────────────────────────────

_HASHTAGS_BASE    = "#Guadeloupe #FlashInfo #Karukera #Antilles #Caraïbes"
_HASHTAGS_METEO   = "#Météo #MétéoGuadeloupe #MétéoAntilles"
_HASHTAGS_NEWS    = "#Actualités #InfosGuadeloupe #ActuGuadeloupe"
_HASHTAGS_TIKTOK  = "#GuadeloupeTikTok #InfoTikTok"
_HASHTAGS_YOUTUBE = "#Shorts #YouTubeShorts"


def _video_label(idx: int, n_segments: int) -> str:
    if idx == 1:
        return "météo"
    return f"sujet {idx - 1}"


def _tiktok_caption(text: str, idx: int, n_segments: int, date_str: str) -> str:
    """Caption courte pour TikTok : accroche + hashtags (~300 car.)."""
    is_meteo = idx == 1
    # Première phrase du segment comme accroche
    first_sentence = text.split(".")[0].strip()
    if len(first_sentence) > 120:
        first_sentence = first_sentence[:117] + "…"
    topic_tags = _HASHTAGS_METEO if is_meteo else _HASHTAGS_NEWS
    label = "Météo Guadeloupe" if is_meteo else f"Flash Info — {date_str}"
    return (
        f"🇬🇵 {label}\n"
        f"{first_sentence}.\n\n"
        f"{_HASHTAGS_BASE} {topic_tags} {_HASHTAGS_TIKTOK}"
    )


def _youtube_description(text: str, idx: int, n_segments: int, date_str: str) -> str:
    """Description YouTube Shorts : extrait + hashtags."""
    is_meteo = idx == 1
    excerpt = text[:400].rsplit(" ", 1)[0] + "…" if len(text) > 400 else text
    topic_tags = _HASHTAGS_METEO if is_meteo else _HASHTAGS_NEWS
    label = "Météo" if is_meteo else f"Sujet {idx - 1}"
    return (
        f"Flash Info Guadeloupe — {date_str} — {label}\n\n"
        f"{excerpt}\n\n"
        f"{_HASHTAGS_BASE} {topic_tags} {_HASHTAGS_YOUTUBE}"
    )


# ── Étape 7 : Publication YouTube Shorts ─────────────────────────────────────

YOUTUBE_SCOPES       = ["https://www.googleapis.com/auth/youtube.upload"]
YOUTUBE_TAGS         = ["Guadeloupe", "flash info", "actualité", "Antilles", "Caraïbes", "Karukera", "météo", "Shorts"]
YOUTUBE_CATEGORY_ID  = "25"  # News & Politics


def _save_refresh_token(token: str) -> None:
    env_path = Path(__file__).parent / ".env"
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    for i, line in enumerate(lines):
        if line.startswith("YOUTUBE_REFRESH_TOKEN="):
            lines[i] = f"YOUTUBE_REFRESH_TOKEN={token}"
            break
    else:
        lines.append(f"YOUTUBE_REFRESH_TOKEN={token}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("   Refresh token sauvegardé dans .env")


def _youtube_credentials():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request as GoogleRequest
    from google_auth_oauthlib.flow import InstalledAppFlow

    client_config = {
        "installed": {
            "client_id": YOUTUBE_CLIENT_ID,
            "client_secret": YOUTUBE_CLIENT_SECRET,
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    if YOUTUBE_REFRESH_TOKEN:
        creds = Credentials(
            token=None,
            refresh_token=YOUTUBE_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=YOUTUBE_CLIENT_ID,
            client_secret=YOUTUBE_CLIENT_SECRET,
            scopes=YOUTUBE_SCOPES,
        )
        creds.refresh(GoogleRequest())
        return creds

    flow = InstalledAppFlow.from_client_config(client_config, YOUTUBE_SCOPES)
    creds = flow.run_local_server(port=0)
    _save_refresh_token(creds.refresh_token)
    return creds


def upload_youtube_short(video_path: Path, title: str, description: str) -> str:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    print(f"   ▶️  Upload : {video_path.name}…")
    creds = _youtube_credentials()
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)

    body = {
        "snippet": {
            "title": f"{title} #Shorts",
            "description": description,
            "tags": YOUTUBE_TAGS,
            "categoryId": YOUTUBE_CATEGORY_ID,
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _, response = request.next_chunk()

    url = f"https://youtube.com/shorts/{response['id']}"
    print(f"   ✅ {url}")
    return url


def _interleave_interstitials(
    videos: list[tuple[int, Path]],
    items: list[dict],
    output_dir: Path,
) -> list[Path]:
    """
    Intercale un interstitiel avant chaque segment de contenu (MÉTÉO et sujets).
    - videos  : [(segment_index, path), …] dans l'ordre
    - items   : articles collectés (items[0] → segment 2, items[1] → segment 3, …)
    Retourne la liste ordonnée de paths (interstitiels + segments) prête pour concat.
    """
    result: list[Path] = []
    for idx, video_path in videos:
        if idx == 0:
            # INTRO : pas d'interstitiel avant
            result.append(video_path)
            continue

        # Déterminer la catégorie du segment
        if idx == 1:
            category = "météo"
        elif idx - 2 < len(items):
            category = items[idx - 2].get("category", "general")
        else:
            category = "general"

        inter_path = output_dir / f"inter_{idx:02d}_{category.replace(' ', '_')}.mp4"
        print(f"   Interstitiel [{idx}] — {category}")
        _make_interstitial(category, inter_path)
        result.append(inter_path)
        result.append(video_path)

    return result


def concatenate_videos(video_paths: list[Path], output_path: Path) -> Path:
    """Concatène les MP4 dans l'ordre via le concat demuxer FFmpeg (re-encode)."""
    filelist = output_path.parent / "filelist.txt"
    filelist.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in video_paths),
        encoding="utf-8",
    )
    proc = subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(filelist),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        str(output_path),
    ], capture_output=True)
    filelist.unlink(missing_ok=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg concat error: {proc.stderr.decode()}")
    return output_path


def _youtube_full_description(segments: list[str], date_str: str) -> str:
    """Description YouTube pour la vidéo complète : chapitres + hashtags."""
    lines = [f"Flash Info Guadeloupe — {date_str}\n"]
    for i, seg in enumerate(segments):
        if i == 0:
            label = "Intro"
        elif i == len(segments) - 1:
            label = "Outro"
        elif i == 1:
            label = "Météo"
        else:
            label = f"Sujet {i - 1}"
        first = seg.split(".")[0].strip()
        if len(first) > 80:
            first = first[:77] + "…"
        lines.append(f"▸ {label} — {first}.")
    lines.append(f"\n{_HASHTAGS_BASE} {_HASHTAGS_NEWS} {_HASHTAGS_METEO}")
    return "\n".join(lines)


def upload_youtube_video(video_path: Path, title: str, description: str) -> str:
    """Upload une vidéo YouTube normale (pas un Short)."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    print(f"   ▶️  Upload vidéo complète : {video_path.name}…")
    creds = _youtube_credentials()
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": YOUTUBE_TAGS + ["flash info complet", "radio Guadeloupe"],
            "categoryId": YOUTUBE_CATEGORY_ID,
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _, response = request.next_chunk()

    url = f"https://youtube.com/watch?v={response['id']}"
    print(f"   ✅ {url}")
    return url


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Flash info Guadeloupe — génère automatiquement un bulletin audio à partir\n"
            "des flux RSS locaux et de la météo Open-Meteo, rédigé par Maryse (Mistral)\n"
            "et synthétisé en MP3 via Voxtral TTS, puis diffusé sur Telegram et Buzzsprout.\n\n"
            "Workflow : Collecte RSS → Météo → Rédaction Maryse → TTS par segment\n"
            "           → Assemblage FFmpeg avec stinger → Telegram → Buzzsprout → X"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--date", metavar="YYYY-MM-DD",
        help=(
            "Date de collecte des actualités et de la météo (défaut : aujourd'hui).\n"
            "Permet de rejouer un flash pour une date passée ou future.\n"
            "Exemple : --date 2026-04-18"
        ),
    )
    parser.add_argument(
        "--stinger", metavar="FICHIER",
        help=(
            f"Nom du fichier stinger à insérer entre chaque segment audio.\n"
            f"Le fichier doit se trouver dans : {STINGERS_DIR}\n"
            f"Si omis, le premier fichier du répertoire est utilisé automatiquement.\n"
            f"Si le répertoire est vide, un stinger synthétique (goutte d'eau) est généré.\n"
            f"Exemple : --stinger stinger_default.mp3"
        ),
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help=(
            "Mode test : génère le script, l'audio et envoie sur Telegram,\n"
            "mais n'envoie pas sur Buzzsprout ni X/Twitter."
        ),
    )
    parser.add_argument(
        "--no-send", action="store_true",
        help=(
            "Génère le fichier audio MP3 complet mais ne l'envoie pas\n"
            "(ni Telegram, ni Buzzsprout, ni X/Twitter).\n"
            "Utile pour écouter et valider avant diffusion."
        ),
    )
    parser.add_argument(
        "--output", type=Path, metavar="CHEMIN",
        help=(
            "Chemin complet du fichier MP3 de sortie.\n"
            "Défaut : /tmp/flash-YYYYMMDD-HHMM.mp3"
        ),
    )
    parser.add_argument(
        "--tiktok", action="store_true",
        help=(
            "Génère une vidéo MP4 TikTok (1080×1920) par segment audio.\n"
            "Waveform colorée selon la tonalité + sous-titres karaoke mot à mot\n"
            "via timestamps STT Voxtral. Vidéos dans /tmp/tiktok-YYYYMMDD-HHMM/.\n"
            "Compatible avec --no-send."
        ),
    )
    parser.add_argument(
        "--youtube", action="store_true",
        help=(
            "Publie les vidéos MP4 sur YouTube Shorts via l'API YouTube Data v3.\n"
            "Nécessite YOUTUBE_CLIENT_ID et YOUTUBE_CLIENT_SECRET dans .env.\n"
            "Le refresh token est sauvegardé automatiquement après la première autorisation.\n"
            "L'intro et l'outro sont exclus. Compatible avec --tiktok."
        ),
    )
    parser.add_argument(
        "--transcript", action="store_true",
        help=(
            "Transcrit l'audio généré via l'API Mistral STT (Voxtral).\n"
            "Permet de vérifier que le TTS a bien prononcé le texte attendu.\n"
            "La transcription est affichée et sauvegardée à côté du MP3 (.txt).\n"
            "Compatible avec --no-send et --dry-run."
        ),
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help=(
            "Mode verbeux : affiche le détail de chaque étape du pipeline.\n"
            "Étape 1 — articles collectés, retenus, écartés (avec raison).\n"
            "Étape 2 — ordre des segments, sources citées, zones géo utilisées.\n"
            "Étape 3 — chemins des fichiers temporaires et assemblage FFmpeg.\n"
            "Compatible avec --dry-run."
        ),
    )
    parser.add_argument(
        "--check-feeds", action="store_true",
        help="Vérifie la disponibilité de chaque flux RSS et affiche un rapport. Arrêt sans générer d'audio.",
    )
    args = parser.parse_args()

    if args.check_feeds:
        print("🔍 Vérification des flux RSS…\n")
        ok, ko = [], []
        for source in RSS_SOURCES:
            try:
                with urllib.request.urlopen(source.url, timeout=10) as r:
                    content = r.read()
                root = ET.fromstring(content)
                items_found = len(root.findall(".//item")) + len(root.findall(".//entry"))
                print(f"  ✅  {source.name}")
                print(f"      {source.url}")
                print(f"      {items_found} entrées trouvées\n")
                ok.append(source.name)
            except Exception as e:
                print(f"  ❌  {source.name}")
                print(f"      {source.url}")
                print(f"      Erreur : {e}\n")
                ko.append(source.name)
        print(f"Résultat : {len(ok)} OK, {len(ko)} en erreur")
        if ko:
            sys.exit(1)
        return

    now_gwada = datetime.now(GUADELOUPE_TZ)
    print(f"🕐 Heure locale Guadeloupe : {_date_fr(now_gwada.date())} — {now_gwada.strftime('%H:%M')} (UTC{now_gwada.strftime('%z')[:3]}:{now_gwada.strftime('%z')[3:]})")

    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"❌ Format de date invalide : '{args.date}'. Attendu : YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)
    else:
        target_date = now_gwada.date()

    now = datetime.combine(target_date, datetime.min.time())
    date_str = _date_fr(target_date)

    # Étape 1
    items = fetch_news(RSS_FEEDS, MAX_ITEMS, target_date)
    if not items:
        print(f"⚠️  Aucune actualité pour le {date_str} — flash météo uniquement.")

    if args.verbose:
        print("\n══════════════════════════════════════════════════════════")
        print("  VERBOSE — ÉTAPE 1 : COLLECTE RSS")
        print("══════════════════════════════════════════════════════════")
        print(f"  Date cible : {target_date}  |  Flux : {len(RSS_FEEDS)}  |  Articles retenus : {len(items)}\n")
        print("  JSON des articles collectés :")
        print(json.dumps(items, ensure_ascii=False, indent=2))
        print("══════════════════════════════════════════════════════════\n")

    weather = fetch_weather(target_date)

    # Étape 2
    sources = list(dict.fromkeys(item["source"] for item in items))  # unique, ordre conservé

    if args.verbose:
        print("\n══════════════════════════════════════════════════════════")
        print("  VERBOSE — MÉTÉO")
        print("══════════════════════════════════════════════════════════")
        print(f"  {weather}")
        print("══════════════════════════════════════════════════════════\n")

    segments_maryse = build_segments(items, date_str, weather, sources)

    def _print_segments(segs: list[str], label: str) -> None:
        print(f"\n══════════════════════════════════════════════════════════")
        print(f"  VERBOSE — {label}")
        print(f"══════════════════════════════════════════════════════════")
        for i, seg in enumerate(segs):
            tag = "INTRO" if i == 0 else "MÉTÉO" if i == 1 else ("OUTRO" if i == len(segs)-1 else f"SUJET {i-1}")
            print(f"\n  ── {tag} ──")
            print(f"  {seg.strip()}")
        print(f"\n  Texte brut (séparateurs inclus) :")
        print(f"\n{SEG_SEPARATOR}\n".join(segs))
        print("══════════════════════════════════════════════════════════\n")

    if args.verbose:
        _print_segments(segments_maryse, "SORTIE MARYSE (brut)")

    # Étape 2b — Révision stylistique
    segments = revise_style(segments_maryse)
    segments = _ensure_sources_in_outro(segments, sources)
    segments = _enforce_prononciations(segments)

    if args.verbose:
        _print_segments(segments, "SORTIE RÉVISEUR STYLISTIQUE")

    # Étape 2c — Ancrage local
    if args.verbose:
        print("\n══════════════════════════════════════════════════════════")
        print("  VERBOSE — JSON PASSÉ À L'ANCRAGE LOCAL")
        print("══════════════════════════════════════════════════════════")
        print(json.dumps(
            [{"titre": it["title"], "source": it["source"], "description": it["desc"]} for it in items],
            ensure_ascii=False, indent=2
        ))
        print("══════════════════════════════════════════════════════════\n")

    segments = anchor_local(segments, items)
    segments = _ensure_sources_in_outro(segments, sources)
    segments = _enforce_prononciations(segments)

    if args.verbose:
        _print_segments(segments, "SORTIE ANCRAGE LOCAL (final)")
    else:
        print("\n── Script final (après ancrage) ────────────────────────")
        for i, seg in enumerate(segments):
            label = "INTRO" if i == 0 else "MÉTÉO" if i == 1 else ("OUTRO" if i == len(segments)-1 else f"[{i-1}]")
            print(f"\n{label}\n{seg}")
        print("\n────────────────────────────────────────────────────────\n")

    # Étape 2d — Classification tonale (avant dry-run pour que le verbose la montre)
    tones = classify_tones(segments)

    if args.verbose:
        print("\n══════════════════════════════════════════════════════════")
        print("  VERBOSE — TONALITÉS PAR SEGMENT")
        print("══════════════════════════════════════════════════════════")
        for i, (tone, seg) in enumerate(zip(tones, segments)):
            label = "INTRO" if i == 0 else "MÉTÉO" if i == 1 else ("OUTRO" if i == len(segments)-1 else f"SUJET {i-1}")
            print(f"  {label:8s} → {tone:8s} ({TTS_VOICES.get(tone, TTS_VOICE_DEFAULT)})")
        print("══════════════════════════════════════════════════════════\n")

    # Étape 3
    stinger = resolve_stinger(args.stinger)
    output_path = args.output or OUTPUT_DIR / f"flash-{now.strftime('%Y%m%d-%H%M')}.mp3"

    if args.verbose:
        print("\n── VERBOSE : Étape 3 — Génération audio ────────────────")
        print(f"  Stinger    : {stinger}")
        print(f"  Sortie MP3 : {output_path}")
        print(f"  Segments   : {len(segments)} → {len(segments) - 1} stingers intercalés")
        print("────────────────────────────────────────────────────────\n")

    output_path, seg_paths = generate_audio(
        segments, output_path, stinger, tones=tones,
        keep_segments=args.tiktok or args.youtube,
    )

    title = f"Flash Info Guadeloupe — {date_str}"

    if args.tiktok or args.youtube:
        video_dir = OUTPUT_DIR / f"tiktok-{now.strftime('%Y%m%d-%H%M')}"
        videos = generate_tiktok(seg_paths, segments, tones, video_dir)
        print(f"\n🎬 {len(videos)} vidéos dans {video_dir}")
        for sp in seg_paths:
            sp.unlink(missing_ok=True)

        n_seg = len(segments)

        if args.tiktok:
            print("📤 Envoi des vidéos sur Telegram...")
            for idx, video_path in videos:
                if idx == 0 or idx == n_seg - 1:
                    tg_label = "INTRO" if idx == 0 else "OUTRO"
                    send_telegram_video(video_path, f"🎬 {title} — {tg_label}")
                else:
                    caption = _tiktok_caption(segments[idx], idx, n_seg, date_str)
                    send_telegram_video(video_path, caption)

        if args.youtube:
            print("▶️  Publication YouTube Shorts...")
            for idx, video_path in videos:
                if idx == 0 or idx == n_seg - 1:
                    continue  # skip intro et outro
                yt_label = "Météo" if idx == 1 else f"Sujet {idx - 1}"
                yt_title = f"Flash Info Guadeloupe — {date_str} — {yt_label}"
                yt_desc = _youtube_description(segments[idx], idx, n_seg, date_str)
                upload_youtube_short(video_path, yt_title, yt_desc)

        # Vidéo complète : générée dès que --tiktok ou --youtube est actif
        print("🎞️  Génération vidéo complète avec interstitiels…")
        full_video_path = video_dir / "flash-info-complet.mp4"
        ordered = _interleave_interstitials(videos, items, video_dir)
        concatenate_videos(ordered, full_video_path)
        print(f"   Vidéo complète : {full_video_path} ({full_video_path.stat().st_size // 1024 // 1024} Mo)")

        print("📤 Envoi vidéo complète sur Telegram…")
        send_telegram_video(full_video_path, f"🎙️ {title} — émission complète")

        if args.youtube:
            print("▶️  Upload YouTube vidéo complète…")
            yt_full_desc = _youtube_full_description(segments, date_str)
            upload_youtube_video(full_video_path, title, yt_full_desc)

    if args.transcript:
        print("📝 Transcription de l'audio généré...")
        transcript = transcribe_audio(output_path)
        print("\n── Transcription ────────────────────────────────────────")
        print(transcript)
        print("────────────────────────────────────────────────────────\n")
        transcript_path = output_path.with_suffix(".txt")
        transcript_path.write_text(transcript, encoding="utf-8")
        print(f"   Sauvegardé : {transcript_path}")

    # Étape 4 — Telegram (dry-run inclus)
    send_telegram(output_path, f"🎙️ {title}")

    if args.dry_run:
        print(f"--dry-run : audio généré et envoyé sur Telegram. Arrêt avant Buzzsprout/X.")
        return

    if args.no_send:
        print(f"--no-send : fichier disponible à {output_path}")
        return

    headlines = "\n".join(f"• {item['title']}" for item in items)
    sources_line = " | ".join(sources) if sources else "médias locaux"
    description = (
        f"Flash info du {date_str} — l'essentiel de l'actualité en Guadeloupe en moins de 2 minutes.\n\n"
        f"Au programme :\n{headlines}\n\n"
        f"Informations issues de : {sources_line}"
    )
    tags = BUZZSPROUT_TAGS

    # Étape 5 — Buzzsprout → Spotify
    episode_url = publish_buzzsprout(output_path, title, description, tags)

    print(f"\n✅ Flash info terminé : {output_path}")


if __name__ == "__main__":
    main()
