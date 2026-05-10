"""
Pydantic models for Horoscope API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date as date_type
from enum import Enum


class EditionEnum(str, Enum):
    matin = "matin"
    midi = "midi"
    soir = "soir"


# --- Request Models ---


class HoroscopeFetchRequest(BaseModel):
    date: date_type = Field(..., description="Date de l'horoscope (YYYY-MM-DD)")
    edition: EditionEnum = Field(..., description="Edition : matin, midi, soir")
    n_signs: int = Field(7, ge=1, le=12, description="Nombre de signes a inclure (défaut: 7)")
    include_signs: Optional[List[str]] = Field(
        None,
        description="Liste de signes specifiques (ex: ['Bélier', 'Taureau'])"
    )


class HoroscopeTitleRequest(BaseModel):
    signs: List[str] = Field(..., min_items=1, max_items=4, description="Liste de 1 a 4 signes (ex: ['Bélier', 'Taureau'])")
    date: date_type = Field(..., description="Date de l'horoscope")
    edition: EditionEnum = Field(..., description="Edition : matin, midi, soir")
    use_llm: bool = Field(
        True,
        description="Utiliser Mistral LLM pour generer le titre. Si False, utilise le fallback deterministe."
    )


# --- Response Models ---


class SignText(BaseModel):
    sign: str = Field(..., description="Nom du signe (ex: Bélier)")
    text: str = Field(..., description="Texte de l'horoscope pour ce signe")


class HoroscopeResponse(BaseModel):
    date: date_type = Field(..., description="Date de l'horoscope")
    edition: EditionEnum = Field(..., description="Edition")
    signs: List[SignText] = Field(..., description="Liste des signes avec leurs textes")
    weather: Optional[str] = Field(None, description="Resume meteo du jour")
    full_text: str = Field(..., description="Texte complet de l'horoscope")
    title: str = Field(..., description="Titre genere (compatible Apple Podcast)")


class HoroscopeTitleResponse(BaseModel):
    title: str = Field(..., description="Titre Apple Podcast-compatible")
    signs: List[str] = Field(..., description="Signes utilises dans le titre")
    edition: EditionEnum = Field(..., description="Edition")
    date: date_type = Field(..., description="Date")
    correlation: Optional[str] = Field(None, description="Theme de correlation extrait")
    zodiac_symbols: List[str] = Field(default_factory=list, description="Symboles zodiacaux utilises (♈, ♉, etc.)")


class SignOfDayResponse(BaseModel):
    date: date_type = Field(..., description="Date")
    sign_fr: str = Field(..., description="Nom du signe en francais")
    sign_en: str = Field(..., description="Nom du signe en anglais")
    symbol: str = Field(..., description="Symbole zodiacal (♈, ♉, etc.)")


class ZodiacSignResponse(BaseModel):
    name_fr: str
    name_en: str
    symbol: str
    start_date: str = Field(..., description="Date de debut (MM-DD)")
    end_date: str = Field(..., description="Date de fin (MM-DD)")


class AllZodiacSignsResponse(BaseModel):
    signs: List[ZodiacSignResponse] = Field(..., description="Tous les signes du zodiaque")


class WeatherResponse(BaseModel):
    date: date_type = Field(..., description="Date")
    summary: str = Field(..., description="Resume meteo (ex: 'Ensoleillé, 28-32°C')")
    temperature_min: float = Field(..., description="Temperature minimale (°C)")
    temperature_max: float = Field(..., description="Temperature maximale (°C)")


class HoroscopeArchiveResponse(BaseModel):
    date: date_type = Field(..., description="Date de l'horoscope")
    edition: EditionEnum = Field(..., description="Edition")
    filename: str = Field(..., description="Nom du fichier d'archive")
    full_text: str = Field(..., description="Contenu complet du fichier")
    signs: List[str] = Field(..., description="Liste des signes presents")
