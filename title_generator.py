#!/usr/bin/env python3
"""
Génération de titres accrocheurs pour flash info et horoscope via Mistral.

Utilisé par :
  - flash-info-gwada.py   (génération inline)
  - horoscope-gwada.py    (génération inline)
  - update_podcast_titles.py (post-traitement / régénération manuelle)
"""

import json
import random
import re
import time
import urllib.request
from pathlib import Path

# ── Constantes ────────────────────────────────────────────────────────────────

MODEL    = "mistral-small-latest"
CHAT_URL = "https://api.mistral.ai/v1/chat/completions"

MONTH_NAMES = {
    "01": "janvier", "02": "février", "03": "mars",    "04": "avril",
    "05": "mai",     "06": "juin",    "07": "juillet",  "08": "août",
    "09": "septembre", "10": "octobre", "11": "novembre", "12": "décembre",
}

SIGN_EMOJIS = {
    "Bélier": "♈", "Taureau": "♉", "Gémeaux": "♊", "Cancer": "♋",
    "Lion": "♌",   "Vierge": "♍",  "Balance": "♎", "Scorpion": "♏",
    "Sagittaire": "♐", "Capricorne": "♑", "Verseau": "♒", "Poissons": "♓",
}

_SIGN_NAMES = {
    "Bélier", "Taureau", "Gémeaux", "Cancer", "Lion", "Vierge",
    "Balance", "Scorpion", "Sagittaire", "Capricorne", "Verseau", "Poissons",
    "Bèlmè", "Toré", "Jimo", "Kannkrab", "Lyon", "Vyèj",
    "Balans", "Skòpyon", "Sajitè", "Kaprikòn", "Vèso", "Pwason",
}

_SIGN_EMOJI_PATTERN = re.compile(
    r"^[A-ZÀÂÄÉÈÊËÏÎÔÙÛÜŸA-z][\w\s]* [♈♉♊♋♌♍♎♏♐♑♒♓] & "
    r"[A-ZÀÂÄÉÈÊËÏÎÔÙÛÜŸA-z][\w\s]* [♈♉♊♋♌♍♎♏♐♑♒♓] :\s*"
)

# ── LLM ───────────────────────────────────────────────────────────────────────

def _call_mistral(system: str, user: str, api_key: str,
                  temperature: float = 0.85, max_tokens: int = 120) -> str:
    payload = {
        "model": MODEL,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    }
    req = urllib.request.Request(
        CHAT_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        },
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                wait = 15 * 2 ** attempt
                print(f"   ⏳ Mistral {e.code} — retry dans {wait}s…", flush=True)
                time.sleep(wait)
            else:
                raise
        except (TimeoutError, OSError):
            if attempt < 3:
                time.sleep(15 * 2 ** attempt)
            else:
                raise
    return ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean(raw: str) -> str:
    title = re.sub(r'[\[\]\*\`\"\n\r]', "", raw)
    title = title.strip("'")
    title = re.sub(r"\s+", " ", title).strip().rstrip(".")
    title = _SIGN_EMOJI_PATTERN.sub("", title).strip()
    return title


def _date_fr(date_compact: str) -> tuple[str, str]:
    """'20260509' → ('9', 'mai')"""
    return str(int(date_compact[6:8])), MONTH_NAMES.get(date_compact[4:6], "?")


# ── Parseur horoscope ─────────────────────────────────────────────────────────

def _normalize_sign(raw: str) -> str | None:
    candidate = raw.strip().title()
    return candidate if candidate in SIGN_EMOJIS else None


def parse_sign_texts(horoscope_text: str) -> dict[str, str]:
    """Retourne {nom_signe: texte_brut} pour chaque signe trouvé."""
    signs: dict[str, list[str]] = {}
    current: str | None = None
    SKIP_PREFIXES = (
        "HOROSCOPE KARUKERA", "Signes :", "Nous sommes le", "Que la ", "Que les ",
        "Allez,", "====", "Bèl bonjou",
    )
    for line in horoscope_text.splitlines():
        stripped = line.strip()
        m = re.match(r"=== ([A-ZÀÂÄÉÈÊËÏÎÔÙÛÜŸ]+) ===", stripped)
        if m:
            current = _normalize_sign(m.group(1))
            if current and current not in signs:
                signs[current] = []
            continue
        if current and stripped and len(stripped) > 20:
            if not any(stripped.startswith(p) for p in SKIP_PREFIXES):
                signs[current].append(stripped)
    return {k: " ".join(v) for k, v in signs.items() if v}


