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

RSS_FEEDS = [
    "https://www.guadeloupe.franceantilles.fr/actualite/vielocale/rss.xml",
    "https://www.guadeloupe.franceantilles.fr/actualite/sports/rss.xml",
    "https://www.guadeloupe.franceantilles.fr/actualite/social/rss.xml"
    "https://rci.fm/guadeloupe/fb/articles_rss_gp",
    "https://zye-a-mangrovla.fr/?feed=rss2",
    "https://www.regionguadeloupe.fr/actualites-et-agendas/toute-lactualite/flux.rss",
    "https://la1ere.franceinfo.fr/economie/rss?r=guadeloupe"
]
MAX_ITEMS = 7          # 7 sujets → ~2m-2m30 audio
DESC_MAX_CHARS = 400   # description tronquée pour donner assez de contexte

MISTRAL_API_KEY     = os.environ["MISTRAL_API_KEY"]
TTS_MODEL           = "voxtral-mini-tts-2603"
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

def _normalize_for_tts(text: str) -> str:
    import re
    try:
        from num2words import num2words as _n2w
        def _num(n: str) -> str:
            n = n.replace("\u00a0", "").replace(" ", "").replace(",", ".")
            try:
                return _n2w(float(n) if "." in n else int(n), lang="fr")
            except Exception:
                return n
        def _ordinal(n: str) -> str:
            try:
                return _n2w(int(n), lang="fr", to="ordinal")
            except Exception:
                return n
    except ImportError:
        print("   ⚠️  num2words manquant — pip install num2words")
        _num = lambda n: n
        _ordinal = lambda n: n

    # 0. Prononciations locales guadeloupéennes
    for ecrit, oral in _PRONONCIATIONS_LOCALES.items():
        text = text.replace(ecrit, oral)

    # 1a. Apostrophes et guillemets typographiques → ASCII
    text = text.replace("\u2019", "'").replace("\u2018", "'")  # ' '
    text = text.replace("\u201c", '"').replace("\u201d", '"')  # " "
    text = text.replace("\u2013", "-").replace("\u2014", " ")  # – —

    # 1b. Emojis et symboles hors latin/ponctuation courante
    text = re.sub(r"[^\x00-\x7F\u00C0-\u024F\u1E00-\u1EFF\n]", " ", text)

    # 2. Numéros et abréviations de position : n° → numéro
    text = re.sub(r"\bn°\s*", "numéro ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bN°\s*", "Numéro ", text)

    # 3. Ordinaux français : 1er/1re → premier/première, 2e/2ème → deuxième…
    text = re.sub(r"\b1er\b", "premier", text)
    text = re.sub(r"\b1re\b", "première", text)
    text = re.sub(r"\b(\d+)(?:e|ème|eme)\b",
                  lambda m: _ordinal(m.group(1)), text)

    # 4. Monnaies : 3,5M€ / 3 millions d'euros / 15€ / 20$
    text = re.sub(r"(\d+(?:[,\.]\d+)?)\s*[Mm](?:illions?)?\s*€",
                  lambda m: f"{_num(m.group(1))} millions d'euros", text)
    text = re.sub(r"(\d+(?:[,\.]\d+)?)\s*€",
                  lambda m: f"{_num(m.group(1))} euros", text)
    text = re.sub(r"(\d+(?:[,\.]\d+)?)\s*\$",
                  lambda m: f"{_num(m.group(1))} dollars", text)

    # 5. Scores sportifs : 3-1 → trois à un
    #    (ne pas toucher aux noms composés — protégé par \b\d+\b)
    text = re.sub(r"\b(\d+)-(\d+)\b",
                  lambda m: f"{_num(m.group(1))} à {_num(m.group(2))}", text)

    # 6. Codes départementaux DOM (971–976) → lecture chiffre par chiffre
    _DOM_CODES = {
        "971": "quatre-vingt-dix-sept-un",
        "972": "quatre-vingt-dix-sept-deux",
        "973": "quatre-vingt-dix-sept-trois",
        "974": "quatre-vingt-dix-sept-quatre",
        "976": "quatre-vingt-dix-sept-six",
    }
    for code, spoken in _DOM_CODES.items():
        text = re.sub(r"\b" + code + r"\b", spoken, text)

    # 7. Heures : 07h30 → sept heures trente
    text = re.sub(
        r"\b(\d{1,2})h(\d{2})\b",
        lambda m: f"{_num(m.group(1))} heures {_num(m.group(2))}",
        text,
    )

    # 7. Nombres avec unités
    _UNIT_PATTERNS = [
        (r"(\d+(?:[,\.]\d+)?)\s*°C",   lambda m: f"{_num(m.group(1))} degrés"),
        (r"(\d+(?:[,\.]\d+)?)\s*km/h",  lambda m: f"{_num(m.group(1))} kilomètres par heure"),
        (r"(\d+(?:[,\.]\d+)?)\s*km\b",  lambda m: f"{_num(m.group(1))} kilomètres"),
        (r"(\d+(?:[,\.]\d+)?)\s*mm\b",  lambda m: f"{_num(m.group(1))} millimètres"),
        (r"(\d+(?:[,\.]\d+)?)\s*%",     lambda m: f"{_num(m.group(1))} pour cent"),
        (r"(\d+(?:[,\.]\d+)?)\s*m²",    lambda m: f"{_num(m.group(1))} mètres carrés"),
    ]
    for pattern, repl in _UNIT_PATTERNS:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    # 8. Nombres isolés restants
    text = re.sub(r"\b(\d[\d\u00a0]*(?:[,\.]\d+)?)\b", lambda m: _num(m.group(1)), text)

    # 9a. Sigles prononcés comme des mots : R.C.I / R.C.I. → RCI (avant épellation)
    for _sm in _SIGLES_MOT:
        _dotted = ".".join(_sm)          # R.C.I
        text = text.replace(_dotted + ".", _sm).replace(_dotted, _sm)

    # 9b. Sigles avec points collés : S.D.I.S / C.H.U. → S. D. I. S. / C. H. U.
    text = re.sub(
        r"\b([A-Z](?:\.[A-Z]){1,4})\.?\b",
        lambda m: m.group(1).replace(".", ". ") + ".",
        text,
    )

    # 9c. Sigles tout-majuscules sans points (2-5 lettres) → épelés, sauf _SIGLES_MOT
    text = re.sub(
        r"\b([A-Z]{2,5})\b",
        lambda m: m.group(1) if m.group(1) in _SIGLES_MOT else ". ".join(m.group(1)) + ".",
        text,
    )

    # 10. Abréviations textuelles
    for abbr, full in _ABBREVS.items():
        text = text.replace(abbr, full)

    # 10b. Titres honorifiques ambigus (regex : ne remplace que devant un nom propre)
    text = re.sub(r"\bMe\b(?=\s+[A-ZÀÂÉÈÊËÎÏÔÙÛÜ])", "Maître", text)

    # 11. Caractères spéciaux résiduels
    text = re.sub(r"[#*\[\]_~`|\\^@]", " ", text)
    text = re.sub(r"/", " sur ", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)

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


def generate_audio(segments: list[str], output_path: Path, stinger: Path, tones: list[str] | None = None) -> Path:
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

    # Nettoyage des fichiers temporaires
    for sp in seg_paths:
        sp.unlink(missing_ok=True)

    print(f"   Fichier final : {output_path} ({output_path.stat().st_size:,} bytes)")
    return output_path


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
        "--verbose", action="store_true",
        help=(
            "Mode verbeux : affiche le détail de chaque étape du pipeline.\n"
            "Étape 1 — articles collectés, retenus, écartés (avec raison).\n"
            "Étape 2 — ordre des segments, sources citées, zones géo utilisées.\n"
            "Étape 3 — chemins des fichiers temporaires et assemblage FFmpeg.\n"
            "Compatible avec --dry-run."
        ),
    )
    args = parser.parse_args()

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

    generate_audio(segments, output_path, stinger, tones=tones)

    title = f"Flash Info Guadeloupe — {date_str}"

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
