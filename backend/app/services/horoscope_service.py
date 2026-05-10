"""
Service for managing horoscopes.
Respects strict constraints for Apple Podcast-compatible titles:
- Zodiac symbols (♈♉♊...) AFTER sign names
- NO hyphens (-)
- NO year in titles
- Format: "Signe ♈ et Signe ♉ : [correlation], dans votre horoscope de ce {edition} du {day} {month}"
"""
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import date, datetime
import logging
import random
import httpx

from ..models.horoscope import (
    HoroscopeResponse, HoroscopeTitleResponse, SignOfDayResponse,
    WeatherResponse, AllZodiacSignsResponse, HoroscopeArchiveResponse,
)
from ..config import settings
from ..utils.file_utils import read_file, find_horoscope_file, extract_sign_sections, list_horoscope_archives
from ..utils.zodiac_utils import ZODIAC_SIGNS, ZODIAC_SYMBOLS, resolve_sign, sign_for_date, get_sign_fr
from ..utils.mistral_client import MistralClient

logger = logging.getLogger(__name__)


class HoroscopeService:
    # Mapping des emojis par edition
    EDITION_EMOJIS = {
        "matin": "\u2605",  # 🌅
        "midi": "\u2600",   # 🌞
        "soir": "\u263D",   # 🌙
    }

    # Themes par signe pour le fallback
    SIGN_THEMES = {
        "Bélier": "l'audace", "Taureau": "la stabilité", "Gémeaux": "la communication",
        "Cancer": "l'intuition", "Lion": "la créativité", "Vierge": "la précision",
        "Balance": "l'harmonie", "Scorpion": "la passion", "Sagittaire": "l'aventure",
        "Capricorne": "la persévérance", "Verseau": "l'innovation", "Poissons": "les émotions",
    }

    @staticmethod
    async def fetch_horoscope(
        date: date,
        edition: str,
        n_signs: int = 7,
        include_signs: Optional[List[str]] = None,
    ) -> HoroscopeResponse:
        """
        Recupere l'horoscope depuis les archives locales.
        """
        # 1. Recupere la meteo
        try:
            weather = await HoroscopeService.fetch_weather(date)
        except Exception:
            weather = None

        # 2. Charge l'horoscope depuis les archives
        filepath = find_horoscope_file(date, edition)
        if not filepath:
            raise FileNotFoundError(f"Aucun fichier d'horoscope trouve pour {date} - {edition}")

        content = read_file(filepath)
        sign_sections = extract_sign_sections(content)

        if not sign_sections:
            raise ValueError(f"Aucune section de signe trouvee dans {filepath}")

        # 3. Selectionne les signes
        all_signs = list(sign_sections.keys())
        if include_signs:
            selected_signs = [s for s in include_signs if s in all_signs]
            if not selected_signs:
                raise ValueError(f"Aucun des signes demandes ({include_signs}) trouves")
        else:
            selected_signs = random.sample(all_signs, min(n_signs, len(all_signs)))

        # 4. Construit les SignText
        signs = []
        for sign in selected_signs:
            signs.append({"sign": sign, "text": sign_sections[sign].strip()})

        full_text = "\n\n".join([f"=== {s['sign'].upper()} ===\n{s['text']}" for s in signs])

        # 5. Genere le titre (respecte tes contraintes)
        title = await HoroscopeService.generate_title(
            signs=selected_signs,
            date=date,
            edition=edition,
            horoscope_text=full_text,
            use_llm=bool(settings.MISTRAL_API_KEY),
        )

        return HoroscopeResponse(
            date=date,
            edition=edition,
            signs=signs,
            weather=weather.summary if weather else None,
            full_text=full_text,
            title=title,
        )

    @staticmethod
    async def generate_title(
        signs: List[str],
        date: date,
        edition: str,
        horoscope_text: Optional[str] = None,
        use_llm: bool = True,
    ) -> str:
        """
        Genere un titre Apple Podcast-compatible.
        Respecte TES contraintes :
        - Symboles zodiacaux (♈, ♉, etc.) APRES les noms de signes
        - PAS de tirets (-)
        - PAS d'année
        - Format : "Signe ♈ et Signe ♉ : [correlation], dans votre horoscope de ce {edition} du {jour} {mois}"
        """
        if use_llm and horoscope_text and settings.MISTRAL_API_KEY:
            try:
                title = await HoroscopeService._generate_title_llm(
                    signs=signs,
                    date=date,
                    edition=edition,
                    horoscope_text=horoscope_text,
                )
                if title and HoroscopeService._validate_title(title, signs):
                    return title
            except Exception as e:
                logger.warning(f"LLM echoue pour le titre : {e}")

        # Fallback deterministe
        return HoroscopeService._generate_title_fallback(
            signs=signs,
            date=date,
            edition=edition,
        )

    @staticmethod
    async def _generate_title_llm(
        signs: List[str],
        date: date,
        edition: str,
        horoscope_text: str,
    ) -> str:
        """Genere un titre via Mistral LLM, aligne sur TES contraintes."""
        from ..utils.date_utils import format_horoscope_date_edition

        date_str = format_horoscope_date_edition(date, edition)
        signs_with_symbols = [f"{s} {ZODIAC_SYMBOLS.get(s, '')}" for s in signs]

        # Prompt strict respectant TES contraintes
        system_prompt = f"""Tu es un expert en astrologie et en redaction pour podcasts Apple.
**REGLES STRICTES A RESPECTER ABSOLUMENT** :
1. Les symboles zodiacaux (♈♉♊♋♌♍♎♏♐♑♒♓) **DOIVENT** etre places **APRES** les noms des signes.
   Exemple : "Bélier ♈" et **PAS** "♈ Bélier".
2. Format **OBLIGATOIRE** :
   - 1 signe : "Signe {symbole} : [thème], dans votre horoscope de {date_str}"
   - 2 signes : "Signe {symbole1} et Signe {symbole2} : [correlation], dans votre horoscope de {date_str}"
   - 3+ signes : "Signe {symbole1}, Signe {symbole2} et Signe {symbole3} : [correlation], dans votre horoscope de {date_str}"
3. La correlation **DOIT** etre une phrase courte extraite du texte d'horoscope.
4. **INTERDIT** : tirets (-), annees (2025, 2026, etc.), points d'exclamation, guillemets.
5. Utilise **UNIQUEMENT** le texte fourni pour trouver des themes de correlation entre les signes.
6. Reponds **UNIQUEMENT** avec le titre, sans explication, sans guillemets."""

        user_prompt = f"""Signes a utiliser : {', '.join(signs_with_symbols)}
Date/Edition : {date_str}
Texte de l'horoscope :
{horoscope_text[:2000]}

Genere UN titre conforme aux 6 regles ci-dessus."""

        try:
            title = await MistralClient.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.7,
                max_tokens=150,
            )
            # Nettoyage
            title = title.strip().strip('"').strip("'")
            title = " ".join(title.split())

            # Verifie et corrige les symboles si necessaire
            title = HoroscopeService._ensure_symbols_after_names(title, signs)

            return title
        except Exception:
            return ""

    @staticmethod
    def _ensure_symbols_after_names(title: str, signs: List[str]) -> str:
        """S'assure que les symboles sont apres les noms de signes."""
        for sign in signs:
            symbol = ZODIAC_SYMBOLS.get(sign, "")
            if not symbol:
                continue

            # Si le signe est dans le titre mais pas le symbole
            if sign in title and symbol not in title:
                title = title.replace(sign, f"{sign} {symbol}")
            # Si le symbole est avant le nom (ex: "♈ Bélier")
            elif symbol in title and sign in title:
                symbol_pos = title.find(symbol)
                sign_pos = title.find(sign)
                if symbol_pos != -1 and sign_pos != -1 and symbol_pos < sign_pos:
                    # Deplace le symbole apres le nom
                    title = title.replace(f"{symbol} {sign}", f"{sign} {symbol}")

        return title

    @staticmethod
    def _validate_title(title: str, signs: List[str]) -> bool:
        """Valide qu'un titre respecte toutes TES contraintes."""
        # 1. Verifie la presence des symboles
        for sign in signs:
            symbol = ZODIAC_SYMBOLS.get(sign, "")
            if symbol and symbol not in title:
                return False

        # 2. Verifie l'absence de tirets
        if "-" in title:
            return False

        # 3. Verifie l'absence d'annee
        current_year = str(date.today().year)
        years_to_check = [str(y) for y in range(current_year - 1, current_year + 2)]
        if any(year in title for year in years_to_check):
            return False

        # 4. Verifie le format de base
        if ": " not in title:
            return False
        if "dans votre horoscope de ce" not in title:
            return False

        # 5. Verifie que les symboles sont apres les noms
        for sign in signs:
            symbol = ZODIAC_SYMBOLS.get(sign, "")
            if symbol and sign in title and symbol in title:
                sign_pos = title.find(sign)
                symbol_pos = title.find(symbol, sign_pos)
                if symbol_pos == -1:
                    return False  # Symbole manquant apres le nom
                if symbol_pos < sign_pos:
                    return False  # Symbole avant le nom

        return True

    @staticmethod
    def _generate_title_fallback(
        signs: List[str],
        date: date,
        edition: str,
    ) -> str:
        """Genere un titre deterministe respectant TES contraintes."""
        from ..utils.date_utils import format_horoscope_date_edition

        date_str = format_horoscope_date_edition(date, edition)
        signs_with_symbols = [f"{s} {ZODIAC_SYMBOLS.get(s, '')}" for s in signs]

        if len(signs) == 1:
            correlation = HoroscopeService.SIGN_THEMES.get(signs[0], "votre jour astrologique")
            title = f"Signe {signs_with_symbols[0]} : {correlation}, dans votre horoscope de {date_str}"
        elif len(signs) == 2:
            correlation = "une connexion céleste"
            title = f"Signe {signs_with_symbols[0]} et Signe {signs_with_symbols[1]} : {correlation}, dans votre horoscope de {date_str}"
        else:
            correlation = "une harmonie cosmique"
            joined_signs = ", ".join([f"Signe {s}" for s in signs_with_symbols])
            title = f"{joined_signs} : {correlation}, dans votre horoscope de {date_str}"

        return title

    @staticmethod
    async def get_sign_of_day(date: date) -> SignOfDayResponse:
        """Retourne le signe zodiacal pour une date donnee."""
        sign_en = sign_for_date(date)
        sign_fr = get_sign_fr(sign_en)
        return SignOfDayResponse(
            date=date,
            sign_fr=sign_fr,
            sign_en=sign_en,
            symbol=ZODIAC_SYMBOLS.get(sign_fr, ""),
        )

    @staticmethod
    async def get_all_zodiac_signs() -> AllZodiacSignsResponse:
        """Retourne tous les signes du zodiaque."""
        signs = []
        for sign in ZODIAC_SIGNS:
            signs.append({
                "name_fr": sign["name_fr"],
                "name_en": sign["name_en"],
                "symbol": sign["symbol"],
                "start_date": sign["start"],
                "end_date": sign["end"],
            })
        return AllZodiacSignsResponse(signs=signs)

    @staticmethod
    async def fetch_weather(target_date: date) -> WeatherResponse:
        """Recupere la meteo depuis Open-Meteo API pour la Guadeloupe."""
        params = {
            "latitude": 16.17,
            "longitude": -61.58,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode",
            "timezone": "America/Guadeloupe",
            "start_date": target_date.isoformat(),
            "end_date": target_date.isoformat(),
        }
        url = "https://api.open-meteo.com/v1/forecast"

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        d = data.get("daily", {})
        if not d.get("time"):
            raise ValueError("Aucune donnee meteo disponible")

        tmax = d["temperature_2m_max"][0]
        tmin = d["temperature_2m_min"][0]
        rain = d["precipitation_sum"][0]
        wind = d["windspeed_10m_max"][0]
        code = int(d["weathercode"][0])

        # Map le code WMO a une description
        desc = HoroscopeService._get_weather_description(code)

        return WeatherResponse(
            date=target_date,
            summary=f"{desc}, {tmin:.0f}–{tmax:.0f}°C, {HoroscopeService._rain_label(rain)}, {HoroscopeService._wind_label(wind)} ({wind:.0f} km/h)",
            temperature_min=tmin,
            temperature_max=tmax,
        )

    @staticmethod
    def _get_weather_description(code: int) -> str:
        """Retourne la description pour un code meteo WMO."""
        weather_map = {
            0: "Ciel dégagé",
            1: "Principalement dégagé",
            2: "Partiellement nuageux",
            3: "Nuageux",
            45: "Brouillard",
            48: "Brouillard givrant",
            51: "Bruine légère",
            53: "Bruine modérée",
            55: "Bruine forte",
            56: "Bruine verglaçante légère",
            57: "Bruine verglaçante forte",
            61: "Pluie légère",
            63: "Pluie modérée",
            65: "Pluie forte",
            66: "Pluie verglaçante légère",
            67: "Pluie verglaçante forte",
            71: "Chute de neige légère",
            73: "Chute de neige modérée",
            75: "Chute de neige forte",
            77: "Neige en grains",
            80: "Averses de pluie légère",
            81: "Averses de pluie modérées",
            82: "Averses de pluie violentes",
            85: "Averses de neige légères",
            86: "Averses de neige violentes",
            95: "Orage",
            96: "Orage avec légère pluie",
            99: "Orage avec forte pluie",
        }
        return weather_map.get(code, "Temps variable")

    @staticmethod
    def _rain_label(mm: float) -> str:
        if mm == 0: return "pas de pluie"
        if mm < 5: return "légère pluie"
        if mm < 20: return "pluie modérée"
        return "fortes pluies"

    @staticmethod
    def _wind_label(kmh: float) -> str:
        if kmh < 20: return "vent faible"
        if kmh < 40: return "vent modéré"
        if kmh < 60: return "vent fort"
        return "vent violent"

    @staticmethod
    async def get_horoscope_archive(date: date, edition: str) -> Optional[HoroscopeArchiveResponse]:
        """Recupere un horoscope depuis les archives locales."""
        filepath = find_horoscope_file(date, edition)
        if not filepath or not filepath.exists():
            return None

        content = read_file(filepath)
        sign_sections = extract_sign_sections(content)
        signs = list(sign_sections.keys())

        return HoroscopeArchiveResponse(
            date=date,
            edition=edition,
            filename=filepath.name,
            full_text=content,
            signs=signs,
        )

    @staticmethod
    async def list_horoscope_archives() -> List[Dict]:
        """Liste toutes les archives disponibles."""
        return list_horoscope_archives()

    @staticmethod
    def _extract_correlation(title: str) -> Optional[str]:
        """Extrait la partie 'correlation' du titre."""
        if ": " not in title:
            return None

        parts = title.split(":")
        if len(parts) < 2:
            return None

        correlation_part = parts[1].split(",")[0].strip()
        return correlation_part