def parse_sign_list(horoscope_text: str) -> list[str]:
    for line in horoscope_text.splitlines():
        if line.startswith("Signes :"):
            found = []
            for part in line.split(":", 1)[1].split(","):
                name = part.strip().replace("&", "").replace("*", "").strip()
                if name in SIGN_EMOJIS:
                    found.append(name)
            return found
    return []


# ── Filtrage sections horoscope du flash info ─────────────────────────────────

def _strip_horoscope_sections(text: str) -> str:
    """Retire les paragraphes horoscope (signe zodiacal en début de section)."""
    sep = "————"
    sections = text.split(sep)
    news = []
    for section in sections:
        first_word = section.strip().split(",")[0].strip()
        if first_word in _SIGN_NAMES:
            continue
        news.append(section)
    return sep.join(news)


# ── Anti-répétition ───────────────────────────────────────────────────────────

def _banned_words_from_titles(recent_titles: list[str]) -> str:
    """Extrait les mots surexploités (≥2 occurrences) et les retourne en chaîne."""
    word_counts: dict[str, int] = {}
    for t in recent_titles:
        m = re.search(r":\s*(.+?),\s*dans votre horoscope", t)
        phrase = m.group(1) if m else t
        for w in re.findall(r"[a-zàâäéèêëïîôùûüÿ]{4,}", phrase.lower()):
            word_counts[w] = word_counts.get(w, 0) + 1
    banned = sorted(w for w, c in word_counts.items() if c >= 2)
    return ", ".join(banned[:20])


def _load_recent_horoscope_titles(podcast_path: Path) -> list[str]:
    """Charge les titres horoscope existants depuis podcast.xml."""
    if not podcast_path.exists():
        return []
    import html as _html
    xml = podcast_path.read_text(encoding="utf-8")
    titles = []
    for raw_item in re.findall(r"<item>(.*?)</item>", xml, re.DOTALL):
        m_guid  = re.search(r"<guid[^>]*>(.*?)</guid>", raw_item)
        m_title = re.search(r"<title>(.*?)</title>", raw_item)
        if m_guid and m_title and "horoscope" in (m_guid.group(1) or ""):
            titles.append(_html.unescape(m_title.group(1).strip()))
    return titles


# ── Générateurs publics ───────────────────────────────────────────────────────

def generate_flash_title(
    source: "str | Path",
    edition: str,
    date_compact: str,
    api_key: str | None = None,
    recent_titles: list[str] | None = None,
) -> str | None:
    """
    Génère un titre accrocheur pour un flash info.

    Args:
        source:       texte brut ou chemin vers le fichier archive .txt
        edition:      'matin', 'midi' ou 'soir'
        date_compact: 'YYYYMMDD'
        api_key:      clé Mistral (MISTRAL_API_KEY ou MISTRAL_API_KEY_BOTIRAN)
    """
    if not api_key:
        return None

    if isinstance(source, Path):
        raw_text = source.read_text(encoding="utf-8")
    else:
        raw_text = source

    text = _strip_horoscope_sections(raw_text)
    day, month = _date_fr(date_compact)

    system = (
        "Tu es un rédacteur accrocheur pour Radio Karukera, une radio de la diaspora guadeloupéenne. "
        "Tu écris des titres de flash info courts qui donnent envie d'écouter sans tout révéler — "
        "comme un teaser. "
        "Tu réponds TOUJOURS par une seule phrase courte — jamais de liste, jamais de tirets."
    )
    user = (
        f"Voici le texte d'un flash info guadeloupéen — édition du {edition} du {day} {month} :\n\n"
        f"{text}\n\n"
        "Choisis l'info la plus marquante et génère UN SEUL titre accrocheur (max 70 caractères) "
        "qui donne envie d'écouter sans tout révéler, comme un teaser radio. "
        "Une seule phrase, pas de liste, pas de numérotation, pas de guillemets, pas de ponctuation finale."
    )

    _EDITION_PREP = {"matin": "au matin", "midi": "à midi", "soir": "au soir"}

    try:
        raw = _call_mistral(system, user, api_key, temperature=0.80, max_tokens=100)
        teaser = _clean(raw)
        if teaser:
            prep = _EDITION_PREP.get(edition, edition)
            return f"{teaser}, dans votre flash-info du {day} {month} {prep}"
        return None
    except Exception as e:
        print(f"   ⚠️  Titre flash info LLM échoué : {e}")
        return None


