"""
Pydantic models for Publish API.
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class PlatformEnum(str, Enum):
    telegram = "telegram"
    buzzsprout = "buzzsprout"
    b2 = "b2"
    github = "github"


# --- Telegram ---


class TelegramPublishRequest(BaseModel):
    file_path: str = Field(..., description="Chemin vers le fichier a publier (relatif a PROJECT_ROOT)")
    caption: str = Field(..., description="Legende du message")
    chat_id: Optional[str] = Field(
        None,
        description="ID du chat Telegram (par defaut : TELEGRAM_CHAT_ID du .env)"
    )
    reply_to_message_id: Optional[int] = Field(
        None,
        description="ID du message auquel repondre"
    )


class TelegramPublishResponse(BaseModel):
    success: bool
    message_id: Optional[int] = None
    error: Optional[str] = None


# --- Buzzsprout ---


class BuzzsproutPublishRequest(BaseModel):
    audio_path: str = Field(..., description="Chemin vers le fichier audio MP3")
    title: str = Field(..., description="Titre de l'episode")
    description: str = Field(..., description="Description de l'episode")
    tags: Optional[str] = Field(
        "Guadeloupe, horoscope, FlashInfoKarukera",
        description="Tags separes par des virgules"
    )


class BuzzsproutPublishResponse(BaseModel):
    success: bool
    episode_id: Optional[str] = None
    episode_url: Optional[str] = None
    error: Optional[str] = None


# --- Backblaze B2 ---


class B2UploadRequest(BaseModel):
    local_path: str = Field(..., description="Chemin local du fichier")
    remote_key: str = Field(..., description="Cle distante (ex: 'horoscope/2025/05/horoscope-matin.mp3')")


class B2UploadResponse(BaseModel):
    success: bool
    url: Optional[str] = None
    error: Optional[str] = None


# --- GitHub Release ---


class GitHubUploadRequest(BaseModel):
    local_path: str = Field(..., description="Chemin local du fichier")
    tag: str = Field(..., description="Tag GitHub (ex: 'horoscope-2025-05')")
    release_name: str = Field(..., description="Nom de la release (ex: 'Horoscope Karukera - Mai 2025')")


class GitHubUploadResponse(BaseModel):
    success: bool
    download_url: Optional[str] = None
    error: Optional[str] = None


# --- Podcast RSS ---


class PodcastRSSUpdateRequest(BaseModel):
    title: str = Field(..., description="Titre de l'episode")
    description: str = Field(..., description="Description")
    audio_url: str = Field(..., description="URL de l'audio (MP3)")
    audio_size: int = Field(..., description="Taille du fichier en octets")
    duration_seconds: float = Field(..., description="Duree en secondes")
    guid: str = Field(..., description="GUID unique (ex: 'horoscope-20250505-matin')")
    pub_date: Optional[str] = Field(
        None,
        description="Date de publication (RFC 2822). Par defaut : maintenant."
    )


class PodcastRSSUpdateResponse(BaseModel):
    success: bool
    podcast_xml_updated: bool = False
    error: Optional[str] = None