def generate_horoscope_title(
    source: "str | Path",
    edition: str,
    date_compact: str,
    api_key: str | None = None,
    recent_titles: list[str] | None = None,
    podcast_path: Path | None = None,
) -> str | None:
    """
    Génère un titre accrocheur pour un horoscope (corrélation entre deux signes).

    Args:
        source:        texte brut ou chemin vers le fichier archive .txt
        edition:       'matin' ou 'soir'
        date_compact:  'YYYYMMDD'
        api_key:       clé Mistral
        recent_titles: liste de titres déjà générés (anti-répétition)
        podcast_path:  si fourni, charge les titres existants depuis le RSS
    """
    if not api_key:
        return None

    if isinstance(source, Path):
        text = source.read_text(encoding="utf-8")
    else:
        text = source

    sign_texts = parse_sign_texts(text)
    sign_list  = parse_sign_list(text)

    available = [s for s in sign_list if s in sign_texts and len(sign_texts[s]) > 80]
    if len(available) < 2:
        available = [s for s in sign_texts if len(sign_texts[s]) > 80]
    if len(available) < 2:
        return None

    signe1, signe2 = random.sample(available, 2)
    excerpt1 = sign_texts[signe1][:700]
    excerpt2 = sign_texts[signe2][:700]

    # Anti-répétition : charger depuis podcast.xml si pas fourni
    all_recent = list(recent_titles or [])
    if podcast_path and not all_recent:
        all_recent = _load_recent_horoscope_titles(podcast_path)

    avoid_block = ""
    if all_recent:
        banned = _banned_words_from_titles(all_recent)
        if banned:
            avoid_block = (
                f"\n\nMots et verbes déjà surexploités — interdits dans ta réponse : {banned}."
            )

    system = (
        "Tu es un rédacteur créatif pour Radio Karukera, une radio de la diaspora guadeloupéenne au Luxembourg. "
        "Tu génères des titres d'horoscopes courts, poétiques, percutants, avec une touche créole et caraïbéenne. "
        "Tu réponds TOUJOURS par une seule phrase courte — jamais de liste, jamais de tirets, "
        "jamais de signe deux-points, jamais d'analyse."
    )
    user = (
        f"Horoscope — {signe1.upper()} :\n{excerpt1}\n\n"
        f"Horoscope — {signe2.upper()} :\n{excerpt2}\n\n"
        "Trouve l'image ou la sensation la plus forte dans chaque texte, puis forge UNE SEULE phrase poétique "
        "qui croise ces deux univers de façon surprenante.\n"
        "Exemple de bonne réponse : «Le kabrit broute l'ombre du gran pélikan»\n"
        f"{avoid_block}\n"
        "Réponds avec cette unique phrase (max 55 caractères). Pas de guillemets, pas de ponctuation finale."
    )

    try:
        raw = _call_mistral(system, user, api_key, temperature=0.88, max_tokens=80)
        correlation = _clean(raw)
        if not correlation:
            return None
    except Exception as e:
        print(f"   ⚠️  Titre horoscope LLM échoué : {e}")
        return None

    e1 = SIGN_EMOJIS.get(signe1, "✨")
    e2 = SIGN_EMOJIS.get(signe2, "✨")
    day, month = _date_fr(date_compact)
    _EDITION_PREP = {"matin": "au matin", "midi": "à midi", "soir": "au soir"}
    prep = _EDITION_PREP.get(edition, edition)

    return f"{signe1} {e1} & {signe2} {e2} : {correlation}, dans votre horoscope du {day} {month} {prep}"
